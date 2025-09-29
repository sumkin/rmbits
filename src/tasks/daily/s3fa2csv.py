import csv
import subprocess
from joblib import Parallel, delayed
import multiprocessing
from datetime import datetime, timedelta

from s3utils import *
from fareader import *
#from emailutils import *


def process(bkgdate, depdate):
    csv2check = 'ay-emr-job/nrm/fa/' + bkgdate[:4] +\
                                 '/' + bkgdate[4:6] +\
                                 '/' + bkgdate[6:8] +\
                                 '/fa_' + bkgdate + '_' + depdate + '.csv.gz'
    if s3fileexists(csv2check):
        print(csv2check, ' exists')
        return 0

    try:
        fardr = FAReader(bkgdate, depdate)
        fardr.read_dfs()
    except Exception as e:
        print(e)
        return 0

    fname_out = '/mnt/data/tmp/fa_' + bkgdate + '_' + depdate + '.csv'
    with open(fname_out, 'w') as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OPR_CC','BASE_OPR_FLTNUM','BASE_OD_DEP_DATE',\
                            'POS','FF',\
                            'SC','SSCD','ASCD','SCYIELD','MPSC',\
                            'GC','SGCD','AGCD','GCYIELD','MPGC',\
                            'BKGCNT','BKGYIELD','AVSC','BKGDATE'])
        for r in fardr.rows():
            csvwriter.writerow(r)

    print("Zipping file...")
    subprocess.check_output(['gzip',fname_out])

    print("Copying file to s3...")
    subprocess.check_output(['aws','s3','cp',fname_out+'.gz','s3://'+csv2check])

    print("Cleaning-up...")
    subprocess.check_output(['rm', fname_out+'.gz'])
    return 1


def process_parallel(bkgdate, depdates):
    num_cores = multiprocessing.cpu_count()
    results = Parallel(n_jobs = int(num_cores / 2))(delayed(process)(bkgdate, depdate) for depdate in depdates)
    return sum(results)


def process_non_parallel(bkgdate, depdates):
    num = 0
    for depdate in depdates:
        num += 1
        process(bkgdate, depdate)
    return num


if __name__ == "__main__":

    bkgdt = datetime.now()
    for i in range(370):
        bkgdate = datetime.strftime(bkgdt, '%Y%m%d')

        depdates = []
        dt = datetime.now()
        for i in range(365):
            depdate = datetime.strftime(dt, '%Y%m%d')
            dt = dt + timedelta(days = 1)
            depdates.append(depdate)

        process_parallel(bkgdate, depdates)
        bkgdt = bkgdt - timedelta(days = 1)





