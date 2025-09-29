import csv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from threading import Lock
from time import sleep

from defs import *
from db_connector import *
from bffreader2 import *
from yieldlookuploader import *


mutex = Lock()


class McFlyReader:
    '''
    Reads files from s3 bucket and
    produces McFly data.
    '''

    #@profile
    def __init__(self, srcdate, depdate, bkgdate, srcyl):
        self.srcdate = srcdate
        self.depdate = depdate
        self.bkgdate = bkgdate

        depdately = datetime.strptime(self.depdate, '%Y%m%d') - timedelta(days = 364)
        self.depdately = datetime.strftime(depdately, '%Y%m%d')

        bkgdately = datetime.strptime(bkgdate, '%Y%m%d') - timedelta(days = 364)
        self.bkgdately = datetime.strftime(bkgdately, '%Y%m%d')

        # Yield lookups.
        self.yl = srcyl
        self.ylly = YieldLookupLoader(self.bkgdately).get()


    #@profile
    def project(self, clss, rds, ylds, yld):
        '''
        Given demand curve method finds 
        demand corresponding to provided 
        yield.
        '''
        n = len(rds)
        assert len(ylds) == n

        for i in range(n):
            if yld >= ylds[i]:
                break

        if i == 0:
            # yld is higher than all other yields.
            y0 = ylds[0]
            y1 = ylds[0]
            d0 = rds[0]
            d1 = d0
            for i in range(1,len(ylds)):
                if abs(ylds[i] - y0) > EPS:
                    y1 = ylds[i]
                    d1 += rds[i]
                    break
                d1 += rds[i]
            assert abs(y0 - y1) > EPS
            return max(0,d0 - ((yld - y0)/(y0 - y1)) * (d1 - d0))
        elif i == n - 1:
            # yld is lower than all other yields.
            yn1 = ylds[n-1]
            dn1 = sum(rds[:n])
            yn2 = ylds[n-2]
            dn2 = sum(rds[:n-1])
            for i in range(n-1,0,-1):
                if abs(ylds[i] - yn1) > EPS:
                    yn2 = ylds[i]
                    dn2 = sum(rds[:i])
            return max(0,dn2 + ((yn2 - yld)/(yn1 - yn2)) * (dn2 - dn1))
        else:
            # yld is between. ylds[i] >= yld >= ylds[i-1].     
            y0,y1 = ylds[i],ylds[i-1]
            d0,d1 = sum(rds[:i+1]),sum(rds[:i])
            return max(0,d0 + ((y0 - yld)/(y0 - y1)) * (d1 - d0))


    #@profile
    def read_dfs(self):   
        NUM_TRIES = 10
        for i in range(NUM_TRIES):
            try:
                # Forecast data frame.
                self.fdf = pd.read_csv('s3://ay-emr-job/nrm/fullbff/' +\
                                       self.srcdate[:4] + '/' + self.srcdate[4:6] + '/' + self.srcdate[6:8] + '/' +\
                                       'FCST_' + self.srcdate + '_' + self.depdate + '_' + self.bkgdate + '.csv.gz',\
                                       usecols = ['GEO_OD_TS_KEY',\
                                                  'BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEP_DATE',\
                                                  'GEO_ORGN','GEO_DSTN',\
                                                  'POS','BC','FF',\
                                                  'SMP','AMP','SRD','ARD','SGCD','AGCD'],\
                                       dtype = {'GEO_OD_TS_KEY': 'category',\
                                                'BASE_OD_ORGN': 'category',\
                                                'BASE_OD_DSTN': 'category',\
                                                'BASE_OD_DEP_DATE': 'category',\
                                                'GEO_ORGN': 'category',\
                                                'GEO_DSTN': 'category',\
                                                'POS': 'category',\
                                                'BC': 'category',\
                                                'FF': 'category'}) 
                break
            except Exception as e:
                print(e)
                sleep(3)
        self.fdf = self.fdf.replace(np.nan, '')
        self.df = self.fdf.groupby(['GEO_OD_TS_KEY',\
                                    'BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEP_DATE',\
                                    'GEO_ORGN','GEO_DSTN',\
                                    'POS','BC','FF']).agg({'SMP': 'mean',\
                                                           'AMP': 'mean',\
                                                           'SRD': 'sum',\
                                                           'ARD': 'sum',\
                                                           'SGCD': 'sum',\
                                                           'AGCD': 'sum'}).reset_index()

        # Class data frame.
        clsdf = pd.read_csv('s3://ay-emr-job/static/clsorder.csv')

        # Merge class order data frame to forecast data frame.
        self.df = self.df.merge(clsdf, left_on = ['BC'], right_on = ['CLS'], how = 'left')

        # Merge generic fare family.
        for i in range(NUM_TRIES):
            try:
                mutex.acquire()
                DBConnector.pr_conn()
                ffdf = pr.redshift_to_pandas("SELECT * FROM nrm_report.d_ff")
                pr.close_up_shop()
                mutex.release()
                break
            except Exception as e:
                print(e)
                sleep(1)

        self.df = self.df.merge(ffdf, left_on = ['FF'], right_on = ['fare_family'], how = 'left')

        # Read selling class table.
        for i in range(NUM_TRIES):
            try:
                mutex.acquire()
                DBConnector.pr_conn()
                self.scdf = pr.redshift_to_pandas("SELECT geo_od_ts_key, pos, generic_fare_family,\
                                                          selling_class, selling_class_index\
                                                   FROM nrm_report.nrm_loc_row_hist_sfd\
                                                   WHERE base_od_dept_date = '" + self.depdately + "' AND\
                                                         source_file_date = '" + self.bkgdately + "'")
                pr.close_up_shop()
                mutex.release()
                break
            except Exception as e:
                print(e)
                sleep(1)

        self.scdf = self.scdf.drop_duplicates(subset = ['geo_od_ts_key','pos','generic_fare_family'])
        # Sort data frame.       
        self.df = self.df.sort_values(by = ['GEO_OD_TS_KEY','POS','generic_fare_family','ORDER'])

        self.df = self.df[['GEO_OD_TS_KEY',\
                           'BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEP_DATE',\
                           'GEO_ORGN','GEO_DSTN',\
                           'POS','FF','generic_fare_family','BC',\
                           'SMP','AMP','SRD','ARD','SGCD','AGCD']]
        self.df['GEO_OD_TS_KEY_PREV_YEAR'] = self.df['GEO_OD_TS_KEY']\
            .apply(BFFReader2.convert_geo_od_ts_key_prev_year)
        self.df = self.df.merge(self.scdf, left_on = ['GEO_OD_TS_KEY_PREV_YEAR','POS','generic_fare_family'],\
                                           right_on = ['geo_od_ts_key','pos','generic_fare_family'], how = 'left')
        self.df = self.df.replace(np.nan, '')


    #@profile
    def rows(self):     
        smps,amps = [],[]
        srds,ards = [],[]
        sgcds,agcds = [],[]
        clss = []
        yields = []

        prev_r = None
        prev_geo_od_ts_key = None
        prev_pos = None
        prev_ff = None
        for k,r in self.df.iterrows():
            geo_od_ts_key = r['GEO_OD_TS_KEY']
            pos = r['POS']
            ff = r['generic_fare_family']
            if prev_geo_od_ts_key == geo_od_ts_key and\
               prev_pos == pos and\
               prev_ff == ff:
                # Fare family continues.
                smps.append(r['SMP'])
                amps.append(r['AMP'])
                srds.append(r['SRD'])
                ards.append(r['ARD'])
                sgcds.append(r['SGCD'])
                agcds.append(r['AGCD'])
                clss.append(r['BC'])
                yields.append(self.yl.lookup(r['BASE_OD_ORGN'],r['BASE_OD_DSTN'],r['POS'],r['BC']))
            else:
                # New fare family. 
                n = len(smps)
                assert n == len(amps)
                assert n == len(srds)
                assert n == len(ards)
                assert n == len(clss)
                assert n == len(sgcds)
                assert n == len(agcds)

                if n > 1 and prev_r['FF'] != np.nan and prev_r['FF'] != '': # Ignore isolated classes.
                    sgccy,agccy = None,None # Going class current year.
                    sgcd,agcd = 0,0                    

                    scly = None
                    if prev_r['selling_class'] != '':
                        scly = prev_r['selling_class']

                    sclyi = None
                    if prev_r['selling_class_index'] != '':
                        sclyi = prev_r['selling_class_index']

                    for i in range(n):
                        if smps[i] >= 0:
                            sgccy = clss[i]
                            sgcd += srds[i]
                        if amps[i] >= 0:
                            agccy = clss[i]
                            agcd += ards[i]
                    
                    scyieldly = None
                    mcflysd,mcflyad = None,None
                    lyscfound = False

                    if sclyi is None:
                        # No fare family last yer.
                        mcflysd = sgcd
                        mcflyad = agcd
                    elif sclyi == 0:
                        # Fare family existed, but was closed.
                        mcflysd = None
                        mcflyad = None
                        lyscfound = True
                    else: 
                        lyscfound = True
                        # Last year selling class yield.
                        scyieldly = self.ylly.lookup(prev_r['BASE_OD_ORGN'],prev_r['BASE_OD_DSTN'],prev_r['POS'],scly)
                        if scyieldly is not None:
                            if None not in yields:
                                # McFly system demand.
                                mcflysd = self.project(clss, srds, yields, scyieldly)
                                # McFly adjusted demand.
                                mcflyad = self.project(clss, ards, yields, scyieldly)

                    sgcyield = None
                    if sgccy is not None:
                        # System going class yield.
                        sgcyield = self.yl.lookup(prev_r['BASE_OD_ORGN'],prev_r['BASE_OD_DSTN'],prev_r['POS'],sgccy)
         
                    agcyield = None
                    if agccy is not None:
                        # Adjusted going class yield.
                        agcyield = self.yl.lookup(prev_r['BASE_OD_ORGN'],prev_r['BASE_OD_DSTN'],prev_r['POS'],agccy)

                    opr_od_ts_key = BFFReader2.convert_geo_od_ts_key_2_opr_od_ts_key(prev_r['GEO_OD_TS_KEY'])
                    
                    yield [opr_od_ts_key, prev_r['GEO_OD_TS_KEY'],\
                           prev_r['BASE_OD_ORGN'], prev_r['BASE_OD_DSTN'], prev_r['BASE_OD_DEP_DATE'],\
                           prev_r['GEO_ORGN'], prev_r['GEO_DSTN'],\
                           prev_r['POS'], prev_r['FF'], self.bkgdate,\
                           scyieldly, mcflysd, mcflyad, sgcyield, agcyield,\
                           sgcd, agcd, lyscfound]      

                # Start over.
                smps = [r['SMP']]
                amps = [r['AMP']]
                srds = [r['SRD']]
                ards = [r['ARD']]
                sgcds = [r['SGCD']]
                agcds = [r['AGCD']]
                clss = [r['BC']]
                yields = [self.yl.lookup(r['BASE_OD_ORGN'],r['BASE_OD_DSTN'],r['POS'],r['BC'])]

            prev_r = r
            prev_geo_od_ts_key = geo_od_ts_key
            prev_pos = pos
            prev_ff = ff
 


if __name__ == "__main__":
    srcdate = '20200127'
    depdate = '20201231'
    bkgdate = '20201230'
    srcyl = YieldLookupLoader(srcdate).get()
    mcfly = McFlyReader(srcdate,depdate,bkgdate,srcyl)
    print('McFlyReader initialized.')
    mcfly.read_dfs()
    print('Data frames read')

    num = 0
    for r in mcfly.rows():
        num += 1
        if num % 10000 == 0:
            print('num = ', num)


        

  
