import csv
from datetime import datetime, timedelta
import pandas as pd
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_colwidth', 200)

fcstdt = datetime(2019,1,30)
fcstdate = datetime.strftime(fcstdt, '%Y%m%d')
fcstyear, fcstmonth, fcstday = str(fcstdt.year).zfill(2), str(fcstdt.month).zfill(2), str(fcstdt.day).zfill(2)


with open('brexit_Kalle.csv', 'w') as fout:
    cw = csv.writer(fout)
    cw.writerow(['DEPDT','REV','BREV','DIFF','DIFFPERC'])

    depdt = datetime(2019,3,29)
    for i in range(400):
        depdt = depdt + timedelta(days = 1)
        depdate = datetime.strftime(depdt, '%Y%m%d')
        df = pd.read_csv('s3://ay-rmp-home/nrm/cf/'+fcstyear+'/'+fcstmonth+'/'+fcstday+\
                                            '/cf_'+fcstdate+'_'+depdate+'.csv.gz', low_memory = False)
        df['REV'] = df['MP'] * df['LPC_D']
        bdf = pd.read_csv('s3://ay-rmp-home/nrm/04_5th_Kalle_cf/'+fcstyear+'/'+fcstmonth+'/'+fcstday+\
                                                    '/04_5th_Kalle_cf_'+fcstdate+'_'+depdate+'.csv.gz', low_memory = False)
        bdf['REV'] = bdf['MP'] * bdf['LPC_D']
    
        # Revenue wo brexit.
        rev = df['REV'].sum() 
    
        # Revenue with brexit (after re-optimization)
        brev = bdf['REV'].sum()
    
        # Difference of revenues.
        diff = rev - brev
    
        # Percentage of revenue. (loss due to brexit)
        perc = int(100 * diff / rev)
    
        row = [str(depdate), str(rev), str(brev), str(diff), str(perc)+'%']
        cw.writerow(row)
        print row



