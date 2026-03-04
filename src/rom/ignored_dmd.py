import csv
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from joblib import Parallel, delayed
import multiprocessing
from threading import Lock

from dfutils import *


def ignored_demand_check(fcstdate, depdate):
    next_depdate = datetime.strftime(datetime.strptime(depdate, '%Y%m%d') + timedelta(days = 1), '%Y%m%d')
    fcstyear, fcstmonth, fcstday = fcstdate[:4], fcstdate[4:6], fcstdate[6:8]

    # Read demand curve data frame.
    dccsv = 's3://ay-rmp-home/nrm/fdc/' + fcstyear + '/' + fcstmonth + '/' + fcstday +\
                                   '/fdc_' + fcstdate + '_' + depdate + '.csv.gz'  
    dcdf = pd.read_csv(dccsv, low_memory = False).fillna('')
    dcdf['SREV'] = dcdf['SMPWA'] * dcdf['SFD']
    dcdf['AREV'] = dcdf['AMPWA'] * dcdf['AFD']

    # Read inventory data frame.
    next_depdt = datetime.strftime(datetime.strptime(depdate, '%Y%m%d') + timedelta(days = 1), '%Y%m%d')
    invcsv = 's3://ay-rmp-home/nrm/bif/' + fcstyear + '/' + fcstmonth + '/INV_' + fcstdate + '.csv.gz'
    invdf = pd.read_csv(invcsv, low_memory = False).fillna('')
    invdf = invdf.loc[(invdf['DEPDT'] == int(depdate)) | (invdf['DEPDT'] == int(next_depdate))]
    invdf = invdf.loc[(invdf['ORGN'] == 'HEL') | (invdf['DSTN'] == 'HEL')]
    invdf = invdf.loc[(invdf['CABIN'] == 'J') | (invdf['CABIN'] == 'Y')]
    invdf = invdf.loc[(invdf['CAPO'] < 900)]
    invdf = optimize_bif(invdf)

    sd,sdi = 0.0,0.0
    ad,adi = 0.0,0.0
    srev,srevi = 0.0,0.0
    arev,arevi = 0.0,0.0

    sd = dcdf['SFD'].sum()
    ad = dcdf['AFD'].sum()
    srev = dcdf['SREV'].sum()
    arev = dcdf['AREV'].sum()

    '''
    Filter out flows with origin in HEL. 
    They can't be ignored.
    '''         
    df = dcdf.loc[(dcdf['BASE_OD_ORGN'] != 'HEL')]
    df = df[['BASE_SEG_DEP_DATE','BASE_OPR_CC','BASE_OPR_FLTNUM','SFD','AFD','SREV','AREV']]

    for k,r in df.iterrows():
        if k % 10000 == 0:
            print('k = ', k) 
        base_seg_dep_dates = str(r['BASE_SEG_DEP_DATE']).split('-')
        oprccs,oprfltnums = str(r['BASE_OPR_CC']).split('-'), str(r['BASE_OPR_FLTNUM']).split('-')
        if oprfltnums[0] == 'nan':
            continue
          
        ignored = False 
        assert len(oprfltnums) > 0
        assert len(oprfltnums) < 3
        assert len(base_seg_dep_dates) > 0
        assert len(base_seg_dep_dates) < 3
        if len(oprfltnums) == 2:
            if int(base_seg_dep_dates[1]) == int(next_depdate):
                try:
                    deptm = invdf[(invdf['FLTNUM'] == int(oprfltnums[1])) &\
                                   (invdf['DEPDT'] == int(next_depdate))].iloc[0]['DEPTM']    
                    if deptm > 300:
                        ignored = True 
                except:
                    ignored = True
            elif int(base_seg_dep_dates[1]) != int(depdate):
                ignored = True

        if ignored:
            sdi += r['SFD']
            adi += r['AFD']
            srevi += r['SREV']
            arevi += r['AREV']
  
    return sd,ad,sdi,adi,srev,arev,srevi,arevi


def process(fcstdate, depdate):
    try:
        sd,ad,sdi,adi,srev,arev,srevi,arevi = ignored_demand_check(fcstdate, depdate)
        return [fcstdate,depdate,sd,ad,sdi,adi,srev,arev,srevi,arevi]
    except Exception as e:
        print('e = ', e)
        return None


def process_parallel(fcstdate, depdates, writer):
    num_cores = multiprocessing.cpu_count()
    results = Parallel(n_jobs = num_cores)(delayed(process)(fcstdate, depdate) for depdate in depdates)
    for result in results:
        if result is not None:
            writer.writerow(result)
    return len(results)


def process_non_parallel(fcstdate, depdates, writer):
    num = 0
    for depdate in depdates:
        process(fcstdate, depdate, writer)
        num += 1
    return num


if __name__ == "__main__":
    fcstdate = '20191205'
    with open('ignored_dmd.csv', 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['FCSTDATE','DEPDATE','SD','AD','SDI','ADI','SREV','AREV','SREVI','AREVI'])

        depdates = []
        depdate = fcstdate
        for i in range(360):
            depdates.append(depdate)
            depdate = datetime.strftime(datetime.strptime(depdate,'%Y%m%d') + timedelta(days=1),'%Y%m%d')

        process_parallel(fcstdate, depdates, writer)


