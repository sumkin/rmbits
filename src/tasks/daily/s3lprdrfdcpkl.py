from datetime import datetime, timedelta
from joblib import Parallel, delayed
import gzip
import pickle
import multiprocessing
import traceback

from s3utils import *
from lpreaderfdc import *
from funcutils import *

def process(fname, dtstr):
    print("Processing ", fname)

    modes = ["remaining", "final"]
    for mode in modes:
        depdt = fname.split('/')[5].split('.')[0].split('_')[2]
        ndepdt = datetime.strftime(datetime.strptime(depdt, "%Y%m%d") + timedelta(days=1),"%Y%m%d")

        pkl2check = "ay-rmp-home/nrm/lprdrfdcpkl/{}/{}/{}/lprdrfdcpkl_{}_{}_{}.pkl.gz".format(dtstr[:4],
                                                                                             dtstr[4:6],
                                                                                             dtstr[6:8],
                                                                                             dtstr,
                                                                                             depdt,
                                                                                             mode)
    
        if s3fileexists(pkl2check):
            print(pkl2check, " exists")
            return 0

        fdc2check = "ay-rmp-home/nrm/fdc/{}/{}/{}/fdc_{}_{}.csv.gz".format(dtstr[:4],
                                                                          dtstr[4:6],
                                                                          dtstr[6:8],
                                                                          dtstr,
                                                                          depdt)
        nfdc2check = "ay-rmp-home/nrm/fdc/{}/{}/{}/fdc_{}_{}.csv.gz".format(dtstr[:4],
                                                                           dtstr[4:6],
                                                                           dtstr[6:8],
                                                                           dtstr,
                                                                           ndepdt)
        if not s3fileexists(fdc2check) or not s3fileexists(nfdc2check):
            return 0    

        decompdt = depdt
        lpreaderfdc = LPReaderFDC(dtstr, decompdt, mode=mode)
        lpreaderfdc.read()
        pklobj = lpreaderfdc.get_pkl_object()

        print("Pickling file...")
        pklfnamegz = "/mnt/data/tmp/lpreaderfdcpkl_{}_{}_{}.pkl.gz".format(dtstr, depdt, mode)
        with gzip.open(pklfnamegz, "wb") as fout:
            pickle.dump(pklobj, fout, protocol=4)

        print("Copying file to s3...")
        try:
            try_x_times(3, subprocess.check_output)(["aws", "s3", "cp", pklfnamegz, "s3://" + pkl2check])
        except:
            print("Failed on copy...")

        print("Cleaning-up...")
        try:
            try_x_times(3, subprocess.check_output(["rm", pklfnamegz]))
        except:
            print("Failed on removal...")

    return 1

def process_parallel(fnames, dtstr):
    num_cores = multiprocessing.cpu_count()
    results = Parallel(n_jobs=int((2 * num_cores) / 3))(delayed(process)(fname, dtstr) for fname in fnames)
    return sum(results)

def process_non_parallel(fnames, dtstr):
    num = 0
    for fname in fnames:
        process(fname, dtstr)
        num += 1
    return num

if __name__ == "__main__":
    dt = datetime.now() - timedelta(days=1)
    for i in range(100):
        dtstr = datetime.strftime(dt, "%Y%m%d")
        dty, dtm, dtd = dtstr[:4], dtstr[4:6], dtstr[6:8]

        try:
            fnames = gets3files("ay-rmp-home/nrm/fdc/{}/{}/{}".format(dty, dtm, dtd))
            if len(fnames) != 0:
                num = 0
                try:
                    num = process_parallel(fnames, dtstr)
                except Exception as e:
                    print(e)
                    traceback.print_exc()
                    pass
        except Exception as e:
            print("e = ", e)
            traceback.print_exc()
        dt = dt - timedelta(days=1)


