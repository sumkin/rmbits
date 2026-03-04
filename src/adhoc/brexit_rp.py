import os
import csv
from datetime import datetime, timedelta
import pandas as pd
from joblib import Parallel, delayed

fname = 'rp.csv'

num = 1
with open(fname, 'w') as fout:
    csvw = csv.writer(fout)
    csvw.writerow(['CC','FLTNUM','DEPDT','MONTH','MARGINAL','MARGINAL_BREXIT'])
    dt = datetime(2019,3,30)
    while dt <= datetime(2020,1,13):
        depdt = dt.strftime('%Y%m%d')
        print 'depdt = ', depdt
        path  = 's3://ay-rmp-home/nrm/cf/2019/01/22/cf_sar_rows_20190122_' + depdt + '.csv.gz'
        bpath = 's3://ay-rmp-home/nrm/brexit_cf/2019/01/22/br_cf_sar_rows_20190122_' + depdt + '.csv.gz'

        df = pd.read_csv(path, low_memory = False)       
        df['MARGINAL'].replace('.', '0.0', inplace = True)
        df['MARGINAL'] = df['MARGINAL'].astype(float)
        df = df[['VARNAME','MARGINAL']]

        bdf = pd.read_csv(bpath, low_memory = False)
        bdf['MARGINAL'].replace('.', '0.0', inplace = True)
        bdf['MARGINAL'] = bdf['MARGINAL'].astype(float)
        bdf = bdf[['VARNAME','MARGINAL']]

        fdf = df.merge(bdf, on = ['VARNAME'], suffixes = ['_o','_b'])
        for i,r in fdf.iterrows():
            varname = r['VARNAME']
            m_o = r['MARGINAL_o']
            m_b = r['MARGINAL_b']

            cc = varname[:2]
            fltnum = varname[2:6]
            depdt = varname[7:15]
            month = depdt[:6]
            m_o = float(m_o)
            m_b = float(m_b)
            num += 1
            csvw.writerow([cc,fltnum,depdt,month,m_o,m_b])
        dt = dt + timedelta(days = 1)

print 'num = ', num

