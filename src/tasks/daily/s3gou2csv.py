import numpy as np
import csv
import traceback
import subprocess
from joblib import Parallel, delayed
import multiprocessing
from datetime import datetime, timedelta

from s3utils import *
#from emailutils import *


def process(depdt):
    print('depdt = ', depdt)
    csv2check = 'ay-rmp-home/nrm/gou/'+depdt[:4]+'/'+depdt[4:6]+'/gou_'+depdt+'.csv.gz'
    if s3fileexists(csv2check):
        return 0 

    # Reading bof.
    print('Reading bof...')
    bof = pd.read_csv('s3://ay-rmp-home/nrm/bof/'+depdt[:4]+'/'+depdt[4:6]+'/BKG_OD_'+depdt+'.csv.gz', low_memory = False)
    bof['ISO_COUNTRY'] = bof['ISO_COUNTRY'].replace(np.nan, 'ZZ')
    bof['ISO_REGION'] = bof['ISO_REGION'].replace(np.nan, '')
    bof['TDIRECTION'] = bof['TDIRECTION'].replace(np.nan, '')
    bof = bof.loc[bof['BASE_OD_DEPT_DATE'] == int(depdt)]
    bof = bof.groupby(['BASE_OD_ORGN','BASE_OD_DSTN',\
                       'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                       'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                       'BASE_OPR_CC','BASE_OPR_FLTNUM','BASE_OD_DEPT_DATE',\
                       'TDIRECTION','SELL_CLS','BKG_TYPE','ISO_COUNTRY','ISO_REGION'])\
             .agg({'REFERENCE': 'count', 'YIELD': 'sum'}).reset_index()
    bof['DOW'] = pd.to_datetime(bof['BASE_OD_DEPT_DATE'], format='%Y%m%d').dt.weekday
    bof.loc[bof['ISO_COUNTRY'] == 'ZZ', ['ISO_COUNTRY']] = 'ROW'

    # Reading pag.
    print('Reading pag...')
    pag = pd.read_csv('s3://ay-rmp-home/nrm/pa/'+depdt[:4]+'/'+depdt[4:6]+'/pag_'+depdt+'.csv.gz', low_memory = False)
    pag = pag.loc[pag['BASE_OD_DEPT_DATE'] == int(depdt)]
    pag['CREV'] = pag['MP'] * pag['LPC_AMD']
    pag = pag.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OPR_CC','BASE_OPR_FLTNUM',\
                       'BASE_OD_DEPT_DATE','BC','POS'])\
             .agg({'AMD': 'sum', 'LPC_AMD': 'sum', 'CREV': 'sum'}).reset_index()
    pag['DOW'] = pd.to_datetime(pag['BASE_OD_DEPT_DATE'], format='%Y%m%d').dt.weekday

    # Merge dataframes.
    print('Merging dataframes...')
    df = bof.merge(pag, left_on = ['BASE_OD_ORGN','BASE_OD_DSTN',\
                                   'BASE_OPR_CC','BASE_OPR_FLTNUM','BASE_OD_DEPT_DATE',\
                                   'ISO_COUNTRY','DOW','SELL_CLS'],\
                        right_on = ['BASE_OD_ORGN','BASE_OD_DSTN',\
                                    'BASE_OPR_CC','BASE_OPR_FLTNUM','BASE_OD_DEPT_DATE',\
                                    'POS','DOW','BC'],\
                        how = 'inner')

    fname_out = '/mnt/data/tmp/gou_' + depdt + '.csv'
    with open(fname_out, 'w') as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(['BASE_OD_ORGN','BASE_OD_DSTN',\
                            'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                            'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                            'BASE_OPR_CC','BASE_OPR_FLTNUM','BASE_OD_DEPT_DATE',\
                            'TDIRECTION','SELL_CLS','BKG_TYPE',\
                            'ISO_COUNTRY','ISO_REGION','YIELD',\
                            'REFERENCE','DOW','BC','POS','LPC_AMD','AMD','CREV','SRC_DATE'])
        
        for i,r in df.iterrows():
            row = [str(r['BASE_OD_ORGN']), str(r['BASE_OD_DSTN']),\
                   str(r['BASE_OD_ORGN_COUNTRY']), str(r['BASE_OD_ORGN_REGION']),\
                   str(r['BASE_OD_DSTN_COUNTRY']), str(r['BASE_OD_DSTN_REGION']),\
                   str(r['BASE_OPR_CC']), str(r['BASE_OPR_FLTNUM']), str(r['BASE_OD_DEPT_DATE']),\
                   str(r['TDIRECTION']), str(r['SELL_CLS']), str(r['BKG_TYPE']),\
                   str(r['ISO_COUNTRY']), str(r['ISO_REGION']), str(r['YIELD']),\
                   str(r['REFERENCE']), str(r['DOW']), str(r['BC']),\
                   str(r['POS']), str(r['LPC_AMD']), str(r['AMD']), str(r['CREV'])]
            csvwriter.writerow(row + [str(depdt)])

    print('Zipping file...')
    subprocess.check_output(['gzip', fname_out])
 
    print('Copying file to s3...')
    subprocess.check_output(['aws','s3','cp',fname_out+'.gz','s3://'+csv2check])

    print('Cleaning-up...')
    subprocess.check_output(['rm',fname_out+'.gz'])

    return 1 
 

def process_parallel(dts):
    num_cores = multiprocessing.cpu_count()
    results = Parallel(n_jobs = 5)(delayed(process)(dt) for dt in dts)
    return sum(results)


def process_non_parallel(dts):
    res = 0
    for dt in dts:
        res += process(dt)
    return res


if __name__ == "__main__":
    dts = []
    dt = datetime.now() - timedelta(days = 5)
    for i in range(365):
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



