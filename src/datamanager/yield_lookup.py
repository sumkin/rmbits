import pandas as pd
from datetime import datetime, timedelta
from time import sleep
import random

from airport_s3 import AirportS3


class YieldLookup:

    def __init__(self, dt):
        """
        datetime should be in format YYYYMMDD.
        """
        dtyear  = dt[:4]
        dtmonth = dt[4:6]
        dtday   = dt[6:8]

        # Read dataframes.
        NUM_TRIES = 3
        for i in range(NUM_TRIES):
            try:
                self.ydf = pd.read_csv('s3://ay-rmp-home/nrm/yield/'+dtyear+'/'+dtmonth+\
                                       '/YIELD_'+dt+'.csv.gz',
                                       usecols = ['TRVLFROM','TRVLTO',\
                                                  'ORGN','DSTN','POS','CLS','GBL_AM'])
                # Create key.
                self.ydf['KEY'] = self.ydf['ORGN'] +\
                                  self.ydf['DSTN'] +\
                                  self.ydf['POS'] +\
                                  self.ydf['CLS']  
                self.ydf['ORGN'] = self.ydf['ORGN'].astype('category')
                self.ydf['DSTN'] = self.ydf['DSTN'].astype('category')
                self.ydf['POS'] = self.ydf['POS'].astype('category')
                self.ydf['CLS'] = self.ydf['CLS'].astype('category')
                self.ydf['KEY'] = self.ydf['KEY'].astype('category')
                self.ydf.set_index(['KEY'])
                break
            except Exception as e:
                sleep(random.randint(0,5))
                if i == NUM_TRIES - 1:
                    raise e
        self.ydf = self.ydf.loc[(self.ydf['TRVLFROM'] <= int(dt)) & (int(dt) <= self.ydf['TRVLTO'])]

        for i in range(NUM_TRIES):
            try:
                self.gdf = pd.read_csv('s3://ay-rmp-home/static/geoset_mapping.csv', sep=';')
                break
            except Exception as e:
                if i == NUM_TRIES - 1:
                    raise e

        # Create cache.
        self.m = {}
        for k,r in self.ydf.iterrows():
            self.m[r['KEY']] = []
            dtfrom = datetime.strptime(str(r['TRVLFROM']), '%Y%m%d')
            dtto = datetime.strptime(str(r['TRVLTO']), '%Y%m%d')
            days = (dtto - dtfrom).days
            self.m[r['KEY']].append([float(r['GBL_AM']), str(r['TRVLFROM']), str(r['TRVLTO']), days])

        self.ap = AirportS3()
       

    def lookup(self,orgn,dstn,pos,cls):
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

        # Try geoset lookup.
        try:
            gpos = self.gdf.loc[self.gdf['COUNTRY'] == pos]['GEO_SET'].iloc[0]
            k = orgn+dstn+gpos+cls
            try:
                res, mindays = self.m[k][0][0], self.m[k][0][3]
                for e in self.m[k][1:]:
                    if e[3] < mindays:
                        res, mindays = e[0], e[3]
                return res
            except:
                pass
        except:
            pass

        # Try the same with ROW.
        k = orgn+dstn+'ROW'+cls
        try:
            res, mindays = self.m[k][0][0], self.m[k][0][3]
            for e in self.m[k][1:]:
                if e[3] < mindays:
                    res, mindays = e[0], e[3]
            return res
        except:
            pass

        orgn_country, orgn_region = self.ap.get_cr(orgn)
        dstn_country, dstn_region = self.ap.get_cr(dstn)

        # Lookup country to country.
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
                    print(orgn,dstn,pos,cls)
                    assert False


if __name__ == "__main__":
    yl = YieldLookup('20190404')
    p = yl.lookup('AMS','HEL','NL','Q')
    print('p = ', p)
    '''
    for i in range(100000):
        yl.lookup('CAN','LIS','CN','J')
    '''
 
