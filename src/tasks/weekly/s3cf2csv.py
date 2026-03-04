import csv
import subprocess
from joblib import Parallel, delayed
import multiprocessing
from datetime import datetime, timedelta

from s3utils import *
from constrfrcst import *
#from emailutils import *
from funcutils import *

prefix = ''


def process(fname, dtstr):
    decompdt = fname.split('/')[5].split('.')[0].split('_')[3]

    csv2check = "ay-rmp-home/nrm/{}cf/{}/{}/{}/{}cf_{}_{}.csv.gz".format(prefix,
                                                                        dtstr[:4],
                                                                        dtstr[4:6],
                                                                        dtstr[6:8],
                                                                        prefix,
                                                                        dtstr,
                                                                        decompdt)
    csv2check_sp = "ay-rmp-home/nrm/{}cf/{}/{}/{}/{}cf_sp_{}_{}.csv.gz".format(prefix,
                                                                              dtstr[:4],
                                                                              dtstr[4:6],
                                                                              dtstr[6:8],
                                                                              prefix,
                                                                              dtstr,
                                                                              decompdt)
    csv2check_rsrc_sens = "ay-rmp-home/nrm/{}cf/{}/{}/{}/{}cf_rsrc_sens_{}_{}.csv.gz".format(prefix,
                                                                                            dtstr[:4],
                                                                                            dtstr[4:6],
                                                                                            dtstr[6:8],
                                                                                            prefix,
                                                                                            dtstr,
                                                                                            decompdt)
    csv2check_prdt_sens = "ay-rmp-home/nrm/{}cf/{}/{}/{}/{}cf_prdt_sens_{}_{}.csv.gz".format(prefix,
                                                                                            dtstr[:4],
                                                                                            dtstr[4:6],
                                                                                            dtstr[6:8],
                                                                                            prefix,
                                                                                            dtstr,
                                                                                            decompdt)
    if s3fileexists(csv2check) and\
       s3fileexists(csv2check_sp) and\
       s3fileexists(csv2check_rsrc_sens) and\
       s3fileexists(csv2check_prdt_sens):
        print(csv2check, csv2check_sp, csv2check_rsrc_sens, csv2check_prdt_sens, " exist")
        return 0

    cf = ConstrFrcst(dtstr, decompdt)
    maxval, maxsol = cf.solve_max()
    if len(maxsol) == 0:
        print("Zero length solution")
        return 0
    minval, minsol = 0, [0] * len(maxsol)

    fname_out = "/home/ay49514/tmp/{}cf_{}_{}.csv".format(prefix, dtstr, decompdt)
    with open(fname_out, "w") as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(["GEO_OD_TS_KEY", "BASE_OD_ORGN", "BASE_OD_DSTN", "BASE_OD_VIA",
                            "BASE_OD_ORGN_COUNTRY", "BASE_OD_ORGN_REGION",
                            "BASE_OD_DSTN_COUNTRY", "BASE_OD_DSTN_REGION",
                            "BASE_OPR_CC", "BASE_OPR_FLTNUM",
                            "BASE_MKT_CC", "BASE_MKT_FLTNUM",
                            "BASE_OD_DEPT_DATE", "BASE_SEG_DEP_DATE", "BASE_SEG_ARR_DATE",
                            "GEO_ORGN", "GEO_DSTN",
                            "PREV_VIA", "PREV_OPR_CC", "PREV_OPR_FLTNUM", "PREV_MKT_CC", "PREV_MKT_FLTNUM",
                            "PREV_SEG_DEP_DATE", "PREV_SEG_ARR_DATE",
                            "NEXT_VIA", "NEXT_OPR_CC", "NEXT_OPR_FLTNUM", "NEXT_MKT_CC", "NEXT_MKT_FLTNUM",
                            "NEXT_SEG_DEP_DATE", "NEXT_SEG_ARR_DATE",
                            "POS", "BC", "FF", "TP", "MP", "D", "LPS", "SRC_DATE"])
        for r in cf.rows(maxsol, minsol):
            csvwriter.writerow(r + [dtstr])

    fname_sp_out = "/home/ay49514/tmp/{}cf_sp_{}_{}.csv".format(prefix, dtstr, decompdt)
    with open(fname_sp_out, "w") as fsout:
        csvwriter = csv.writer(fsout)
        csvwriter.writerow(["CC", "FLTNUM", "CABIN", "DEPDT", "CAP", "SPOILAGE", "SRC_DATE"])
        ns, cs, ss = cf.slack_rows()
        assert len(cs) == len(ss)
        assert len(ss) == len(ns)
        for i in range(len(cs)):
            n = ns[i]
            c = cs[i]
            s = ss[i]

            cc = n[:2]
            fltnum = n[2:6]
            cmpt = n[6]
            depdt = n[7:15]

            r = [cc, fltnum, cmpt, depdt, c, s]
            csvwriter.writerow(r + [dtstr])

    fname_rsrc_sens_out = "/home/ay49514/tmp/{}cf_rsrc_sens_{}_{}.csv".format(prefix, dtstr, decompdt)
    with open(fname_rsrc_sens_out, "w") as fsout:
        csvwriter = csv.writer(fsout)
        csvwriter.writerow(["CC", "FLTNUM", "CABIN", "DEPDT", "DUAL", "LOW", "HIGH", "SRC_DATE"])
        ns, sps, slows, shighs = cf.sp_rsrc_rows()
        assert len(ns) == len(sps)
        assert len(ns) == len(slows)
        assert len(ns) == len(shighs)
        for i in range(len(ns)):
            n = ns[i]
            sp = sps[i]
            slow = slows[i]
            shigh = shighs[i]

            cc = n[:2]
            fltnum = n[2:6]
            cmpt = n[6]
            depdt = n[7:15]

            r = [cc, fltnum, cmpt, depdt, sp, slow, shigh]
            csvwriter.writerow(r + [dtstr])

    fname_prdt_sens_out = "/home/ay49514/tmp/{}cf_prdt_sens_{}_{}.csv".format(prefix, dtstr, decompdt)
    with open(fname_prdt_sens_out, "w") as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(["GEO_OD_TS_KEY", "BASE_OD_ORGN", "BASE_OD_DSTN", "BASE_OD_VIA",
                            "BASE_OD_ORGN_COUNTRY", "BASE_OD_ORGN_REGION",
                            "BASE_OD_DSTN_COUNTRY", "BASE_OD_DSTN_REGION",
                            "BASE_OPR_CC", "BASE_OPR_FLTNUM",
                            "BASE_MKT_CC", "BASE_MKT_FLTNUM",
                            "BASE_OD_DEPT_DATE", "BASE_SEG_DEP_DATE", "BASE_SEG_ARR_DATE",
                            "GEO_ORGN", "GEO_DSTN",
                            "PREV_VIA", "PREV_OPR_CC", "PREV_OPR_FLTNUM", "PREV_MKT_CC", "PREV_MKT_FLTNUM",
                            "PREV_SEG_DEP_DATE", "PREV_SEG_ARR_DATE",
                            "NEXT_VIA", "NEXT_OPR_CC", "NEXT_OPR_FLTNUM", "NEXT_MKT_CC", "NEXT_MKT_FLTNUM",
                            "NEXT_SEG_DEP_DATE", "NEXT_SEG_ARR_DATE",
                            "POS", "BC", "FF", "TP", "CABIN",
                            "DUAL", "LOW", "HIGH", "SRC_DATE"])
        for r in cf.sp_prdt_rows(maxsol):
            csvwriter.writerow(r + [dtstr])

    print("Zipping file...")
    try:
        try_x_times(3, subprocess.check_output)(["gzip", fname_out])
        try_x_times(3, subprocess.check_output)(["gzip", fname_sp_out])
        try_x_times(3, subprocess.check_output)(["gzip", fname_rsrc_sens_out])
        try_x_times(3, subprocess.check_output)(["gzip", fname_prdt_sens_out])
    except Exception as e:
        print(e)
        print("Failed on gzip")

    print("Copying file to s3...")
    try:
        try_x_times(3, subprocess.check_output)(["aws", "s3", "cp", fname_out+".gz", "s3://" + csv2check])
        try_x_times(3, subprocess.check_output)(["aws", "s3", "cp", fname_sp_out+".gz", "s3://" + csv2check_sp])
        try_x_times(3, subprocess.check_output)(["aws", "s3", "cp", fname_rsrc_sens_out+".gz", "s3://" + csv2check_rsrc_sens])
        try_x_times(3, subprocess.check_output)(["aws", "s3", "cp", fname_prdt_sens_out+".gz", "s3://" + csv2check_prdt_sens])
    except:
        print("Failed on copy...")

    print("Cleaning-up...")
    try:
        try_x_times(3, subprocess.check_output)(["rm", fname_out + ".gz"])
        try_x_times(3, subprocess.check_output)(["rm", fname_sp_out + ".gz"])
        try_x_times(3, subprocess.check_output)(["rm", fname_rsrc_sens_out + ".gz"])
        try_x_times(3, subprocess.check_output)(["rm", fname_prdt_sens_out + ".gz"])
    except:
        print("Failed on removal...")

    return 1


