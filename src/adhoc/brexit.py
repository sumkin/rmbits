import csv
import subprocess
from joblib import Parallel, delayed
import multiprocessing
from datetime import datetime, timedelta

from s3utils import *
from constrfrcst import *


def process(fname, dtstr):
    depdt = fname.split('/')[5].split('.')[0].split('_')[2]
    if depdt < '20190329':
        return
    csvout = 'ay-rmp-home/nrm/brexit_cf/' + dtstr[:4] + '/' + dtstr[4:6] + '/' + dtstr[6:8] +\
                                     '/br_cf_' + dtstr + '_' + depdt + '.csv.gz'
    if s3fileexists(csvout):
        print csvout, ' exists'
        return 0

    csv_sar_orig = 'ay-rmp-home/nrm/brexit_cf/' + dtstr[:4] + '/' + dtstr[4:6] + '/' + dtstr[6:8] +\
                                           '/br_cf_sar_orig_' + dtstr + '_' + depdt + '.txt.gz'
    csv_sar_rows = 'ay-rmp-home/nrm/brexit_cf/' + dtstr[:4] + '/' + dtstr[4:6] + '/' + dtstr[6:8] +\
                                           '/br_cf_sar_rows_' + dtstr + '_' + depdt + '.csv.gz'
    csv_sar_cols = 'ay-rmp-home/nrm/brexit_cf/' + dtstr[:4] + '/' + dtstr[4:6] + '/' + dtstr[6:8] +\
                                           '/br_cf_sar_cols_' + dtstr + '_' + depdt + '.csv.gz'

    cf = ConstrFrcst(dtstr, depdt)
    maxval, maxsol = cf.solve_max()
    minsol = [0] * len(maxsol)

    fname_out = '/home/ay49514/tmp/br_cf_' + dtstr + '_' + depdt + '.csv'
    fname_out_sar_orig = '/home/ay49514/tmp/br_cf_sar_orig_' + dtstr + '_' + depdt + '.txt'
    fname_out_sar_rows = '/home/ay49514/tmp/br_cf_sar_rows_' + dtstr + '_' + depdt + '.csv'
    fname_out_sar_cols = '/home/ay49514/tmp/br_cf_sar_cols_' + dtstr + '_' + depdt + '.csv'

    with open(fname_out, 'w') as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                            'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                            'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                            'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                            'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                            'BASE_OD_DEPT_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE',\
                            'GEO_ORGN','GEO_DSTN',\
                            'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM','PREV_MKT_CC','PREV_MKT_FLTNUM','PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                            'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM','NEXT_MKT_CC','NEXT_MKT_FLTNUM','NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE',\
                            'POS','FF','BC','TP','MP','F',\
                            'SRD','ARD','SFD','AFD',\
                            'GCC_ARMD','GCC_SRMD','GCC_AFMD','GCC_SFMD','ADC','SDC','AMDC','SMDC','D',\
                            'LPC_D','LPC_D_MIN','CREV','SRC_DATE'])
        for r in cf.rows(maxsol, minsol):
            csvwriter.writerow(r + [dtstr])

    print 'Producing sensitivity report...'
    cf.sens_report(fname_out_sar_orig,\
                   fname_out_sar_rows,\
                   fname_out_sar_cols)

    print 'Zipping file...'
    subprocess.check_output(['gzip', fname_out])
    subprocess.check_output(['gzip', fname_out_sar_orig])
    subprocess.check_output(['gzip', fname_out_sar_rows])
    subprocess.check_output(['gzip', fname_out_sar_cols])

    subprocess.check_output(['aws','s3','cp',fname_out+'.gz','s3://'+csvout])
    subprocess.check_output(['aws','s3','cp',fname_out_sar_orig+'.gz','s3://'+csv_sar_orig])
    subprocess.check_output(['aws','s3','cp',fname_out_sar_rows+'.gz','s3://'+csv_sar_rows])
    subprocess.check_output(['aws','s3','cp',fname_out_sar_cols+'.gz','s3://'+csv_sar_cols])

    subprocess.check_output(['rm', fname_out+'.gz'])
    subprocess.check_output(['rm', fname_out_sar_orig+'.gz'])
    subprocess.check_output(['rm', fname_out_sar_rows+'.gz'])
    subprocess.check_output(['rm', fname_out_sar_cols+'.gz'])


if __name__ == "__main__":
    dt = datetime.now() - timedelta(days = 1)
    dtstr = datetime.strftime(dt, "%Y%m%d")
    print "dtstr = ", dtstr
    dty = dtstr[:4]
    dtm = dtstr[4:6]
    dtd = dtstr[6:8]

    fnames = gets3files("ay-rmp-home/nrm/fdc/"+dty+"/"+dtm+"/"+dtd)
    num_cores = multiprocessing.cpu_count()
    results = Parallel(n_jobs = num_cores)(delayed(process)(fname, dtstr) for fname in fnames)

 


