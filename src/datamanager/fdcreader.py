import csv
import pandas as pd
import numpy as np
from datetime import datetime

from utils import *
from s3utils import *

pd.options.mode.chained_assignment = None


class FDCReader:
    """
    Reads files from s3 bucket and produces 
    demand curves future.
    """

    def __init__(self, fcstdate, depdate, curdate):
        """
        Demand curve is produced for remaining demand
        estimated on forecasting date and for departure
        date depdate.
        All dates are in format YYYYMMDD.
        """
        fcstdt = datetime.strptime(fcstdate, "%Y%m%d")
        depdt = datetime.strptime(depdate, "%Y%m%d")
        curdt = datetime.strptime(curdate, "%Y%m%d")

        self.dmd_factor = float((depdt - curdt).days + 1) / ((depdt - fcstdt).days + 1)

        self.fcstdate = fcstdate
        self.depdate = depdate
        self.curdate = datetime.strftime(curdt, "%Y%m%d")


    def rows(self):
        """
        Read data frames (forecast frame and yield)
        """
        fcstdateyear = self.fcstdate[:4]
        fcstdatemonth = self.fcstdate[4:6]
        fcstdateday = self.fcstdate[6:8]
 
        depdateyear = self.depdate[:4]
        depdatemonth = self.depdate[4:6]
        depdateday = self.depdate[6:8]

        # Read forecast dataframe.
        fcstcsv = "s3://ay-rmp-home/nrm/bff/{}/{}/{}/FCST_OD_{}_{}.csv.gz".format(fcstdateyear,
                                                                                 fcstdatemonth,
                                                                                 fcstdateday,
                                                                                 self.fcstdate,
                                                                                 self.depdate)
        fcstdf = pd.read_csv(fcstcsv, low_memory=False)

        # Replace NA values (bad for grouping).
        fcstdf = fcstdf.replace(np.nan, "")

        # Set remaining demand to zero for flows with negative marginal profits.
        fcstdf.loc[fcstdf["SMPWA"] < 0.0, "SRD"] = 0
        fcstdf.loc[fcstdf["AMPWA"] < 0.0, "ARD"] = 0

        fcstdf["ARD"] = fcstdf["ARD"].astype(float)
        fcstdf["SRD"] = fcstdf["SRD"].astype(float)

        fcstdf["ARD"] = self.dmd_factor * fcstdf["ARD"]
        fcstdf["SRD"] = self.dmd_factor * fcstdf["SRD"]

        fcstdf = fcstdf[["GEO_OD_TS_KEY", "BASE_OD_ORGN", "BASE_OD_DSTN", "BASE_OD_VIA",
                         "BASE_OD_ORGN_COUNTRY", "BASE_OD_ORGN_REGION",
                         "BASE_OD_DSTN_COUNTRY", "BASE_OD_DSTN_REGION",
                         "BASE_OPR_CC", "BASE_OPR_FLTNUM",
                         "BASE_MKT_CC", "BASE_MKT_FLTNUM",
                         "BASE_OD_DEP_DATE", "BASE_SEG_DEP_DATE", "BASE_SEG_ARR_DATE",
                         "GEO_ORGN", "GEO_DSTN",
                         "PREV_VIA", "PREV_OPR_CC", "PREV_OPR_FLTNUM",
                         "PREV_MKT_CC", "PREV_MKT_FLTNUM",
                         "PREV_SEG_DEP_DATE", "PREV_SEG_ARR_DATE",
                         "NEXT_VIA", "NEXT_OPR_CC", "NEXT_OPR_FLTNUM",
                         "NEXT_MKT_CC", "NEXT_MKT_FLTNUM",
                         "NEXT_SEG_DEP_DATE", "NEXT_SEG_ARR_DATE",
                         "POS", "BC", "FF", "TP",
                         "SMPWA", "AMPWA",
                         "SRD", "ARD", "SFD", "AFD", "SRC_DATE"]]

        for _, r in fcstdf.iterrows():
            yield r


if __name__ == "__main__":
    fdc = FDCReader("20240506", "20241028", "20240506")
    with open("out.csv", "w") as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(["opr_od_ts_key", "geo_od_ts_key",
                            "base_od_dept_airport", "base_od_arr_airport", "base_od_dept_date",
                            "geo_od_dept_airport", "geo_od_arr_airport",
                            "pos", "fare_family", "booking_class",
                            "system_marginal_profit", "adjusted_marginal_profit",
                            "system_remaining_demand", "adjusted_remaining_demand",
                            "source_file_date"])
        for r in fdc.rows():
            geo_od_ts_key = r["GEO_OD_TS_KEY"]
            base_od_orgn = r["BASE_OD_ORGN"]
            base_od_dstn = r["BASE_OD_DSTN"]
            base_od_via = r["BASE_OD_VIA"]
            if base_od_orgn == "FUE" and base_od_dstn == "HEL":
                print(geo_od_ts_key)
            csvwriter.writerow(r)



