import csv
import sys
import traceback
import subprocess
from joblib import Parallel, delayed
import multiprocessing
from datetime import datetime, timedelta
from random import shuffle

from defs import *
from s3utils import *
from fdcreader import *


def process(fcstdt, curdt, depdt):
    csv2check = "ay-rmp-home/nrm/fdc/{}/{}/{}/fdc_{}_{}.csv.gz".format(curdt[:4],
                                                                      curdt[4:6],
                                                                      curdt[6:8],
                                                                      curdt,
                                                                      depdt)
    if s3fileexists(csv2check):
        print(csv2check, " exists")
        return 0

    bff2check = "ay-rmp-home/nrm/bff/{}/{}/{}/FCST_OD_{}_{}.csv.gz".format(fcstdt[:4],
                                                                          fcstdt[4:6],
                                                                          fcstdt[6:8],
                                                                          fcstdt,
                                                                          depdt)
    if not s3fileexists(bff2check):
        print(bff2check, " exists")
        return 0

    print("Processing fdc ", curdt, " ", depdt, "...")
    fdc = FDCReader(fcstdt, depdt, curdt)
    fname_out = "/mnt/data/tmp/fdc_{}_{}.csv".format(curdt, depdt)
    with open(fname_out, "w") as fout:
        csvwriter = csv.writer(fout)

        csvwriter.writerow(["GEO_OD_TS_KEY", "BASE_OD_ORGN", "BASE_OD_DSTN", "BASE_OD_VIA",
                            "BASE_OD_ORGN_COUNTRY", "BASE_OD_ORGN_REGION",
                            "BASE_OD_DSTN_COUNTRY", "BASE_OD_DSTN_REGION",
                            "BASE_OPR_CC", "BASE_OPR_FLTNUM",
                            "BASE_MKT_CC", "BASE_MKT_FLTNUM",
                            "BASE_OD_DEP_DATE", "BASE_SEG_DEP_DATE", "BASE_SEG_ARR_DATE",
                            "GEO_ORGN", "GEO_DSTN",
                            "PREV_VIA", "PREV_OPR_CC", "PREV_OPR_FLTNUM", "PREV_MKT_CC", "PREV_MKT_FLTNUM",
                            "PREV_SEG_DEP_DATE", "PREV_SEG_ARR_DATE",
                            "NEXT_VIA", "NEXT_OPR_CC", "NEXT_OPR_FLTNUM", "NEXT_MKT_CC", "NEXT_MKT_FLTNUM",
                            "NEXT_SEG_DEP_DATE", "NEXT_SEG_ARR_DATE",
                            "POS", "BC", "FF", "TP",
                            "SMPWA", "AMPWA",
                            "SRD", "ARD", "SFD", "AFD",
                            "SRC_DATE"])
        for r in fdc.rows():
            csvwriter.writerow(r)
    
    print("Zipping file...")
    subprocess.check_output(["gzip", fname_out])

    print("Copying file to s3...")
    subprocess.check_output(["aws", "s3", "cp", fname_out + ".gz", "s3://" + csv2check])

    print("Cleaning-up...")
    subprocess.check_output(["rm", fname_out + ".gz"])
    return 1


def process_parallel(fcstdt, curdt, depdts):
    num_cores = multiprocessing.cpu_count()
    results = Parallel(n_jobs=int(num_cores))(delayed(process)(fcstdt, curdt, depdt) for depdt in depdts)
    return sum(results)


def process_non_parallel(fcstdt, curdt, depdts):
    num = 0
    for depdt in depdts:
        num += 1
        process(fcstdt, curdt, depdt)
    return num


if __name__ == "__main__":

    dt = datetime.now()
    for i in range(300):
        fcstdt, fcstfiles = s3getlastfcstfiles(dt)
        fcstdt = datetime.strftime(fcstdt, "%Y%m%d")

        depdt, depdts = dt, []
        for j in range(365):
            depdts.append(datetime.strftime(depdt, "%Y%m%d"))
            depdt += timedelta(days=1)

        try:        
            num = process_parallel(fcstdt, datetime.strftime(dt, "%Y%m%d"), depdts)
        except Exception as e:
            print("s3fdc2csv.py e = ", e)
            print(traceback.print_exc(file=sys.stdout))
        dt = dt - timedelta(days=1)


