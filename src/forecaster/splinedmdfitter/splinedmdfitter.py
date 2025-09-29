import numpy as np
import pandas as pd
from time import sleep
from scipy.interpolate import interp1d

from defs import *
#from yield_lookup import *


class SplineDmdFitter:


    def __init__(self, srcdate, depdate):
        self.srcdate = srcdate
        self.depdate = depdate
        #self.yl = YieldLookup(self.srcdate)


    @staticmethod
    def fit(ps, Ds):
        fps = []
        fDs = []
        for i in range(len(ps)):
            if abs(Ds[i]) > EPS:
                fps.append(ps[i])
                fDs.append(Ds[i])
        assert len(fps) == len(fDs)
        interp1d_f = interp1d(ps, Ds, kind = 'cubic')
        return interp1d_f

    '''
    def rows(self):
        NUM_TRIES = 10
        for i in range(NUM_TRIES):
            try:
                df = pd.read_csv('s3://ay-emr-job/nrm/bff/'+self.srcdate[:4]+'/'+self.srcdate[4:6]+'/'+self.srcdate[6:8]+\
                                                        '/FCST_OD_'+self.srcdate+'_'+self.depdate+'.csv.gz',\
                                                         usecols = ['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN',\
                                                                    'POS','TP','FF','BC','SRDSUM','ARDSUM'])
                break
            except Exception as e:
                print(e)
                sleep(1)
        df = df.replace(np.nan, '')
        for i in range(NUM_TRIES):
            try:
                clsdf = pd.read_csv('s3://ay-emr-job/static/clsorder_old.csv')
                break
            except Exception as e:
                print(e)
                sleep(1)
        df = df.merge(clsdf, left_on = ['BC'], right_on = ['CLS'], how = 'left')
        df = df.sort_values(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','POS','TP','FF','ORDER'])

        clss = []
        srds = []
        ards = []
        prev_r = None
        prev_geo_od_ts_key = None
        prev_pos = None
        prev_tp = None
        prev_ff = None
        for k,r in df.iterrows():
            geo_od_ts_key = r['GEO_OD_TS_KEY']
            pos = r['POS']
            tp = r['TP']
            ff = str(r['FF'])

            if ff == '' or ff == 'nan' or ff == np.nan:
                continue

            if prev_geo_od_ts_key == geo_od_ts_key and\
               prev_pos == pos and\
               prev_tp == tp and\
               prev_ff == ff:
                # Fare-family continues.
                clss.append(r['BC'])
                srds.append(r['SRDSUM'])
                ards.append(r['ARDSUM'])
            else: 
                # New fare family.
                if len(srds) > 0:
                    # Output fare family.
                    ps = []
                    sDs = []
                    aDs = []
                    for i in range(len(clss)):
                        ps.append(self.yl.lookup(prev_r['BASE_OD_ORGN'],prev_r['BASE_OD_DSTN'],prev_r['POS'],clss[i]))
                        sDs.append(sum(srds[:i+1]))
                        aDs.append(sum(ards[:i+1]))
                   
                    print(prev_r['BASE_OD_ORGN'],prev_r['BASE_OD_DSTN'],prev_r['POS'])
                    print(clss) 
                    aspln = self.fit(ps,sDs)
                    sspln = self.fit(ps,aDs)

                    yield [prev_r['GEO_OD_TS_KEY'],prev_r['BASE_OD_ORGN'],prev_r['BASE_OD_DSTN'],\
                           prev_r['POS'],prev_r['TP'],prev_r['FF'],aspln,sspln]
               
                clss = [r['BC']]
                srds = [r['SRDSUM']]
                ards = [r['ARDSUM']]

            prev_r = r
            prev_geo_od_ts_key = geo_od_ts_key
            prev_pos = pos
            prev_tp = tp
            prev_ff = ff
    '''


if __name__ == "__main__":
    fitter = SplineDmdFitter('20200302','20200609')

    num = 0
    for r in fitter.rows():
        if num % 1000 == 0:
            print('num = ', num)
        num += 1




