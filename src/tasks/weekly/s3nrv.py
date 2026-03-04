import csv
import subprocess
from joblib import Parallel, delayed
import multiprocessing
from datetime import datetime, timedelta

from s3utils import *
from nrv.nrvreader import *
from funcutils import *

def process_exp(fname, dtstr):
    depdt = fname.split('/')[5].split('.')[0].split('_')[4]
    csv2check_exp = "ay-rmp-home/nrm/nrv_exp/{}/{}/{}/nrv_exp_{}_{}.csv.gz".format(dtstr[:4],
                                                                                  dtstr[4:6],
                                                                                  dtstr[6:8],
                                                                                  dtstr,
                                                                                  depdt)
    if s3fileexists(csv2check_exp):
        print(csv2check_exp, " exists")
        return 0

    print("Processing ", fname)

    #try:
    nrv = NRVReader(dtstr, depdt)
    nrv.read_dfs()
    #except Exception as e:
    #    print("e = {}".format(e))
    #    print("Failed on reading nrv values.")
    #    return 0

    fname_out = "/mnt/data/tmp/nrv_exp_{}_{}.csv".format(dtstr, depdt)
    with open(fname_out, "w") as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(["GEO_OD_TS_KEY",
                            "GEO_ORGN", "GEO_DSTN",
                            "BASE_OD_ORGN", "BASE_OD_ORGN_COUNTRY",
                            "BASE_OD_DSTN", "BASE_OD_DSTN_COUNTRY", "BASE_OD_DEPT_DATE",
                            "POS", "FF", "GFF", "TP", "NRV", "SRC_DATE"])
        for r in nrv.rows_exp():
            csvwriter.writerow(r + [dtstr])

    print("Zipping file...")
    try:
        try_x_times(3, subprocess.check_output)(["gzip", fname_out])
    except Exception as e:
        print("e = ", e)
        print("Failed on gzip")

    print("Copying file to s3...")
    try:
        try_x_times(3, subprocess.check_output)(["aws", "s3", "cp", fname_out+".gz", "s3://"+csv2check_exp])
    except Exception as e:
        print("e = ", e)
        print("Failed on copy...")

    print("Cleaning-up...")
    try:
        try_x_times(3, subprocess.check_output)(["rm", fname_out+".gz"])
    except Exception as e:
        print("e = ", e)
        print("Failed on removal...")
    
    return 1

def process_pwl(fname, dtstr):
    depdt = fname.split('/')[5].split('.')[0].split('_')[4]
    csv2check_pwl = "ay-rmp-home/nrm/nrv_pwl/{}/{}/{}/nrv_pwl_{}_{}.csv.gz".format(dtstr[:4],
                                                                                  dtstr[4:6],
                                                                                  dtstr[6:8],
                                                                                  dtstr,
                                                                                  depdt)
    if s3fileexists(csv2check_pwl):
        print(csv2check_pwl, " exists")
        return 0

    print("Processing ", fname)

    try:
        nrv = NRVReader(dtstr, depdt)
        nrv.read_dfs()
    except Exception as e:
        print("e = {}".format(e))
        print("Failed on reading nrv values.")
        return 0

    fname_out = "/mnt/data/tmp/nrv_pwl_{}_{}.csv".format(dtstr, depdt)
    with open(fname_out, "w") as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(["GEO_OD_TS_KEY",
                            "GEO_ORGN", "GEO_DSTN",
                            "BASE_OD_ORGN", "BASE_OD_ORGN_COUNTRY",
                            "BASE_OD_DSTN", "BASE_OD_DSTN_COUNTRY", "BASE_OD_DEPT_DATE",
                            "POS", "FF", "GFF", "TP", "NRV", "SRC_DATE"])
        for r in nrv.rows_pwl():
            csvwriter.writerow(r + [dtstr])

    print("Zipping file...")
    try:
        try_x_times(3, subprocess.check_output)(["gzip", fname_out])
    except Exception as e:
        print("e = ", e)
        print("Failed on gzip")

    print("Copying file to s3...")
    try:
        try_x_times(3, subprocess.check_output)(["aws", "s3", "cp", fname_out + ".gz", "s3://" + csv2check_pwl])
    except Exception as e:
        print("e = ", e)
        print("Failed on copy...")

    print("Cleaning-up...")
    try:
        try_x_times(3, subprocess.check_output)(["rm", fname_out + ".gz"])
    except Exception as e:
        print("e = ", e)
        print("Failed on removal...")

    return 1

def process_parallel(fnames, dtstr):
    num_cores = multiprocessing.cpu_count()
    results_exp = Parallel(n_jobs=int(num_cores))(delayed(process_exp)(fname, dtstr) for fname in fnames)
    results_pwl = Parallel(n_jobs=int(num_cores))(delayed(process_pwl)(fname, dtstr) for fname in fnames)
    return sum(results_exp) + sum(results_pwl)

def process_non_parallel(fnames, dtstr):
    res = 0
    for fname in fnames:
        res += process_exp(fname, dtstr)
        res += process_pwl(fname, dtstr)

if __name__ == "__main__":
    dt = datetime.now()
    for i in range(100):
        dtstr = datetime.strftime(dt, "%Y%m%d")
        dty, dtm, dtd = dtstr[:4], dtstr[4:6], dtstr[6:8]

        fnames = gets3files("ay-rmp-home/nrm/cf/"+dty+"/"+dtm+"/"+dtd)
        fnames = [fname for fname in fnames if "prdt_sens" in fname]

        if len(fnames) != 0:
            dt_s = datetime.now()
            num = process_parallel(fnames, dtstr)
            dt_e = datetime.now()
            sbj = str(num) + " nrv files have been processed for " + dtstr
            seconds = int((dt_e - dt_s).seconds)
            hours = seconds / 3600
            minutes = (seconds - hours * 3600) / 60
            seconds = (seconds - hours * 3600 - minutes * 60)
            txt = "Processed in " + str(hours) + " hours " + str(minutes) + " minutes " + str(seconds) + " seconds"

        dt = dt - timedelta(days=1)



