import csv
import math
import yaml
import numpy as np
import pandas as pd
from threading import Lock
from time import sleep
import snowflake.connector

from defs import *
from db_connector import *
from yield_lookup import *

mutex = Lock()

class NRVReader:
    """
    Reads files from s3 buckets:
    dual values, exponential demand, constrained forecast and yield.
    """

    def __init__(self, srcdate, depdate):
        self.srcdate = srcdate
        self.depdate = depdate
        self.yl = YieldLookup(self.srcdate)

    def read_dfs(self):
        # Read product dual values.
        fname = "s3://ay-rmp-home/nrm/cf/{}/{}/{}/cf_prdt_sens_{}_{}.csv.gz".format(self.srcdate[:4],
                                                                                    self.srcdate[4:6],
                                                                                    self.srcdate[6:8],
                                                                                    self.srcdate,
                                                                                    self.depdate)
        self.df = pd.read_csv(fname, low_memory=False)
        self.df = self.df.replace(np.nan, '')
        clsdf = pd.read_csv("s3://ay-rmp-home/static/clsorder.csv")
        self.df = self.df.merge(clsdf, left_on=['BC'], right_on=['CLS'], how='left')
 
        # Read exponential demand. 
        fname = "s3://ay-rmp-home/nrm/expdmd/{}/{}/{}/expdmd_{}_{}.csv.gz".format(self.srcdate[:4],
                                                                                  self.srcdate[4:6],
                                                                                  self.srcdate[6:8],
                                                                                  self.srcdate,
                                                                                  self.depdate)
        edf = pd.read_csv(fname, low_memory=False)

        # Merge exponential demand to product dataframe.
        self.df = self.df.merge(edf, left_on=["GEO_OD_TS_KEY", "POS", "FF", "TP"],
                                     right_on=["GEO_OD_TS_KEY", "POS", "FF", "TP"],
                                     how="left")

        # Read constrained forecast.
        fname = "s3://ay-rmp-home/nrm/cf/{}/{}/{}/cf_{}_{}.csv.gz".format(self.srcdate[:4],
                                                                         self.srcdate[4:6],
                                                                         self.srcdate[6:8],
                                                                         self.srcdate,
                                                                         self.depdate)
        cfdf = pd.read_csv(fname, low_memory=False)

        # Merge constrained demand.
        self.df = self.df.merge(cfdf, left_on=["GEO_OD_TS_KEY",
                                               "GEO_ORGN",
                                               "GEO_DSTN",
                                               "BASE_OD_ORGN_COUNTRY",
                                               "BASE_OD_DSTN_COUNTRY",
                                               "BASE_OD_DEPT_DATE",
                                               "POS",
                                               "FF",
                                               "TP",
                                               "BC"],
                                      right_on=["GEO_OD_TS_KEY",
                                                "GEO_ORGN",
                                                "GEO_DSTN",
                                                "BASE_OD_ORGN_COUNTRY",
                                                "BASE_OD_DSTN_COUNTRY",
                                                "BASE_OD_DEPT_DATE",
                                                "POS",
                                                "FF",
                                                "TP",
                                                "BC"],
                                      how="left")

        # Merge generic fare family.
        NUM_TRIES = 5
        for i in range(NUM_TRIES):
            try:
                mutex.acquire()
                with open("/home/ay49514/rmbits/config.yaml") as f:
                    d = yaml.load(f)
                    ctx = snowflake.connector.connect(
                        user=d["SNOWFLAKE_DATABASE"]["USER"],
                        private_key_file=d["SNOWFLAKE_DATABASE"]["PRIVATE_KEY_FILE"],
                        private_key_file_pwd=d["SNOWFLAKE_DATABASE"]["PRIVATE_KEY_FILE_PWD"],
                        account=d["SNOWFLAKE_DATABASE"]["ACCOUNT"]
                    )
                    cur = ctx.cursor()
                    cur.execute("SELECT * FROM RMP_SANDBOX.REPORT.D_FF")
                    data = []
                    for row in cur.fetchall():
                        data.append([row[0], row[1], row[2], row[3]])
                    ffdf = pd.DataFrame(data, columns=["FARE_FAMILY", "GENERIC_FARE_FAMILY", "CABIN", "FF_SORT"])

                mutex.release()
                break
            except Exception as e:
                print("e = ", e)
                sleep(1)

        self.df = self.df.merge(ffdf, left_on=["FF"], right_on=["FARE_FAMILY"], how="left")
        self.df = self.df.sort_values(by=["GEO_OD_TS_KEY", "POS", "FF", "TP", "ORDER"])

    def rows_exp(self):
        clss = []
        yields = []
        mus = []

        prev_r = None
        prev_geo_od_ts_key = None
        prev_pos = None
        prev_ff = None
        prev_tp = None
        for _, r in self.df.iterrows():
            geo_od_ts_key = r["GEO_OD_TS_KEY"]
            pos = r["POS"]
            ff = r["FF"]
            tp = r["TP"]
            if r["BC"] == "G" or r["BC"] == "A":
                continue
            if ff == np.nan or ff == "nan" or ff == "":
                continue
            if prev_geo_od_ts_key == geo_od_ts_key and\
               prev_pos == pos and\
               prev_ff == ff and\
               prev_tp == tp:
                clss.append(r["BC"])
                yields.append(self.yl.lookup(r["BASE_OD_ORGN_x"], r["BASE_OD_DSTN_x"], r["POS"], r["BC"]))

                mus.append(r["DUAL"])
            else:
                # New fare family.
                n = len(clss)
                assert n == len(yields)
                assert n == len(mus)

                if n > 1 and prev_ff != np.nan and prev_ff != '': # Ignore isolated classes.
                    v = prev_r["AV"]
                    w = prev_r["AW"] # we use only adjusted, because duals are only adjusted.

                    if abs(v) > EPS and abs(w) > EPS: # skip zero demand.
                        m = len(clss)
                        assert m == len(yields)
                        assert m == len(mus)

                        if -EPS <= mus[0] < 0.0:
                            mus[0] = 0.0
                        nrv = mus[0] * np.exp(-yields[0] / w)
                        prev_yield = yields[0]

                        for i in range(1, len(clss)):
                            nrv += mus[i] * (np.exp(-yields[i] / w) - np.exp(-prev_yield / w))
                            prev_yield = yields[i]
                        if nrv < 0:
                            # FIXME: This could happen. Investigate it later.
                            nrv = 0.0
                        assert nrv >= 0.0, "nrv = {}".format(nrv)

                        yield [prev_r["GEO_OD_TS_KEY"],
                               prev_r["GEO_ORGN"], prev_r["GEO_DSTN"],
                               prev_r["BASE_OD_ORGN_x"], prev_r["BASE_OD_ORGN_COUNTRY"],
                               prev_r["BASE_OD_DSTN_x"], prev_r["BASE_OD_DSTN_COUNTRY"],
                               prev_r["BASE_OD_DEPT_DATE"],
                               prev_r["POS"], prev_r["FF"], prev_r["GENERIC_FARE_FAMILY"], prev_r["TP"],
                               nrv]

                # Start over.
                clss = [r["BC"]]
                yields = [self.yl.lookup(r["BASE_OD_ORGN_x"], r["BASE_OD_DSTN_x"], r["POS"], r["BC"])]
                mus = [r["DUAL"]]
            prev_r = r
            prev_geo_od_ts_key = geo_od_ts_key
            prev_pos = pos
            prev_ff = ff
            prev_tp = tp

    def rows_pwl(self):
        clss = []
        mus = []
        ds = []

        prev_r = None
        prev_geo_od_ts_key = None
        prev_pos = None
        prev_ff = None
        prev_tp = None
        for _, r in self.df.iterrows():
            geo_od_ts_key = r["GEO_OD_TS_KEY"]
            pos = r["POS"]
            ff = r["FF"]
            tp = r["TP"]
            if r["BC"] == "G" or r["BC"] == "A":
                continue
            if ff == np.nan or ff == "nan" or ff == "":
                continue
            if prev_geo_od_ts_key == geo_od_ts_key and\
               prev_pos == pos and\
               prev_ff == ff and\
               prev_tp == tp:
                clss.append(r["BC"])
                mus.append(r["DUAL"])
                ds.append(r["D"])
            else:
                # New fare family.
                n = len(clss)
                assert n == len(ds), "clss = {}, ds = {}".format(clss, ds)

                for i in range(n - 1, -1, -1):
                    if math.isnan(ds[i]):
                        del clss[i]
                        del mus[i]
                        del ds[i]

                n = len(clss)
                assert n == len(mus) == len(ds)

                if n > 0:
                    # Calculate NRV values.
                    if abs(ds[n-1]) < EPS:
                        nrv = 0.0
                    else:
                        nrv = sum([mus[i] * ds[i] / sum(ds) for i in range(n)])

                    yield [prev_r["GEO_OD_TS_KEY"],
                           prev_r["GEO_ORGN"], prev_r["GEO_DSTN"],
                           prev_r["BASE_OD_ORGN_x"], prev_r["BASE_OD_ORGN_COUNTRY"],
                           prev_r["BASE_OD_DSTN_x"], prev_r["BASE_OD_DSTN_COUNTRY"],
                           prev_r["BASE_OD_DEPT_DATE"],
                           prev_r["POS"], prev_r["FF"], prev_r["GENERIC_FARE_FAMILY"], prev_r["TP"],
                           nrv]

                # Start over.
                clss = [r["BC"]]
                mus = [r["DUAL"]]
                ds = [r["D"]]
            prev_r = r
            prev_geo_od_ts_key = geo_od_ts_key
            prev_pos = pos
            prev_ff = ff
            prev_tp = tp

if __name__ == "__main__":
    nrv = NRVReader("20240311", "20240615")
    nrv.read_dfs()

    num = 0
    for r in nrv.rows_pwl():
        geo_od_ts_key, _, _, _, _, _, _, _, pos, ff, gff, tp, v = r
        if geo_od_ts_key == "JFKHEL2024061520240616AY0016" and pos == "DE" and ff == "UEYL" and tp == "L":
            print("pwl", num, geo_od_ts_key, pos, ff, tp, v)
            print("")
        num += 1

    num = 0
    for r in nrv.rows_exp():
        geo_od_ts_key, _, _, _, _, _, _, _, pos, ff, gff, tp, v = r
        if geo_od_ts_key == "JFKHEL2024061520240616AY0016" and pos == "DE" and ff == "UEYL" and tp == "L":
            print("exp", num, geo_od_ts_key, pos, ff, tp, v)
            print("")
        num += 1



