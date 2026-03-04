import pandas as pd

from s3utils import *

fcstdate  = '20180911'
fcstyear  = fcstdate[:4]
fcstmonth = fcstdate[4:6]
fcstday   = fcstdate[6:8]

fnames = gets3files('ay-rmp-home/nrm/cf/'+fcstyear+'/'+fcstmonth+'/'+fcstday+'/')
for fname in fnames:
    print 'fname = ', fname
    df = pd.read_csv('s3://ay-rmp-home/'+fname)
    df['REV'] = df['MP'].astype(float) * df['AMD'].astype(float)
    df['CREV'] = df['MP'].astype(float) * df['CAMD'].astype(float)
    print df['AMD'].sum(), df['CAMD'].sum(), df['REV'].sum(), df['CREV'].sum()


