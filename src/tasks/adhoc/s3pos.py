import pandas as pd
from datetime import datetime
from pos import *

df = POS.get_fcst_all()

csvfname = 'POS_' + datetime.strftime(datetime.now(),'%Y%m%d') + '.csv'
df.to_csv(csvfname)