def process_parallel(fnames, dtstr):
    num_cores = multiprocessing.cpu_count()
    results = Parallel(n_jobs=num_cores - 3)(delayed(process)(fname, dtstr) for fname in fnames)
    return sum(results)


def process_non_parallel(fnames, dtstr):
    for fname in fnames:
        print("fname = {}".format(fname))
        process(fname, dtstr)


if __name__ == "__main__":
    dt = datetime.now()
    for i in range(100):
        dtstr = datetime.strftime(dt, "%Y%m%d")
        dty = dtstr[:4]
        dtm = dtstr[4:6]
        dtd = dtstr[6:8]

        fnames = gets3files("ay-rmp-home/nrm/bff/{}/{}/{}".format(dty, dtm, dtd))
        fnames = [fname for fname in fnames if "final" not in fname]
        if len(fnames) != 0:
            dt_s = datetime.now()
            num = process_non_parallel(fnames, dtstr)
            dt_e = datetime.now()
            sbj = str(num) + " cf files have been processed for " + dtstr
            seconds = int((dt_e - dt_s).seconds)
            hours = seconds / 3600
            minutes = (seconds - hours * 3600) / 60
            seconds = (seconds - hours * 3600 - minutes * 60)
            txt = "Processed in " + str(hours) + " hours " + str(minutes) + " minutes " + str(seconds) + " seconds"
        dt = dt - timedelta(days=1)



