import csv
from datetime import datetime, timedelta
import pandas as pd
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_colwidth', 200)

fcstdt = datetime(2019,5,19)
fcstdate = datetime.strftime(fcstdt, '%Y%m%d')
fcstyear, fcstmonth, fcstday = str(fcstdt.year).zfill(2), str(fcstdt.month).zfill(2), str(fcstdt.day).zfill(2)

fname = 'XIA_CKG_C'
prefix_w = 'XIA_CKG_C_cf'
prefix_wo = 'XIA_CKG_cf'

with open(fname + '_sim.csv', 'w') as fout:
    cw = csv.writer(fout)
    cw.writerow(['DEPDT','DMDW','DMDWO','DDIFF','REVW','REVWO','RDIFF','RDIFFPERC'])

    depdt = datetime(2019,5,19)
    for i in range(357):
        depdate = datetime.strftime(depdt, '%Y%m%d')
        try:
            dfw = pd.read_csv('s3://ay-emr-job/nrm/'+prefix_w+'/'+fcstyear+'/'+fcstmonth+'/'+fcstday+\
                                                 '/'+prefix_w+'_'+fcstdate+'_'+depdate+'.csv.gz', low_memory = False)
            assert dfw[['MP','LPC_D']].isnull().sum().sum() == 0
            dfw['REV'] = dfw['MP'] * dfw['LPC_D']

            dfwo = pd.read_csv('s3://ay-emr-job/nrm/'+prefix_wo+'/'+fcstyear+'/'+fcstmonth+'/'+fcstday+\
                                                  '/'+prefix_wo+'_'+fcstdate+'_'+depdate+'.csv.gz', low_memory = False)
            assert dfwo[['MP','LPC_D']].isnull().sum().sum() == 0
            dfwo['REV'] = dfwo['MP'] * dfwo['LPC_D']

            # Demand wo simulation.
            dmdwo = dfwo['LPC_D'].sum()

            # Demand with simulation (after re-optimization).
            dmdw = dfw['LPC_D'].sum()

            # Difference of demand.
            ddiff = dmdw - dmdwo
    
            # Revenue wo simulation.
            revwo = dfwo['REV'].sum() 
    
            # Revenue with simulation (after re-optimization).
            revw = dfw['REV'].sum()
    
            # Difference of revenues.
            rdiff = revw - revwo
    
            # Percentage of revenue. (loss due to brexit).
            perc = float(100 * rdiff / revwo)
    
            row = [str(depdate), str(dmdw), str(dmdwo), str(ddiff), str(revw), str(revwo), str(rdiff), str(perc)]
            cw.writerow(row)
            prin row
        except Exception as e:
            print e
            pass
        depdt = depdt + timedelta(days = 1)
       



