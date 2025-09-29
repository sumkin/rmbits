import os
import sys
import csv
import subprocess
from datetime import datetime, timedelta
import pandas as pd

from s3utils import *
#from emailutils import *

def process(dt):

    currcsvfname = 'ay-emr-job/nrm/bof/' + dt[:4] + '/' + dt[4:6] + '/BKG_OD_' + dt + '.csv.gz' 
    if not s3fileexists(currcsvfname):
        print(currcsvfname, ' does not exist')
        return 0

    prevdt = datetime.strptime(dt,'%Y%m%d') - timedelta(days=1)
    prevdt = datetime.strftime(prevdt, '%Y%m%d')
    prevdty = prevdt[:4]
    prevdtm = prevdt[4:6]
    prevdtd = prevdt[6:8]
    num = 10
    for i in range(num):
        prevcsvfname = 'ay-emr-job/nrm/bof/' + prevdt[:4] + '/' + prevdt[4:6] + '/BKG_OD_' + prevdt + '.csv.gz'
        if not s3fileexists(prevcsvfname):
            print(prevcsvfname, ' does not exist')
            prevdt = datetime.strftime(datetime.strptime(prevdt,'%Y%m%d') - timedelta(days=1), '%Y%m%d')
            prevdty = prevdt[:4]
            prevdtm = prevdt[4:6]
            prevdtd = prevdt[6:8]
            if i == num - 1:
                return 0
        else:
            break

    ncsv2check = 'ay-emr-job/nrm/bcd/' + dt[:4] + '/' + dt[4:6] + '/bkgd_' + prevdt + '_' + dt + '.csv.gz'
    if s3fileexists(ncsv2check):
        print(ncsv2check, ' exists')
        return 0
    ccsv2check = 'ay-emr-job/nrm/bcd/' + dt[:4] + '/' + dt[4:6] + '/cnld_' + prevdt + '_' + dt + '.csv.gz'
    if s3fileexists(ccsv2check):
        print(ccsv2check, ' exists')
        return 0

    print('Reading dataframes...')
    prev_df = pd.read_csv('s3://' + prevcsvfname, low_memory = False).fillna('')
    curr_df = pd.read_csv('s3://' + currcsvfname, low_memory = False).fillna('')
  
    print('Merging dataframes...')
    df = prev_df.merge(curr_df, on = 'REFERENCE', how = 'outer', suffixes = ['_PREV','_CURR'])

    print('Merged.')
    print('New bookings.')
    ndf = df.loc[df['SELL_CLS_PREV'].isnull()]
    ndf = ndf[[u'BASE_OD_ORGN_CURR', u'BASE_OD_DSTN_CURR',
               u'BASE_OD_VIA_CURR', u'BASE_OD_ORGN_COUNTRY_CURR',
               u'BASE_OD_ORGN_REGION_CURR', u'BASE_OD_DSTN_COUNTRY_CURR',
               u'BASE_OD_DSTN_REGION_CURR', u'BASE_OPR_CC_CURR',
               u'BASE_OPR_FLTNUM_CURR', u'BASE_MKT_CC_CURR', u'BASE_MKT_FLTNUM_CURR',
               u'BASE_OD_DEPT_DATE_CURR', u'DAYSPRIOR_CURR',
               u'BASE_SEG_DEPT_DATE_CURR', u'BASE_SEG_ARR_DATE_CURR', u'GEO_ORGN_CURR', u'GEO_DSTN_CURR',
               u'PREV_VIA_CURR', u'PREV_OPR_CC_CURR', u'PREV_OPR_FLTNUM_CURR',
               u'PREV_MKT_CC_CURR', u'PREV_MKT_FLTNUM_CURR',
               u'PREV_SEG_DEPT_DATE_CURR', u'PREV_SEG_ARR_DATE_CURR', u'NEXT_VIA_CURR', u'NEXT_OPR_CC_CURR',
               u'NEXT_OPR_FLTNUM_CURR', u'NEXT_MKT_CC_CURR', u'NEXT_MKT_FLTNUM_CURR',
               u'NEXT_SEG_DEPT_DATE_CURR', u'NEXT_SEG_ARR_DATE_CURR',
               u'RLOCATOR_CURR', u'TDIRECTION_CURR',
               u'BKG_TYPE_CURR', u'PSEUDO_CITY_CODE_CURR',
               u'ISO_COUNTRY_CURR', u'ISO_REGION_CURR', u'AGDUTY_CODE_CURR', u'REQUESTOR_ID_CURR',
               u'SELL_CLS_CURR', u'CABIN_CURR', u'REFERENCE', u'YIELD_CURR', u'SRC_DATE_CURR']]        
    ndf.columns = [u'BASE_OD_ORGN', u'BASE_OD_DSTN',
                   u'BASE_OD_VIA', u'BASE_OD_ORGN_COUNTRY',
                   u'BASE_OD_ORGN_REGION', u'BASE_OD_DSTN_COUNTRY',
                   u'BASE_OD_DSTN_REGION', u'BASE_OPR_CC',
                   u'BASE_OPR_FLTNUM', u'BASE_MKT_CC', u'BASE_MKT_FLTNUM',
                   u'BASE_OD_DEPT_DATE', u'DAYSPRIOR',
                   u'BASE_SEG_DEPT_DATE', u'BASE_SEG_ARR_DATE', u'GEO_ORGN', u'GEO_DSTN',
                   u'PREV_VIA', u'PREV_OPR_CC', u'PREV_OPR_FLTNUM',
                   u'PREV_MKT_CC', u'PREV_MKT_FLTNUM',
                   u'PREV_SEG_DEPT_DATE', u'PREV_SEG_ARR_DATE', u'NEXT_VIA', u'NEXT_OPR_CC',
                   u'NEXT_OPR_FLTNUM', u'NEXT_MKT_CC', u'NEXT_MKT_FLTNUM',
                   u'NEXT_SEG_DEPT_DATE', u'NEXT_SEG_ARR_DATE', 
                   u'RLOCATOR', u'TDIRECTION',
                   u'BKG_TYPE', u'PSEUDO_CITY_CODE',
                   u'ISO_COUNTRY', u'ISO_REGION', u'AGDUTY_CODE', u'REQUESTOR_ID',
                   u'SELL_CLS', u'CABIN', u'REFERENCE', u'YIELD', u'SRC_DATE']
    ndf['BASE_OD_DEPT_DATE'] = ndf['BASE_OD_DEPT_DATE'].astype(int)
    ndf['BASE_SEG_DEPT_DATE'] = ndf['BASE_SEG_DEPT_DATE'].astype(str)
    ndf['BASE_SEG_ARR_DATE'] = ndf['BASE_SEG_ARR_DATE'].astype(str)
    ndf['SRC_DATE'] = ndf['SRC_DATE'].astype(int)
    ndf['DAYSPRIOR'] = ndf['DAYSPRIOR'].astype(int)
    try:
        ndf['AGDUTY_CODE'] = ndf['AGDUTY_CODE'].astype(int)
    except:
        pass

    print('Cancelled bookings.')
    cdf = df.loc[df['SELL_CLS_CURR'].isnull()]
    cdf = cdf[[u'BASE_OD_ORGN_PREV', u'BASE_OD_DSTN_PREV',
               u'BASE_OD_VIA_PREV', u'BASE_OD_ORGN_COUNTRY_PREV',
               u'BASE_OD_ORGN_REGION_PREV', u'BASE_OD_DSTN_COUNTRY_PREV',
               u'BASE_OD_DSTN_REGION_PREV', u'BASE_OPR_CC_PREV',
               u'BASE_OPR_FLTNUM_PREV', u'BASE_MKT_CC_PREV', u'BASE_MKT_FLTNUM_PREV',
               u'BASE_OD_DEPT_DATE_PREV', u'DAYSPRIOR_PREV',
               u'BASE_SEG_DEPT_DATE_PREV', u'BASE_SEG_ARR_DATE_PREV', u'GEO_ORGN_PREV', u'GEO_DSTN_PREV',
               u'PREV_VIA_PREV', u'PREV_OPR_CC_PREV', u'PREV_OPR_FLTNUM_PREV',
               u'PREV_MKT_CC_PREV', u'PREV_MKT_FLTNUM_PREV',
               u'PREV_SEG_DEPT_DATE_PREV', u'PREV_SEG_ARR_DATE_PREV', u'NEXT_VIA_PREV', u'NEXT_OPR_CC_PREV',
               u'NEXT_OPR_FLTNUM_PREV', u'NEXT_MKT_CC_PREV', u'NEXT_MKT_FLTNUM_PREV',
               u'NEXT_SEG_DEPT_DATE_PREV', u'NEXT_SEG_ARR_DATE_PREV', 
               u'RLOCATOR_PREV', u'TDIRECTION_PREV',
               u'BKG_TYPE_PREV', u'PSEUDO_CITY_CODE_PREV',
               u'ISO_COUNTRY_PREV', u'ISO_REGION_PREV', u'AGDUTY_CODE_PREV', u'REQUESTOR_ID_PREV',
               u'SELL_CLS_PREV', u'CABIN_PREV', u'REFERENCE', u'YIELD_PREV', u'SRC_DATE_PREV']]
    cdf.columns = [u'BASE_OD_ORGN', u'BASE_OD_DSTN',
                   u'BASE_OD_VIA', u'BASE_OD_ORGN_COUNTRY',
                   u'BASE_OD_ORGN_REGION', u'BASE_OD_DSTN_COUNTRY',
                   u'BASE_OD_DSTN_REGION', u'BASE_OPR_CC',
                   u'BASE_OPR_FLTNUM', u'BASE_MKT_CC', u'BASE_MKT_FLTNUM',
                   u'BASE_OD_DEPT_DATE', u'DAYSPRIOR',
                   u'BASE_SEG_DEPT_DATE', u'BASE_SEG_ARR_DATE', u'GEO_ORGN', u'GEO_DSTN',
                   u'PREV_VIA', u'PREV_OPR_CC', u'PREV_OPR_FLTNUM',
                   u'PREV_MKT_CC', u'PREV_MKT_FLTNUM',
                   u'PREV_SEG_DEPT_DATE', u'PREV_SEG_ARR_DATE', u'NEXT_VIA', u'NEXT_OPR_CC',
                   u'NEXT_OPR_FLTNUM', u'NEXT_MKT_CC', u'NEXT_MKT_FLTNUM',
                   u'NEXT_SEG_DEPT_DATE', u'NEXT_SEG_ARR_DATE', 
                   u'RLOCATOR', u'TDIRECTION',
                   u'BKG_TYPE', u'PSEUDO_CITY_CODE',
                   u'ISO_COUNTRY', u'ISO_REGION', u'AGDUTY_CODE', u'REQUESTOR_ID',
                   u'SELL_CLS', u'CABIN', u'REFERENCE', u'YIELD', u'SRC_DATE']
    cdf['SRC_DATE'] = (pd.to_datetime(cdf['SRC_DATE'], format = '%Y%m%d') + pd.DateOffset(days = 1)).dt.strftime('%Y%m%d')
    cdf['BASE_OD_DEPT_DATE'] = cdf['BASE_OD_DEPT_DATE'].astype(int)
    cdf['BASE_SEG_DEPT_DATE'] = cdf['BASE_SEG_DEPT_DATE'].astype(str)
    cdf['BASE_SEG_ARR_DATE'] = cdf['BASE_SEG_ARR_DATE'].astype(str)
    cdf['SRC_DATE'] = cdf['SRC_DATE'].astype(int)
    cdf['DAYSPRIOR'] = cdf['DAYSPRIOR'].astype(int)
    try:
        cdf['AGDUTY_CODE'] = cdf['AGDUTY_CODE'].astype(int)
    except:
        pass

    print('Writing files...') 
    nfname_out = '/mnt/data/tmp/bkgd_' + prevdt + '_' + dt + '.csv'
    cfname_out = '/mnt/data/tmp/cnld_' + prevdt + '_' + dt + '.csv'
    ndf.to_csv(nfname_out, index = False)
    cdf.to_csv(cfname_out, index = False)
 
    print('Zipping files...')
    subprocess.check_output(['gzip', nfname_out])
    subprocess.check_output(['gzip', cfname_out])

    print('Copying files to s3...')
    subprocess.check_output(['aws','s3','cp',nfname_out+'.gz','s3://'+ncsv2check])
    subprocess.check_output(['aws','s3','cp',cfname_out+'.gz','s3://'+ccsv2check])

    print('Cleaning-up...')
    subprocess.check_output(['rm', nfname_out+'.gz'])
    subprocess.check_output(['rm', cfname_out+'.gz'])
    return 2


def process_non_parallel(dtstrs):
    num_cores = multiprocessing.cpu_count()
    results = Parallel(n_jobs = num_cores)(delayed(process)(dtstr) for dtstr in dtstrs)
    return sum(results)


def process_parallel(dtstrs):
    num = 0
    for dtstr in dtstrs:
        process(dtstr)
        num += 1
    return num


if __name__ == "__main__":
    dts = []
    dt = datetime.now() + timedelta(days = 1)
    for i in range(365):
        dts.append(datetime.strftime(dt,'%Y%m%d'))
        dt = dt - timedelta(days = 1)

    dt_b = datetime.now()
    num = process_parallel(dts)
    dt_e = datetime.now()

    seconds = int((dt_e - dt_b).seconds)
    hours = seconds / 3600
    minutes = (seconds - hours * 3600) / 60
    seconds = (seconds - hours * 3600 - minutes * 60)

    '''
    sbj = str(num) + ' bcd files have been processed.'
    body = 'Processed in ' + str(hours) + ' hours ' + str(minutes) + ' minutes ' + str(seconds) + ' seconds'
    send_quick('fedor.nikitin@finnair.com', 'fedor.nikitin@finnair.com', sbj, body)
    '''

