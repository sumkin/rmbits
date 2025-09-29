import csv
import pandas as pd
import numpy as np
from datetime import datetime

from utils import *
from s3utils import *

pd.options.mode.chained_assignment = None


class FDCDCPReader:
    '''
    Reads files from s3 bucket and produces 
    demand curves future.
    '''

    def __init__(self, fcstdate, depdate):
        '''
        Demand curve is produced for remaining demand
        estimated on forecasting date and for departure
        date depdate.
        All dates are in format YYYYMMDD.
        '''
        self.fcstdate = fcstdate
        self.depdate  = depdate


    def rows(self):
        '''
        Read data frames (forecast frame and yield)
        ''' 
        fcstdateyear  = self.fcstdate[:4]
        fcstdatemonth = self.fcstdate[4:6]
        fcstdateday   = self.fcstdate[6:8]
 
        depdateyear  = self.depdate[:4]
        depdatemonth = self.depdate[4:6]
        depdateday   = self.depdate[6:8]

        # Read forecast dataframes.
        fcstcsv = 's3://ay-emr-job/nrm/bff/'+fcstdateyear+'/'+fcstdatemonth+'/'+fcstdateday+\
                                         '/FCST_OD_'+self.fcstdate+'_'+self.depdate+'.csv.gz'
        fcstdcpcsv = 's3://ay-emr-job/nrm/bff/'+fcstdateyear+'/'+fcstdatemonth+'/'+fcstdateday+\
                                            '/FCST_OD_DCP_'+self.fcstdate+'_'+self.depdate+'.csv.gz'
        dcpcsv = 's3://ay-emr-job/static/dcp_ranges.csv'

        fcstdf = pd.read_csv(fcstcsv, low_memory = False)
        fcstdcpdf = pd.read_csv(fcstdcpcsv, low_memory = False)
        dcpdf = pd.read_csv(dcpcsv, low_memory = False)

        # Merge dcp dataframe.
        fcstdcpdf = fcstdcpdf.merge(dcpdf, left_on = ['DCP'], right_on = ['DTD_FROM'], how = 'left')
        fcstdcpdf['DTD_FROM'] = fcstdcpdf['DTD_FROM'].astype(int)
        fcstdcpdf['DTD_TO'] = fcstdcpdf['DTD_TO'].astype(int)

        # Replace NA values (bad for groupping).
        fcstdf = fcstdf.replace(np.nan, '')
        fcstdcpdf = fcstdcpdf.replace(np.nan, '')

        # Set remaining demand to zero for flows with negative marginal profits.
        fcstdf['SRD'].fillna(0.0, inplace = True)
        fcstdf['SRD'] = fcstdf['SRD'].astype(float)
        fcstdf['ARD'].fillna(0.0, inplace = True)
        fcstdf['ARD'] = fcstdf['ARD'].astype(float)
        fcstdf['SRGCCD'].fillna(0.0, inplace = True)
        fcstdf['SRGCCD'] = fcstdf['SRGCCD'].astype(float)
        fcstdf['ARGCCD'].fillna(0.0, inplace = True)
        fcstdf['ARGCCD'] = fcstdf['ARGCCD'].astype(float)
        fcstdf['SMPWA'].fillna(0.0, inplace = True)
        fcstdf['SMPWA'] = fcstdf['SMP'].astype(float)
        fcstdf['AMPWA'].fillna(0.0, inplace = True)
        fcstdf['AMPWA'] = fcstdf['AMP'].astype(float)
            
        fcstdf.loc[fcstdf['SMPWA'] < 0.0, 'SRD'] = 0.0
        fcstdf.loc[fcstdf['AMPWA'] < 0.0, 'ARD'] = 0.0
        fcstdf.loc[fcstdf['SMPWA'] < 0.0, 'SRGCCD'] = 0.0
        fcstdf.loc[fcstdf['AMPWA'] < 0.0, 'ARGCCD'] = 0.0

        # Group fcst dataframe.
        fcstdf = fcstdf.groupby(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                                 'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                                 'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                                 'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                 'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                                 'BASE_OD_DEP_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE',\
                                 'GEO_ORGN','GEO_DSTN',\
                                 'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM','PREV_MKT_CC','PREV_MKT_FLTNUM',\
                                 'PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                                 'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM','NEXT_MKT_CC','NEXT_MKT_FLTNUM',\
                                 'NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE',\
                                 'POS','BC','FF','TP','SRC_DATE'])\
                       .agg({'ARD': 'sum',\
                             'ARGCCD': 'sum',\
                             'SRD': 'sum',\
                             'SRGCCD': 'sum',\
                             'SMPWA': 'mean',\
                             'AMPWA': 'mean'}).reset_index()

        # Filter out zero demand, past DCPs and zero flows with negative MPs.
        fcstdcpdf = fcstdcpdf.loc[(fcstdcpdf['SRD'] > 0.0) | (fcstdcpdf['ARD'] > 0.0)]

        fcstdcpdf['SRD'].fillna(0.0, inplace = True)
        fcstdcpdf['SRD'] = fcstdcpdf['SRD'].astype(float)
        fcstdcpdf['ARD'].fillna(0.0, inplace = True)
        fcstdcpdf['ARD'] = fcstdcpdf['ARD'].astype(float)
        fcstdcpdf['SMP'].fillna(0.0, inplace = True)
        fcstdcpdf['SMP'] = fcstdcpdf['SMP'].astype(float)
        fcstdcpdf['AMP'].fillna(0.0, inplace = True)
        fcstdcpdf['AMP'] = fcstdcpdf['AMP'].astype(float)
 
        fcstdcpdf['DTD_TO_DATE'] = pd.to_datetime(fcstdcpdf['BASE_OD_DEP_DATE'], format='%Y%m%d') -\
                                   pd.to_timedelta(fcstdcpdf['DTD_TO'], unit = 'd')
        fcstdcpdf = fcstdcpdf.loc[fcstdcpdf['DTD_TO_DATE'] >= pd.to_datetime(fcstdcpdf['SRC_DATE'], format='%Y%m%d')]

        fcstdcpdf.loc[fcstdcpdf['SMP'] < 0.0, 'SRD'] = 0
        fcstdcpdf.loc[fcstdcpdf['AMP'] < 0.0, 'ARD'] = 0
        fcstdcpdf['SRD_DMD_FACTOR'] =\
            fcstdcpdf.apply(lambda r: dmd_factor(pd.to_datetime(r['BASE_OD_DEP_DATE'], format='%Y%m%d'),\
                                                 r['DTD_TO'],\
                                                 r['DTD_FROM'],\
                                                 pd.to_datetime(r['SRC_DATE'], format='%Y%m%d')) * r['SRD'], axis = 1)
        fcstdcpdf['ARD_DMD_FACTOR'] =\
            fcstdcpdf.apply(lambda r: dmd_factor(pd.to_datetime(r['BASE_OD_DEP_DATE'], format='%Y%m%d'),\
                                                 r['DTD_TO'],\
                                                 r['DTD_FROM'],\
                                                 pd.to_datetime(r['SRC_DATE'], format='%Y%m%d')) * r['ARD'], axis = 1)
        fcstdcpdf['ARD_ABOVE'] =\
            fcstdcpdf.apply(lambda r: r['ARD'] if r['AMP'] > 0 else 0, axis = 1)

        # Groupby fcstdcpdf.
        fcstdcpdf = fcstdcpdf.groupby(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                                       'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                                       'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                                       'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                       'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                                       'BASE_OD_DEP_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE',\
                                       'GEO_ORGN','GEO_DSTN',\
                                       'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM','PREV_MKT_CC','PREV_MKT_FLTNUM',\
                                       'PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                                       'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM','NEXT_MKT_CC','NEXT_MKT_FLTNUM',\
                                       'NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE',\
                                       'POS','BC','FF','TP','SRC_DATE'])\
                             .agg({'SRD': 'sum',\
                                   'ARD': 'sum',\
                                   'SRD_DMD_FACTOR': 'sum',\
                                   'ARD_DMD_FACTOR': 'sum',\
                                   'ARD_ABOVE': 'sum'}).reset_index()

        fcstdcpdf.rename(columns = {'SRD': 'SRD_CURVE_SUM', 'ARD': 'ARD_CURVE_SUM'}, inplace = True)
        fcstdcpdf = fcstdcpdf.merge(fcstdf, on = ['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                                                  'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                                                  'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                                                  'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                                  'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                                                  'BASE_OD_DEP_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE',\
                                                  'GEO_ORGN','GEO_DSTN',\
                                                  'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM','PREV_MKT_CC','PREV_MKT_FLTNUM',\
                                                  'PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                                                  'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM','NEXT_MKT_CC','NEXT_MKT_FLTNUM',\
                                                  'NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE',\
                                                  'POS','BC','FF','TP','SRC_DATE'], how = 'left')
     
        for k,r in fcstdcpdf.iterrows():
            geo_od_ts_key = r['GEO_OD_TS_KEY']
            base_od_orgn = r['BASE_OD_ORGN']
            base_od_dstn = r['BASE_OD_DSTN']
            base_od_via = r['BASE_OD_VIA']
            base_od_orgn_country = r['BASE_OD_ORGN_COUNTRY']
            base_od_orgn_region = r['BASE_OD_ORGN_REGION']
            base_od_dstn_country = r['BASE_OD_DSTN_COUNTRY']
            base_od_dstn_region = r['BASE_OD_DSTN_REGION']
            base_opr_cc = r['BASE_OPR_CC']
            base_opr_fltnum = r['BASE_OPR_FLTNUM']
            base_mkt_cc = r['BASE_MKT_CC']
            base_mkt_fltnum = r['BASE_MKT_FLTNUM']
            base_od_dep_date = r['BASE_OD_DEP_DATE']
            base_seg_dep_date = r['BASE_SEG_DEP_DATE']
            base_seg_arr_date = r['BASE_SEG_ARR_DATE']
            geo_orgn = r['GEO_ORGN']
            geo_dstn = r['GEO_DSTN']
            prev_via = r['PREV_VIA']
            prev_opr_cc = r['PREV_OPR_CC']
            prev_opr_fltnum = r['PREV_OPR_FLTNUM']
            prev_mkt_cc = r['PREV_MKT_CC']
            prev_mkt_fltnum = r['PREV_MKT_FLTNUM']
            prev_seg_dep_date = r['PREV_SEG_DEP_DATE']
            prev_seg_arr_date = r['PREV_SEG_ARR_DATE']
            next_via = r['NEXT_VIA']
            next_opr_cc = r['NEXT_OPR_CC']
            next_opr_fltnum = r['NEXT_OPR_FLTNUM']
            next_mkt_cc = r['NEXT_MKT_CC']
            next_mkt_fltnum = r['NEXT_MKT_FLTNUM']
            next_seg_dep_date = r['NEXT_SEG_DEP_DATE']
            next_seg_arr_date = r['NEXT_SEG_ARR_DATE']
            pos = r['POS']
            bc = r['BC']
            ff = r['FF']
            tp = r['TP']
            src_date = r['SRC_DATE']

            smpwa = r['SMPWA']
            ampwa = r['AMPWA']
            srd = r['SRD']
            ard = r['ARD']
            srd_curve_sum = r['SRD_CURVE_SUM']
            ard_curve_sum = r['ARD_CURVE_SUM']
            srd_dmd_factor = r['SRD_DMD_FACTOR']
            ard_dmd_factor = r['ARD_DMD_FACTOR']
            ard_above = r['ARD_ABOVE']

            if 0.1 * ard <= ard_curve_sum and\
               0.6 * ard <= ard_above:
                pass
            else:
                ard_curve_sum = srd_curve_sum
                ard_dmd_factor = srd_dmd_factor
                  
            yield geo_od_ts_key, base_od_orgn, base_od_dstn, base_od_via,\
                  base_od_orgn_country, base_od_orgn_region,\
                  base_od_dstn_country, base_od_dstn_region,\
                  base_opr_cc, base_opr_fltnum,\
                  base_mkt_cc, base_mkt_fltnum,\
                  base_od_dep_date, base_seg_dep_date, base_seg_arr_date,\
                  geo_orgn, geo_dstn,\
                  prev_via, prev_opr_cc, prev_opr_fltnum,\
                  prev_mkt_cc, prev_mkt_fltnum,\
                  prev_seg_dep_date, prev_seg_arr_date,\
                  next_via, next_opr_cc, next_opr_fltnum,\
                  next_mkt_cc, next_mkt_fltnum,\
                  next_seg_dep_date, next_seg_arr_date,\
                  pos, bc, ff, tp,\
                  smpwa, ampwa, srd, ard, srd_curve_sum, ard_curve_sum,\
                  srd_dmd_factor, ard_dmd_factor, ard_above,\
                  src_date


if __name__ == "__main__":
    fdc = FDCDCPReader('20190902','20200609')
    with open('out.csv','w') as fout:
        num = 0
        for r in fdc.rows():
            print(r)
            num += 1
            if num == 10:
                break





