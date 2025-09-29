import csv
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

fcstdt = datetime(2019,2,25)
fcstdate = datetime.strftime(fcstdt, '%Y%m%d')
fcstyear, fcstmonth, fcstday = str(fcstdt.year).zfill(2), str(fcstdt.month).zfill(2), str(fcstdt.day).zfill(2)

prefix_w = 'au_50_cf'
prefix_wo = 'au_0_cf'
fname = 'au_sim'

with open(fname + '_od.csv', 'w') as fout:
    cw = csv.writer(fout)
    cw.writerow(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEPT_DATE','POS','LPC_D_DIFF','REV_DIFF'])

    dfwsum, dfwosum = None, None    
    depdt = datetime(2019,2,25)
    for i in range(357):
        depdate = datetime.strftime(depdt, '%Y%m%d')
        print 'depdate = ', depdate
        try:
            dfw = pd.read_csv('s3://ay-emr-job/nrm/'+prefix_w+'/'+fcstyear+'/'+fcstmonth+'/'+fcstday+\
                                                 '/'+prefix_w+'_'+fcstdate+'_'+depdate+'.csv.gz', low_memory = False)
            assert dfw[['MP','LPC_D']].isnull().sum().sum() == 0
            dfw['REV'] = dfw['MP'] * dfw['LPC_D']
            assert dfw[['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEPT_DATE','POS']].isnull().sum().sum() == 0
            assert dfw[['LPC_D','REV']].isnull().sum().sum() == 0
            dfw = dfw.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEPT_DATE','POS']).agg({'LPC_D': 'sum', 'REV': 'sum'}).reset_index()
            if dfwsum is None:
                dfwsum = dfw
            else:
                dfwsum = dfwsum.append(dfw)

            dfwo = pd.read_csv('s3://ay-emr-job/nrm/'+prefix_wo+'/'+fcstyear+'/'+fcstmonth+'/'+fcstday+\
                                                  '/'+prefix_wo+'_'+fcstdate+'_'+depdate+'.csv.gz', low_memory = False)
            assert dfwo[['MP','LPC_D']].isnull().sum().sum() == 0
            dfwo['REV'] = dfwo['MP'] * dfwo['LPC_D']
            assert dfwo[['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEPT_DATE','POS']].isnull().sum().sum() == 0
            assert dfwo[['LPC_D','REV']].isnull().sum().sum() == 0
            dfwo = dfwo.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEPT_DATE','POS']).agg({'LPC_D': 'sum', 'REV': 'sum'}).reset_index()
            if dfwosum is None:
                dfwosum = dfwo
            else:
                dfwosum = dfwosum.append(dfwo)
        except Exception as e:
            print e
            pass
        depdt = depdt + timedelta(days = 1)
    
    print 'dfwsum.shape = ', dfwsum.shape
    print 'dfwosum.shape = ', dfwosum.shape
    assert dfwsum[['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEPT_DATE','POS']].isnull().sum().sum() == 0
    assert dfwsum[['LPC_D','REV']].isnull().sum().sum() == 0
    assert dfwosum[['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEPT_DATE','POS']].isnull().sum().sum() == 0
    assert dfwosum[['LPC_D','REV']].isnull().sum().sum() == 0 
    dfwsum = dfwsum.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEPT_DATE','POS']).agg({'LPC_D': 'sum', 'REV': 'sum'}).reset_index()
    dfwosum = dfwosum.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEPT_DATE','POS']).agg({'LPC_D': 'sum', 'REV': 'sum'}).reset_index()
    df = dfwsum.merge(dfwosum, on = ['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEPT_DATE','POS'], how = 'inner', suffixes = ('_w','_wo'))
    df['LPC_D_w'] = df['LPC_D_w'].replace(np.nan, 0.0)
    df['LPC_D_wo'] = df['LPC_D_wo'].replace(np.nan, 0.0)
    df['REV_w'] = df['REV_w'].replace(np.nan, 0.0)
    df['REV_wo'] = df['REV_wo'].replace(np.nan, 0.0)
    df['LPC_D_DIFF'] = df['LPC_D_w'] - df['LPC_D_wo']
    df['REV_DIFF'] = df['REV_w'] - df['REV_wo']
    print 'df.shape = ', df.shape
    
    df = df.sort_values(by = ['REV_DIFF'], ascending = False)
    for i, r in df.iterrows():
        row = [r['BASE_OD_ORGN'],r['BASE_OD_DSTN'],r['BASE_OD_DEPT_DATE'],r['POS'],r['LPC_D_DIFF'],r['REV_DIFF']]
        cw.writerow(row)








