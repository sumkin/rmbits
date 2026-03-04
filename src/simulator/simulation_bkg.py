import csv
import pandas as pd
from datetime import datetime, timedelta

df = None
dt = datetime.now()
for i in range(365):
    dt = dt - timedelta(days = 1)
    dts = datetime.strftime(dt, '%Y%m%d')
    try:
        bdf = pd.read_csv('s3://ay-rmp-home/nrm/bof/' + dts[:4] + '/' + dts[4:6] +\
                                                 '/BKG_OD_' + dts +'.csv.gz', low_memory = False)
    except:
        break
    bdf = bdf.loc[bdf['BASE_OD_DEPT_DATE'] == int(dts)]
    bdf = bdf.groupby(by = ['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEPT_DATE','ISO_COUNTRY'])\
             .agg({'REFERENCE': 'count'}).reset_index()
    if df is None:
        df = bdf
    else:
        df = df.append(bdf)
    print dts

print 'Writing csv...'
fname = 'au_bkg.csv'
with open(fname, 'w') as fout:
    cw = csv.writer(fout)
    cw.writerow(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEPT_DATE','ISO_COUNTRY','NUM'])
    for i,r in df.iterrows():
        cw.writerow([r['BASE_OD_ORGN'],r['BASE_OD_DSTN'],r['BASE_OD_DEPT_DATE'],r['ISO_COUNTRY'],r['REFERENCE']])




        
