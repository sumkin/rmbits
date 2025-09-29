import numpy as np
import pandas as pd
from time import sleep

from defs import *
from yield_lookup import *

class ExpDmdFitter:

    def __init__(self, srcdate, depdate):
        self.srcdate = srcdate
        self.depdate = depdate
        self.yl = YieldLookup(self.srcdate)

    @staticmethod
    def fit(ps, Ds):
        fps = []
        fDs = []
        for i in range(len(ps)):
            if abs(Ds[i]) > EPS:
                fps.append(ps[i])
                fDs.append(Ds[i])
        assert len(fps) == len(fDs)
        if len(fps) <= 1:
            return 0,0
        a11 = sum(fDs)
        a12 = sum([p * D for p,D in zip(fps, fDs)])
        a22 = sum([(p * p) * D for p,D in zip(fps, fDs)])
        b1 = sum([D * np.log(D) for D in fDs])
        b2 = sum([p * D * np.log(D) for p,D in zip(fps, fDs)])
    
        det = a11 * a22 - a12 * a12
        a = (b1 * a22 - b2 * a12) / det
        b = (b2 * a11 - b1 * a12) / det

        if abs(b) <= 10 * EPS:
            # Ignore for the time being.
            return 0, 0

        V = np.exp(a)
        w = -1/b
        return V, w

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
                clsdf = pd.read_csv('s3://ay-emr-job/static/clsorder.csv')
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
        for k, r in df.iterrows():
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
                        ps.append(self.yl.lookup(prev_r['BASE_OD_ORGN'],
                                                 prev_r['BASE_OD_DSTN'],
                                                 prev_r['POS'],
                                                 clss[i]))
                        sDs.append(sum(srds[:i+1]))
                        aDs.append(sum(ards[:i+1]))


                    sV, sw = self.fit(ps, sDs)
                    aV, aw = self.fit(ps, aDs)

                    yield [prev_r['GEO_OD_TS_KEY'], prev_r['BASE_OD_ORGN'], prev_r['BASE_OD_DSTN'],
                           prev_r['POS'], prev_r['TP'], prev_r['FF'],
                           sV, sw, aV, aw]

                clss = [r['BC']]
                srds = [r['SRDSUM']]
                ards = [r['ARDSUM']] 
                    
            prev_r = r
            prev_geo_od_ts_key = geo_od_ts_key
            prev_pos = pos
            prev_tp = tp
            prev_ff = ff

if __name__ == "__main__":
    fitter = ExpDmdFitter('20240318', '20240918')

    num = 0
    for r in fitter.rows():
        if r[-1] < 0.0:
            print(r)
        if num % 1000 == 0:
            print('num = ', num)
        num += 1



