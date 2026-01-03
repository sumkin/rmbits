import sys
import yaml
import gzip
import pickle
import pandas as pd
import numpy as np
from datetime import datetime as dt
from datetime import timedelta

from cls import *
from s3utils import *
from dfutils import *
import snowflake.connector


class LPReaderFDC:
    """
    Read demand curve files from s3 bucket and produce LP vector and matrices.
    """

    def __init__(self, fcstdate, decompdate, mode="remaining"):
        """
        fcstdate YYYYMMDD string (from date for demand curve)
        decompdate  YYYYMMDD string (decomposition date)
        """
        self.fcstdate = fcstdate
        self.decompdate = decompdate

        self.prev_depdate = dt.strftime(dt.strptime(self.decompdate, "%Y%m%d") - timedelta(days=1), "%Y%m%d")
        self.depdate = self.decompdate
        self.next_depdate = dt.strftime(dt.strptime(self.decompdate, "%Y%m%d") + timedelta(days=1), "%Y%m%d")

        self.mode = mode  # remaining or final.

        fcstyear, fcstmonth, fcstday = self.fcstdate[:4], self.fcstdate[4:6], self.fcstdate[6:8]

        # Inventory data frame.
        invcsv = "s3://ay-emr-job/nrm/bif/{}/{}/INV_{}.csv.gz".format(fcstyear, fcstmonth, self.fcstdate)
        self.invdf = pd.read_csv(invcsv, low_memory=False).fillna("")
        self.invdf = self.invdf.loc[self.invdf["DECOMPOSITION_DT"] == int(self.decompdate)]
        self.invdf = self.invdf.loc[(self.invdf["CABIN"] == "J") | (self.invdf["CABIN"] == "Y")]
        self.invdf = self.invdf.loc[(self.invdf["CAPO"] < 900)]
        self.invdf = optimize_bif(self.invdf)

    def read_dfs(self):
        """
        Read demand curve data frames.
        """
        fcstyear, fcstmonth, fcstday  = self.fcstdate[:4], self.fcstdate[4:6], self.fcstdate[6:8]

        # Demand curve dataframe.
        prev_dccsv = "s3://ay-emr-job/nrm/fdc/{}/{}/{}/fdc_{}_{}.csv.gz".format(fcstyear,
                                                                                fcstmonth,
                                                                                fcstday,
                                                                                self.fcstdate,
                                                                                self.prev_depdate)
        dccsv = "s3://ay-emr-job/nrm/fdc/{}/{}/{}/fdc_{}_{}.csv.gz".format(fcstyear,
                                                                           fcstmonth,
                                                                           fcstday,
                                                                           self.fcstdate,
                                                                           self.depdate)
        next_dccsv = "s3://ay-emr-job/nrm/fdc/{}/{}/{}/fdc_{}_{}.csv.gz".format(fcstyear,
                                                                                fcstmonth,
                                                                                fcstday,
                                                                                self.fcstdate,
                                                                                self.next_depdate)
        self.prev_dccsv = prev_dccsv
        self.dccsv = dccsv
        self.next_dccsv = next_dccsv

        if self.prev_depdate >= self.fcstdate:
            self.prev_dcdf = pd.read_csv(prev_dccsv, low_memory=False).fillna("")
        self.dcdf = pd.read_csv(dccsv, low_memory=False).fillna("")
        self.next_dcdf = pd.read_csv(next_dccsv, low_memory=False).fillna("")

        if self.prev_depdate >= self.fcstdate:
            self.dcdf = pd.concat([self.dcdf, self.prev_dcdf, self.next_dcdf], ignore_index=True)
        else:
            self.dcdf = pd.concat([self.dcdf, self.next_dcdf], ignore_index=True)

        # Read bookings from snowflake.
        bofdf = None
        with open("/home/ay49514/rmbits/config.yaml") as f:
            d = yaml.load(f)
            ctx = snowflake.connector.connect(
                account=d["SNOWFLAKE_DATABASE"]["ACCOUNT"],
                user=d["SNOWFLAKE_DATABASE"]["USER"],
                password=d["SNOWFLAKE_DATABASE"]["PASSWORD"],
                schema=d["SNOWFLAKE_DATABASE"]["SCHEMA"],
                warehouse=d["SNOWFLAKE_DATABASE"]["WAREHOUSE"],
                role=d["SNOWFLAKE_DATABASE"]["ROLE"]
            )
            cur = ctx.cursor()
            cur.execute("SELECT GEO_OD_TS_KEY, POC, BOOKING_CLASS, SUM(OD_PAX_COUNT), AVG(YIELD)\
                         FROM RMP_SANDBOX.REPORT.NRM_BKG_CURVE\
                         WHERE BASE_OD_DEPT_DATE = '{}-{}-{}'\
                         GROUP BY GEO_OD_TS_KEY, BASE_OD_DEPT_DATE, POC, BOOKING_CLASS".format(
                             self.depdate[:4],
                             self.depdate[4:6],
                             self.depdate[6:8]
                         ))
            data = []
            for row in cur.fetchall():
                data.append([row[0], row[1], row[2], row[3], row[4]])
            bofdf = pd.DataFrame(data, columns=["GEO_OD_TS_KEY", "ISO_COUNTRY", "SELL_CLS", "REFERENCE", "YIELD"])
        assert bofdf is not None
 
        # Merge class order.
        clsdf = pd.read_csv("s3://ay-emr-job/static/clsorder.csv")
        self.dcdf = self.dcdf.merge(clsdf, left_on=["BC"], right_on=["CLS"], how="left")

        # Merge bookings dataframe.
        self.dcdf = self.dcdf.merge(bofdf, left_on=["GEO_OD_TS_KEY", "POS", "BC"],
                                           right_on=["GEO_OD_TS_KEY", "ISO_COUNTRY", "SELL_CLS"], how="left")
        self.dcdf = self.dcdf.fillna(value={"REFERENCE": 0, "YIELD": 0})

        # Create keys. 
        self.dcdf = self.dcdf.sort_values(by=["GEO_OD_TS_KEY", "POS", "FF", "TP", "ORDER"])
        self.dcdf = self.dcdf.assign(flowsh=lambda x: x.GEO_OD_TS_KEY.astype(str) + "-" +
                                                      x.POS.astype(str) + "-" +
                                                      x.FF.astype(str) + "-" +
                                                      x.TP.astype(str) + "-" +
                                                      x.BC.astype(str))
        self.dcdf = self.dcdf.assign(initrow=lambda x: x.GEO_OD_TS_KEY.astype(str) + "," +
                                                       x.BASE_OD_ORGN.astype(str) + "," +
                                                       x.BASE_OD_DSTN.astype(str) + "," +
                                                       x.BASE_OD_VIA.astype(str) + "," +
                                                       x.BASE_OD_ORGN_COUNTRY.astype(str) + "," +
                                                       x.BASE_OD_ORGN_REGION.astype(str) + "," +
                                                       x.BASE_OD_DSTN_COUNTRY.astype(str) + "," +
                                                       x.BASE_OD_DSTN_REGION.astype(str) + "," +
                                                       x.BASE_OPR_CC.astype(str) + "," +
                                                       x.BASE_OPR_FLTNUM.astype(str) + "," +
                                                       x.BASE_MKT_CC.astype(str) + "," +
                                                       x.BASE_MKT_FLTNUM.astype(str) + "," +
                                                       x.BASE_OD_DEP_DATE.astype(str) + "," +
                                                       x.BASE_SEG_DEP_DATE.astype(str) + "," +
                                                       x.BASE_SEG_ARR_DATE.astype(str) + "," +
                                                       x.GEO_ORGN.astype(str) + "," +
                                                       x.GEO_DSTN.astype(str) + "," +
                                                       x.PREV_VIA.astype(str) + "," +
                                                       x.PREV_OPR_CC.astype(str) + "," +
                                                       x.PREV_OPR_FLTNUM.astype(str) + "," +
                                                       x.PREV_MKT_CC.astype(str) + "," +
                                                       x.PREV_MKT_FLTNUM.astype(str) + "," +
                                                       x.PREV_SEG_DEP_DATE.astype(str) + "," +
                                                       x.PREV_SEG_ARR_DATE.astype(str) + "," +
                                                       x.NEXT_VIA.astype(str) + "," +
                                                       x.NEXT_OPR_CC.astype(str) + "," +
                                                       x.NEXT_OPR_FLTNUM.astype(str) + "," +
                                                       x.NEXT_MKT_CC.astype(str) + "," +
                                                       x.NEXT_MKT_FLTNUM.astype(str) + "," +
                                                       x.NEXT_SEG_DEP_DATE.astype(str) + "," +
                                                       x.NEXT_SEG_ARR_DATE.astype(str) + "," +
                                                       x.POS.astype(str) + "," +
                                                       x.BC.astype(str) + "," +
                                                       x.FF.astype(str) + "," +
                                                       x.TP.astype(str))
        self.dcdf["flowsh"] = self.dcdf["flowsh"].astype("category")
        self.dcdf["initrow"] = self.dcdf["initrow"].astype("category")

    def create_resources_map(self, cap_infl=None):
        """
        Creates map fltnum + cabin + depdate -> index
        for fast retrieval of resource index.
        """
        num = 0
        self.rownumd = {}
        self.rownum2cmpt = []
        self.fltnumdepdt2decompdt = {}
        self.cap = []
        self.fcap = []  # Full capacity.
        for index, row in self.invdf.iterrows():
            if int(row["DECOMPOSITION_DT"]) != int(self.decompdate):
                continue
            if self.mode == "remaining":
                actcap = max(0, int(row["CAPO"]) - int(row["ESB"]))
            else:
                actcap = max(0, int(row["CAPO"]))
            if cap_infl is not None:
                actcap = cap_infl(row, actcap)
            fltnum, cabin = row["FLTNUM"], row["CABIN"]
            self.fltnumdepdt2decompdt[str(fltnum) + str(row["DEPDT"])] = str(row["DECOMPOSITION_DT"])
            if str(row["DECOMPOSITION_DT"]) == self.decompdate and actcap > 0.0:
                k = str(int(fltnum)) + cabin + str(row["DEPDT"])
                self.cap.append(actcap)
                self.fcap.append(int(row["CAPO"]))
                self.rownumd[k] = num
                lbl = row["CC"] + row["ORGN"] + row["DSTN"] + str(fltnum).zfill(4) + cabin + str(row["DEPDT"])
                self.rownum2cmpt.append(lbl)
                num += 1
        self.cap = np.array(self.cap)
        self.fcap = np.array(self.fcap)
        return num

    def read(self, dmd_infl=None, cap_infl=None, yld_infl=None):
        """
        Calculates all parameters for LP.
        """
        self.read_dfs()
        self.create_resources_map(cap_infl)
 
        self.Ai, self.Aj, self.Adata = [], [], []
        self.f = []  # Fares. Coefficients of objective.
        self.d = []  # Demand. Constraints on variables.
        self.b = []  # Bookings. Required for ROM.
        self.y = []  # Yields. Required for ROM.

        self.v_idx2initrow = []
        self.v_idx2flowsh = []  # Store map variable index -> geo flow.
        self.v_flowsh2idx = {}  # Store map geo flow -> variable index.

        n, num = 0, 0
        totnum = self.dcdf.shape[0]
        for _, row in self.dcdf.iterrows():
            if n % 10000 == 0:
                print("{}/{} ({}%)".format(n, totnum, int((100 * n)/totnum)))

            # Get decomposition dates.
            skip = False
            base_seg_dep_dates = str(row["BASE_SEG_DEP_DATE"]).split("-")
            oprfltnums = str(row["BASE_OPR_FLTNUM"]).split("-")
            cmpt = get_cmpt(row["BC"])
            assert len(base_seg_dep_dates) == len(oprfltnums)

            for i in range(len(base_seg_dep_dates)):
                k = str(oprfltnums[i]) + str(base_seg_dep_dates[i])
                if k not in self.fltnumdepdt2decompdt.keys():
                    skip = True
                    break
                else:
                    if self.fltnumdepdt2decompdt[k] != self.decompdate:
                        skip = True
                        break
                k = str(oprfltnums[i]) + cmpt + str(base_seg_dep_dates[i])
                if k not in self.rownumd.keys():
                    skip = True
                    break

            if self.mode == "remainng":
                d = row["ARD"]
            else:
                d = row["AFD"]

            b = row["REFERENCE"] / 2  # divide by 2, because bookings do not have TP and it is sum.
            y = row["YIELD"]          # this is average yield.

            if is_special_cls(row["BC"]):
                d = max(b, d)

            if dmd_infl is not None:
                d = dmd_infl(row, d)  

            d = max(0.0, d)

            flowsh = row["flowsh"]
            initrow = row["initrow"]

            if not skip:
                # Check that all flights are present.
                for i, fltnum in enumerate(oprfltnums):
                    k = str(int(fltnum)) + cmpt + str(base_seg_dep_dates[i])
                    self.Ai.append(self.rownumd[k])
                    self.Aj.append(num)
                    self.Adata.append(1)

                if is_special_cls(row["BC"]):
                    self.f.append(y)
                else:
                    if yld_infl is not None:
                        self.f.append(yld_infl(row, row["AMPWA"]))
                    else:
                        self.f.append(row["AMPWA"])

                self.d.append(d)
                self.b.append(b)
                self.y.append(y)

                self.v_idx2initrow.append(initrow)
                self.v_idx2flowsh.append(flowsh)
                self.v_flowsh2idx[flowsh] = num

            n += 1
            if not skip:
                num += 1

        assert max(self.Aj) < len(self.d)
        assert max(self.Aj) < len(self.b)
        assert max(self.Aj) < len(self.y)
        assert len(self.f) == len(self.d)

        self.f = np.array(self.f)
        self.d = np.array(self.d)
        self.b = np.array(self.b)
        self.y = np.array(self.y)

    def get_A(self):
        return self.Ai, self.Aj, self.Adata

    def get_f(self, idx=None):
        if idx == None:
            return self.f
        else:
            return self.f[idx]

    def get_b(self):
        return self.b

    def get_y(self):
        return self.y

    def get_d(self):
        return self.d

    def get_cap(self):
        return self.cap

    def get_fcap(self):
        return self.fcap

    def get_rownumd(self):
        return self.rownumd     

    def get_fcstcsv(self):
        return self.fcstcsv

    def get_idx(self, flowsh):
        return self.v_flowsh2idx[flowsh]

    def get_initrow(self, idx=None):
        if idx is None:
            return self.v_idx2initrow
        else:
            return self.v_idx2initrow[idx]

    def get_prdt_names(self):
        return self.v_idx2flowsh

    def get_rsrc_names(self):
        return self.rownum2cmpt

    def get_arrdt(self, cc, orgn, dstn, fltnum, depdt):
        return self.invdf[(self.invdf["CC"] == cc) &
                          (self.invdf["ORGN"] == orgn) &
                          (self.invdf["DSTN"] == dstn) &
                          (self.invdf["FLTNUM"] == fltnum) &
                          (self.invdf["DEPDT"] == int(depdt))]["ARRDT"].iloc[0]

    def get_dcdf_row(self,i):
        r = self.dcdf.iloc[i,:] 
        return [r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7],
                r[8], r[9], r[10], r[11], r[12], r[13], r[14], r[14]]

    def get_pkl_object(self):
        res = {}
        res["Ai"], res["Aj"], res["Adata"] = self.get_A()
        res["cap"] = self.get_cap()
        res["d"] = self.get_d()
        res["f"] = self.get_f()
        res["b"] = self.get_b()
        res["y"] = self.get_y()
        res["prdt_names"] = self.get_prdt_names()
        res["rsrc_names"] = self.get_rsrc_names()
        res["initrow"] = self.get_initrow()
        res["fcap"] = self.get_fcap()
        res["v_flowsh2idx"] = self.v_flowsh2idx
        res["v_idx2flowsh"] = self.v_idx2flowsh
        res["rownumd"] = self.rownumd
        return res

if __name__ == "__main__":
    lpreaderfdc = LPReaderFDC("20251006", "20260316")
    print("LPReaderFDC initialized")
    lpreaderfdc.read()
    lpreaderfdc.get_pkl_object()



