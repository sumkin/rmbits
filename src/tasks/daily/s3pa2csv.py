import csv
import traceback
import subprocess
from joblib import Parallel, delayed
import multiprocessing
from datetime import datetime, timedelta
import pickle

from s3utils import *
from postanalysis import *
#from emailutils import *


def process(depdt):
    print('Processing ', depdt)
    csv2check = 'ay-emr-job/nrm/pa/' + depdt[:4] +\
                                 '/' + depdt[4:6] +\
                                 '/pa_' + depdt + '.csv.gz'
    csv2checkg = 'ay-emr-job/nrm/pa/' + depdt[:4] +\
                                  '/' + depdt[4:6] +\
                                  '/pag_' + depdt + '.csv.gz'
    if s3fileexists(csv2check) and s3fileexists(csv2checkg):
        print(csv2check, ' and ', csv2checkg, ' exists')
        return 0
     
    pa = PostAnalysis(depdt)
    val,sol = pa.solve()

    fname_out = '/mnt/data/tmp/pa_' + depdt + '.csv'
    with open(fname_out, 'w') as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                            'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                            'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                            'BASE_OD_DEPT_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE',\
                            'GEO_ORGN','GEO_DSTN',\
                            'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM',\
                            'PREV_MKT_CC','PREV_MKT_FLTNUM',\
                            'PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                            'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM',\
                            'NEXT_MKT_CC','NEXT_MKT_FLTNUM',\
                            'NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE',\
                            'POS','FF','BC','TP','MP','F',\
                            'AMD','LPC_AMD','LPC_AMD_MIN','FIRST_FCST_DATE','LAST_FCST_DATE','SRC_DATE'])
        for r in pa.rows(sol):
            csvwriter.writerow(r + [depdt])

    valg,solg = pa.solve_groups()

    fname_outg = '/mnt/data/tmp/pag_' + depdt + '.csv'
    with open(fname_outg, 'w') as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                            'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                            'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                            'BASE_OD_DEPT_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE',\
                            'GEO_ORGN','GEO_DSTN',\
                            'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM',\
                            'PREV_MKT_CC','PREV_MKT_FLTNUM',\
                            'PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                            'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM',\
                            'NEXT_MKT_CC','NEXT_MKT_FLTNUM',\
                            'NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE',\
                            'POS','FF','BC','TP','MP','F',\
                            'AMD','LPC_AMD','LPC_AMD_MIN','FIRST_FCST_DATE','LAST_FCST_DATE','SRC_DATE'])
        for r in pa.rows(solg):
            csvwriter.writerow(r + [depdt])

    print('Zipping files...')
    subprocess.check_output(['gzip', fname_out])
    subprocess.check_output(['gzip', fname_outg])

    print('Copying files to s3...')
    subprocess.check_output(['aws','s3','cp',fname_out+'.gz','s3://'+csv2check])
    subprocess.check_output(['aws','s3','cp',fname_outg+'.gz','s3://'+csv2checkg])

    print('Cleaning-up...')
    subprocess.check_output(['rm', fname_out + '.gz'])
    subprocess.check_output(['rm', fname_outg + '.gz'])
 
    return 1


def process_parallel(dts):
    num_cores = multiprocessing.cpu_count()
    results = Parallel(n_jobs = 2)(delayed(process)(dt) for dt in dts)
    return sum(results)


def process_non_parallel(dts):
    for dt in dts:
        process(dt)


if __name__ == "__main__":
    dts = []
    dt = datetime.now() - timedelta(days = 1)
    for i in range(3):
        dtstr = datetime.strftime(dt, '%Y%m%d')
        dts.append(dtstr)
        dt = dt - timedelta(days = 1)

    dt_b = datetime.now()
    process_non_parallel(dts)
    dt_e = datetime.now()

    seconds = int((dt_e - dt_b).second)
    hours = seconds / 3600
    minutes = (seconds - hours * 3600) / 60
    seconds = (seconds - hours * 3600 - minutes * 60)

    sbj = csv_fname + ' has been processed.'
    body = 'Processed in ' + str(hours) + ' hours ' + str(minutes) + ' minutes ' + str(seconds) + ' seconds'
    send_quick('fedor.nikitin@finnair.com', 'fedor.nikitin@finnair.com', sbj, body)




