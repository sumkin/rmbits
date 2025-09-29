import numpy as np
import pandas as pd
from tqdm import tqdm

from ff_mapper import *
from s3utils import *

print 'Getiing last av file...'
av_file = s3getlastavfile()
print 'Last av file is ', av_file

print 'Reading data from s3...'
df = pd.read_csv('s3n://' + av_file, low_memory = False)

print 'Melting dataframe with class dimension...'
df = pd.melt(df, id_vars=['ORGN','DSTN','VIA','CC','FLTNUM',\
                          'OD_DEPT_DATE','OD_DEPT_DOW','SEG_DEPT_DATE',\
                          'POS','POSTYPE','LOCJ','LOCIJ','LOCY','LOCIY',\
                          'LOCJ_WOSC','LOCIJ_WOSC','LOCY_WOSC','LOCIY_WOSC',\
                          'SRC_DATE'], var_name='CLS', value_name='AVAIL')

print 'Selecting ORGN,DSTN,POS,CLS...'
df = df[['ORGN','DSTN','POS','CLS']]

print 'Dropping duplicates...'
df = df.drop_duplicates()

print 'Creating ff mapper...'
print 'df.shape = ', df.shape
ffm = FFMapper(df)

print 'Calculating ff mapper...'
df['FF'] = df.progress_apply(lambda x: ffm.get_ff(x['ORGN'],x['DSTN'],x['POS'],x['CLS']), axis=1)

csvfname = 'FF_MAP_'
csvfname += av_file.rsplit('/',1)[1].split('.')[0].split('_')[2]
csvfname += '.csv'

df.to_csv(csvfname, index=False)


