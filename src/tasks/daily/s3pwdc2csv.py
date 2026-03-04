import csv
import subprocess
from joblib import Parallel, delayed
import multiprocessing
from datetime import datetime, timedelta
import traceback

from s3utils import *
from pwdcreader import *
#from emailutils import *


def process(fname, dtstr_prev, dtstr):
    print('fname = ', fname)
    print('dtstr_prev = ', dtstr_prev)
    print('dtstr = ', dtstr)
    depdt = fname.split('/')[5].split('.')[0].split('_')[3]

    csv2check = 'ay-rmp-home/nrm/pwdc/' + dtstr[:4] +\
                                   '/' + dtstr[4:6] +\
                                   '/' + dtstr[6:8] +\
                                   '/dc_' + dtstr_prev + '_' + dtstr + '_' + depdt + '.csv.gz'
    if s3fileexists(csv2check):
        print(csv2check, ' exists')
        return 0

    if not s3fileexists('s3://ay-rmp-home/nrm/bff/' + dtstr[:4] + '/' + dtstr[4:6] +\
                                               '/FCST_OD_' + dtstr + '_' + depdt + '.csv.gz'):
        return 0
    if not s3fileexists('s3://ay-rmp-home/nrm/bff/' + dtstr_prev[:4] + '/' + dtstr_prev[4:6] +\
                                               '/FCST_OD_' + dtstr_prev + '_' + depdt + '.csv.gz'):
        return 0

    pwdc = PWDCReader(dtstr_prev, dtstr, depdt)
    fname_out = "/mnt/data/tmp/dc_" + dtstr_prev + "_" + dtstr + "_" + depdt + ".csv"
    with open(fname_out, "w") as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                            'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                            'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                            'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                            'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                            'BASE_OD_DEP_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE',\
                            'GEO_ORGN','GEO_DSTN',\
                            'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM',\
                            'PREV_MKT_CC','PREV_MKT_FLTNUM',\
                            'PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                            'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM',\
                            'NEXT_MKT_CC','NEXT_MKT_FLTNUM',\
                            'NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE',\
                            'POS','FF','TP','BC','MP','F','AD','SD','AMD','SMD'])
        for r in pwdc.rows():      
            csvwriter.writerow(r)
    
    print("Zipping file...")
    subprocess.check_output(['gzip',fname_out])

    print("Copying file to s3...")
    subprocess.check_output(['aws','s3','cp',fname_out+'.gz','s3://'+csv2check])    

    print("Cleaning-up...")
    subprocess.check_output(['rm', fname_out+'.gz'])
    return 1


def process_parallel(fnames, dtstr_prev, dtstr):
    num_cores = multiprocessing.cpu_count()
    results = Parallel(n_jobs = num_cores - 1)(delayed(process)(fname, dtstr_prev, dtstr) for fname in fnames)
    return sum(results)


def process_non_parallel(fnames, dtstr_prev, dtstr):
    num = 0
    for fname in fnames:
        num += process(fname, dtstr_prev, dtstr)
    return num


if __name__ == "__main__":
    dt = datetime.now()
    for i in range(365):
        dtstr = datetime.strftime(dt, "%Y%m%d")
        dty = dtstr[:4]
        dtm = dtstr[4:6]
        dtd = dtstr[6:8]

        try:        
            fnames = gets3files('ay-rmp-home/nrm/bff/'+dty+'/'+dtm+'/'+dtd)
            if len(fnames) != 0:
                dt_s = datetime.now()
                for i in range(1,10):
                    dtstr_prev = datetime.strftime(dt - timedelta(days=i), "%Y%m%d")
                    dty_prev = dtstr_prev[:4]
                    dtm_prev = dtstr_prev[4:6]
                    dtd_prev = dtstr_prev[6:8]
                    fnames_prev = gets3files('ay-rmp-home/nrm/bff/'+dty_prev+'/'+dtm_prev+'/'+dtd_prev)
                    if len(fnames_prev) > 0:
                        break
                num = process_parallel(fnames, dtstr_prev, dtstr)
                dt_e = datetime.now()
                if num > 0:
                    sbj = str(num) + ' pwdc files processed for ' + dtstr_prev + '-' + dtstr
                    seconds = int((dt_e - dt_s).seconds)
                    hours = seconds / 3600
                    minutes = (seconds - hours * 3600) / 60
                    seconds = (seconds - hours * 3600 - minutes * 60)
                    txt = 'Processed in ' + str(hours) + ' hours ' + str(minutes) + ' minutes ' + str(seconds) + ' seconds.'
                    send_quick('fedor.nikitin@finnair.com','fedor.nikitin@finnair.com',sbj,txt)
                if len(fnames_prev) == 0:
                    print('dtd_prev = ', dtd_prev)
                    print('dty_prev = ', dty_prev)
                    print('dtm_prev = ', dtm_prev)
                    print('dtd = ', dtd)
                    print('dty = ', dty)
                    print('dtm = ', dtm)
                assert len(fnames_prev) > 0
        except Exception as e:
            print(e)
            traceback.print_exc()
        dt = dt - timedelta(days=1)


