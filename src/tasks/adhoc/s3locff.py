import pandas as pd
from tqdm import tqdm

from ff_mapper import *

tqdm.pandas()

TST_FILE = 's3n://ay-rmp-home/nrm/baf/2018/05/AV_OD_20180523.csv.gz'

print 'Reading data frame from s3...'
df = pd.read_csv(TST_FILE)

print 'Adding class dimension...'
df2 = pd.melt(df, id_vars=['ORIG','DSTN','VIA','CC','FLTNUM',\
                           'OD_DEPT_DATE','OD_DEPT_DOW','SEG_DEPT_DATE',\
                           'POS','POSTYPE','LOCJ','LOCIJ','LOCY','LOCIY',\
                           'LOCJ_WOSC','LOCIJ_WOSC','LOCY_WOSC','LOCIY_WOSC',\
                           'SRC_DATE'], var_name='CLS', value_name='AVAIL')
del df
df3 = df2[['ORIG','DSTN','POS','CLS']]
df3 = df3.drop_duplicates()

print 'Creating ff mapper...'
print 'df3.shape = ', df3.shape
ffm = FFMapper(df3)

print 'before df2.shape = ', df2.shape
df2 = df2[df2.AVAIL != 0]

print 'after df2.shape = ', df2.shape

print 'Adding fare family column...'
df2['FF'] = df2.progress_apply(lambda x: ffm.get_ff(x['ORIG'],x['DSTN'],x['POS'],x['CLS']),axis=1)

 


