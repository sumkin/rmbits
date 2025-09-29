import csv
import pandas as pd
import numpy as np

from cls import *
from geo_yield_lookup import *
from demand_curve import *


class PWDCReader:
    '''
    Reads files from s3 bucket and produces 
    demand curves for one past week.
    '''

    def __init__(self, datefrom, dateto, depdate):
        '''
        Demand curve is produced for demand on interval
        [datefrom, dateto] for departure date depdate.
        All dates are in format YYYYMMDD.
        '''
        self.datefrom = datefrom
        self.dateto   = dateto
        self.depdate  = depdate 


    def rows(self):
        '''
        Read data frames (two forecast frames and yield)
        ''' 
        datefromyear  = self.datefrom[:4]
        datefrommonth = self.datefrom[4:6]
        datefromday   = self.datefrom[6:8]
 
        datetoyear  = self.dateto[:4]
        datetomonth = self.dateto[4:6]
        datetoday   = self.dateto[6:8]

        depdateyear  = self.depdate[:4]
        depdatemonth = self.depdate[4:6]
        depdateday   = self.depdate[6:8]

        # Read forecast dataframe.
        fcstcsvfrom = 's3://ay-emr-job/nrm/bff/'+datefromyear+'/'+datefrommonth+'/'+datefromday+\
                                             '/FCST_OD_'+self.datefrom+'_'+self.depdate+'.csv.gz'
        fcstcsvto = 's3://ay-emr-job/nrm/bff/'+datetoyear+'/'+datetomonth+'/'+datetoday+\
                                           '/FCST_OD_'+self.dateto+'_'+self.depdate+'.csv.gz'

        fcstdffrom = pd.read_csv(fcstcsvfrom, low_memory = False).fillna('')
        fcstdfto = pd.read_csv(fcstcsvto, low_memory = False).fillna('')

        fcstdf = pd.merge(fcstdfto, fcstdffrom, how='inner',
                          left_on=['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                                   'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                                   'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                                   'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                   'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                                   'BASE_OD_DEP_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE',\
                                   'GEO_ORGN','GEO_DSTN',\
                                   'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM',\
                                   'PREV_MKT_CC','PREV_MKT_FLTNUM','PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                                   'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM',\
                                   'NEXT_MKT_CC','NEXT_MKT_FLTNUM','NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE',\
                                   'POS','BC','FF','TP'],
                          right_on=['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                                    'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                                    'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                                    'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                    'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                                    'BASE_OD_DEP_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE',\
                                    'GEO_ORGN','GEO_DSTN',\
                                    'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM',\
                                    'PREV_MKT_CC','PREV_MKT_FLTNUM','PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                                    'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM',\
                                    'NEXT_MKT_CC','NEXT_MKT_FLTNUM','NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE',\
                                    'POS','BC','FF','TP'],
                          suffixes=['_CURR','_PREV'])
        fcstdf['ADMD'] = fcstdf['ARD_PREV'] - fcstdf['ARD_CURR']   
        fcstdf['SDMD'] = fcstdf['SRD_PREV'] - fcstdf['SRD_CURR']

        # Read class order and join it to forecast dataframe.
        clsdf = pd.read_csv('s3://ay-emr-job/static/clsorder.csv').fillna('')
        fcstdf = pd.merge(fcstdf, clsdf, how='left',
                                         left_on=['BC'],
                                         right_on=['CLS'])

        # Sort by travel solution, fare family, travel purpose and class order.
        fcstdf = fcstdf.sort_values(by=['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                                        'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                                        'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                                        'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                        'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                                        'BASE_OD_DEP_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE',\
                                        'GEO_ORGN','GEO_DSTN',\
                                        'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM',\
                                        'PREV_MKT_CC','PREV_MKT_FLTNUM','PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                                        'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM',\
                                        'NEXT_MKT_CC','NEXT_MKT_FLTNUM','NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE',\
                                        'POS','FF','TP','ORDER'])

        # Create yield lookuper.
        yl = GeoYieldLookup(self.dateto)

        # Iterate over forecast dataframe.
        prev_ts  = 31 * [None]
        prev_pos = None
        prev_ff = None
        prev_tp = None
        clss,mps,fs,ad,sd = [],[],[],[],[]
        num = 0
        tot_num = fcstdf.shape[0]
        for k,r in fcstdf.iterrows():
            num += 1
            if num % 1000 == 0:
                print(num,'/',tot_num, int(100 * num / tot_num), '%')
            curr_ts = [e if e == e else '' for e in list(r[:31])] # nan != nan
            curr_pos = r['POS']
            curr_ff = r['FF']
            curr_tp = r['TP']
            if num == 1:
                f = yl.lookup(r['BASE_OD_ORGN'],r['BASE_OD_DSTN'],r['POS'],r['BC'])
                clss.append(r['BC'])
                mps.append(r['MP_CURR'])
                fs.append(f)
                ad.append(r['ADMD'])
                sd.append(r['SDMD'])
            else:
                if curr_ts == prev_ts and curr_pos == prev_pos and curr_ff == prev_ff and curr_tp == prev_tp:
                    f = yl.lookup(r['BASE_OD_ORGN'],r['BASE_OD_DSTN'],r['POS'],r['BC'])
                    clss.append(r['BC'])
                    mps.append(r['MP_CURR'])
                    fs.append(f)
                    ad.append(r['ADMD'])
                    sd.append(r['SDMD'])
                else:
                    ads,amds = dc_calc(np.array(mps), np.array(fs), np.array(ad))
                    sds,smds = dc_calc(np.array(mps), np.array(fs), np.array(sd))
                    for i in range(len(clss)):
                        if is_special_cls(clss[i]):
                            yield prev_ts + [prev_pos, prev_ff, prev_tp, clss[i], mps[i], fs[i], 2 * ad[i], 2 * sd[i], 0, 0]
                        else:
                            yield prev_ts + [prev_pos, prev_ff, prev_tp, clss[i], mps[i], fs[i], ads[i], sds[i], amds[i], smds[i]]
                    clss,mps,fs,ad,sd = [r['BC']],[r['MP_CURR']],\
                                        [yl.lookup(r['BASE_OD_ORGN'],r['BASE_OD_DSTN'],r['POS'],r['BC'])],\
                                        [r['ADMD']],[r['SDMD']]    
            prev_ts = curr_ts
            prev_pos = curr_pos
            prev_ff = curr_ff
            prev_tp = curr_tp


if __name__ == "__main__":
    pwdc = PWDCReader('20181204','20181211','20181212')
    with open('out.csv','w') as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                            'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                            'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                            'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                            'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                            'BASE_OD_DEP_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE',\
                            'GEO_ORGN','GEO_DSTN',\
                            'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM',\
                            'PREV_MKT_CC','PREV_MKT_FLTNUM',\
                            'PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                            'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM',\
                            'NEXT_MKT_CC','NEXT_MKT_FLTNUM',\
                            'NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE',\
                            'POS','FF','TP','BC','MP','F','AD','SD','AMD','SMD'])
        for r in pwdc.rows():
            csvwriter.writerow(r)
        csvwriter.flush()



