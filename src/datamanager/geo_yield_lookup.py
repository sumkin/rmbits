import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from airport_s3 import *
#from emailutils import *


class GeoYieldLookup:


    def __init__(self, dt):
        '''
        datetime should be in format YYYYMMDD.
        '''
        dtyear  = dt[:4]
        dtmonth = dt[4:6]
        dtday   = dt[6:8]

        # Read yield dataframe.
        print('Reading yield dataframe...')
        self.ydf = pd.read_csv('s3://ay-rmp-home/nrm/yield/'+dtyear+'/'+dtmonth+\
                                                        '/YIELD_'+dt+'.csv.gz').fillna('')
        self.ydf = self.ydf.loc[(self.ydf['TRVLFROM'] <= int(dt)) & (int(dt) <= self.ydf['TRVLTO'])]

        # Read geo dataframe.
        print('Reading geo dataframe...')
        self.geodf = pd.read_csv('s3://ay-rmp-home/static/geoset_mapping.csv', delimiter=';', low_memory = False)

        self.geoydf = self.ydf.merge(self.geodf, left_on = ['POS'], right_on = ['GEO_SET'], how = 'left')

        # Create key.
        print('Creating key...')
        self.geoydf['KEY'] = self.geoydf['ORGN'] +\
                             self.geoydf['DSTN'] +\
                             self.geoydf['GEO_SET'] +\
                             self.geoydf['CLS']  
        self.geoydf['KEY'] = self.geoydf['KEY'].astype('category')
        self.geoydf.set_index(['KEY'])

        # Create cache.
        print('Creating cache...')
        self.m = {}
        nrows,ncols = self.geoydf.shape
        num = 0
        for k,r in self.geoydf.iterrows():
            num += 1
            self.m[r['KEY']] = []
            dtfrom = datetime.strptime(str(r['TRVLFROM']), '%Y%m%d')
            dtto = datetime.strptime(str(r['TRVLTO']), '%Y%m%d')
            days = (dtto - dtfrom).days
            self.m[r['KEY']].append([float(r['GBL_AM']), str(r['TRVLFROM']), str(r['TRVLTO']), days])
            if num % 100000 == 0:
                print(num, '/', nrows, int((100 * num) / nrows), '%')

        self.ap = AirportS3()
        print('Cache created.')       


    def lookup(self, orgn, dstn, pos, cls):
        if pos == 'FI' or pos == 'ROW':
            pass
        else:
            try:
                pos = self.geodf.loc[self.geodf['COUNTRY'] == pos]['GEO_SET'].iloc[0]
            except:
                try:
                    pos = self.geodf.loc[self.geodf['COUNTRY'] == 'ROW']['GEO_SET'].iloc[0]
                except Exception as e:
                    print('pos = ', pos, e)
                    #send_error('geo_yield_lookup.lookup()', 'pos did not found in geo set')
        
        # Check cache.
        k = orgn+dstn+pos+cls
        try:
            res, mindays = self.m[k][0][0], self.m[k][0][3]
            for e in self.m[k][1:]:
                if e[3] < mindays:
                    res, mindays = e[0], e[3]
            return res
        except:
            pass

        # Lookup country to country.
        orgn_country, orgn_region = self.ap.get_cr(orgn)
        dstn_country, dstn_region = self.ap.get_cr(dstn) 

        k = orgn_country+dstn_country+'ROW'+cls
        try:
            res, mindays = self.m[k][0][0], self.m[k][0][3]
            for e in self.m[k][1:]:
                if e[3] < mindays:
                    res, mindays = e[0], e[3]
            return res
        except:
            pass

        # Lookup region to region.
        k = orgn_region+dstn_region+'ROW'+cls
        try:
            res, mindays = self.m[k][0][0], self.m[k][0][3]
            for e in self.m[k][1:]:
                if e[3] < mindays:
                    res, mindays = e[0], e[3]
            return res
        except:
            if orgn_region == 'MEAST' and dstn_region == 'ASIA':
                orgn_region = 'EUROP'
                try:
                    k = orgn_region+dstn_region+'ROW'+cls
                    res, mindays = self.m[k][0][0], self.m[k][0][3]
                    for e in self.m[k][1:]:
                        if e[3] < mindays:
                            res, mindays = e[0], e[3]
                    return res
                except:
                    pass 

        try:
            pass
            #send_error('geo_yield_lookup.lookup()', k+' entry was not found in cache; orgn,dstn,pos,cls = '+orgn+','+dstn+',' +pos+','+cls)
        except Exception as e:
            print('Porblem with sending email.')
            print(e)
        return np.nan

 
if __name__ == "__main__":
    gyl = GeoYieldLookup('20190404')
    for i in range(1):
        res = gyl.lookup('BKK','SIN','#1EURSOUTH','Y')
        print('res = ', res)
 
