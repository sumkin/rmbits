import csv
import boto3

from datetime import datetime, timedelta
from joblib import Parallel, delayed
import multiprocessing
import subprocess

from s3utils import *
from expdmdfitter import *

def process(fname: str, dtstr: str) -> int:
    depdt = fname.split("/")[5].split(".")[0].split("_")[3]

    csv2check = "ay-rmp-home/nrm/expdmd/" + dtstr[:4] +\
                                     "/" + dtstr[4:6] +\
                                     "/" + dtstr[6:8] +\
                                     "/expdmd_" + dtstr + "_" + depdt + ".csv.gz"
    if s3fileexists(csv2check):
        return 0

    fitter = ExpDmdFitter(dtstr, depdt)

    fname_out = "/home/ay49514/tmp/" + "exp_dmd_" + dtstr + "_" + depdt + ".csv"
    with open(fname_out, "w") as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(["GEO_OD_TS_KEY", "BASE_OD_ORGN", "BASE_OD_DSTN",
                            "POS", "TP", "FF", "SV", "SW", "AV", "AW"])
        for r in fitter.rows():
            csvwriter.writerow(r)

    # Zip file.
    subprocess.check_output(["gzip", fname_out])

    # Copy file to s3.
    s3_client = boto3.client("s3")
    subfolder = dtstr[:4] + "/" + dtstr[4:6] + "/" + dtstr[6:8]
    csvfname = csv2check.split("/")[-1]
    s3_client.upload_file(fname_out + ".gz", "ay-rmp-home", "nrm/expdmd/" + subfolder + "/" + csvfname)

    # Remove send file.
    subprocess.check_output(["rm", fname_out + ".gz"])

    return 1

def process_parallel(fnames, dtstr):
    num_cores = multiprocessing.cpu_count()
    results = Parallel(n_jobs = int(num_cores))(delayed(process)(fname, dtstr) for fname in fnames)
    return sum(results)

def process_non_parallel(fnames, dtstr):
    res = 0
    for fname in fnames:
        res += process(fname, dtstr)
    return res

if __name__ == "__main__":
    dt = datetime.now()
    for i in range(100):
        src_date = dt - timedelta(days = i)
        dtstr = datetime.strftime(src_date, "%Y%m%d")
        dty, dtm, dtd = dtstr[:4], dtstr[4:6], dtstr[6:8]
        fnames = gets3files(f"ay-rmp-home/nrm/bff/{dty}/{dtm}/{dtd}")
        if len(fnames) != 0:
            num = process_non_parallel(fnames, dtstr)






