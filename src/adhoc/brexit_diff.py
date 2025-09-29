import csv
import subprocess
from datetime import datetime, timedelta
import pandas as pd

from s3utils import *


pd.set_option('display.max_columns', 500)
pd.set_option('display.max_colwidth', 200)

fcstdt = datetime(2019,1,18)
fcstdate = datetime.strftime(fcstdt, '%Y%m%d')
fcstyear, fcstmonth, fcstday = str(fcstdt.year).zfill(2), str(fcstdt.month).zfill(2), str(fcstdt.day).zfill(2)

depdt = datetime(2019,3,29)
for i in range(400):
    depdt = depdt + timedelta(days = 1)
    depdate = datetime.strftime(depdt, '%Y%m%d')
    print 'depdate = ', depdate
    df = pd.read_csv('s3://ay-emr-job/nrm/cf/'+fcstyear+'/'+fcstmonth+'/'+fcstday+\
                                         '/cf_'+fcstdate+'_'+depdate+'.csv.gz', low_memory = False)
    df['REV'] = df['MP'] * df['LPC_D']
    bdf = pd.read_csv('s3://ay-emr-job/nrm/brexit_cf/'+fcstyear+'/'+fcstmonth+'/'+fcstday+\
                                         '/brexit_cf_'+fcstdate+'_'+depdate+'.csv.gz', low_memory = False)
    bdf['REV'] = bdf['MP'] * bdf['LPC_D']
    mdf = bdf.merge(df, left_on = ['GEO_OD_TS_KEY','POS','FF','BC','TP'],\
                        right_on = ['GEO_OD_TS_KEY','POS','FF','BC','TP'],\
                        suffixes = ('_b','_wob'),\
                        how = 'left')
    mdf['LPC_DIFF'] = mdf['LPC_D_b'] - mdf['LPC_D_wob']
    mdf = mdf.sort_values(by = ['LPC_DIFF'], ascending = False)
   
    fname_out = '/home/ay49514/tmp/br_diff_cf_'+fcstdate+'_'+depdate+'.csv'
    csvout = 'ay-emr-job/nrm/brexit_diff_cf/' + fcstdate[:4]  +\
                                          '/' + fcstdate[4:6] +\
                                          '/' + fcstdate[6:8] +\
                                          '/br_diff_cf_' + fcstdate + '_' + depdate + '.csv.gz' 
    mdf.to_csv(fname_out)
    subprocess.check_output(['gzip', fname_out])
    subprocess.check_output(['aws','s3','cp',fname_out+'.gz','s3://'+csvout])
    subprocess.check_output(['rm',fname_out+'.gz'])



