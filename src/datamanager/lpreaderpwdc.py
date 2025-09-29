import pandas as pd
import numpy as np

from cls import *


class LPReaderPWDC:
    '''
    Read demand curve files from s3 bucket and produce LP vector and matrices.
    '''

    def __init__(self, fromdate, todate, depdate):
        '''
        fromdate YYYYMMDD string (from date for demand curve)
        todate   YYYYMMDD string (to date for demand curve)
        depdate  YYYYMMDD string (departure date)
        '''
        self.fromdate = fromdate
        self.todate   = todate
        self.depdate  = depdate
        self.next_depdate = datetime.strftime(datetime.strptime(self.depdate, '%Y%m%d') + timedelta(days = 1), '%Y%m%d')


    def read_dfs(self):
        '''
        Read inventory and demand curve data frames.
        '''
        fromyear  = self.fromdate[:4]
        frommonth = self.fromdate[4:6]
        fromday   = self.fromdate[6:8]

        toyear  = self.todate[:4]
        tomonth = self.todate[4:6]
        today   = self.todate[6:8]

        depyear  = self.depdate[:4]
        depmonth = self.depdate[4:6]
        depday   = self.depdate[6:8]  

        # Demand curve data frame.
        dccsv = 's3://ay-emr-job/nrm/pwdc/'+toyear+'/'+tomonth+'/'+today+\
                                        '/dc_' + self.fromdate + '_' + self.todate + '_' + self.depdate + '.csv.gz'
        next_dccsv = 's3://ay-emr-job/nrm/pwdc/'+toyear+'/'+tomonth+'/'+today+\
                                        '/dc_' + self.fromdate + '_' + self.todate + '_' + self.next_depdate + '.csv.gz'
        self.dccsv = dccsv
        self.next_dccsv = next_dccsv
        dc_dfo = pd.read_csv(dccsv, low_memory = False).fillna('')
        dc_dfo = dc_dfo.replace(np.nan, '', regex = True)
        next_dcdfo = pd.read_csv(next_dccsv, low_memory = False).fillna('')
        next_dc_dfo = next_dc_dfo.replace(np.nan, '', regex = True)
        dc_dfo = dc_dfo.append(next_dc_dfo)

        self.dc_df = dc_dfo.groupby(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                     'BASE_OD_DEPT_DATE','GEO_ORGN',\
                                     'GEO_DSTN','PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM',\
                                     'NEXT_VIA','NEXT_OPR_CC',\
                                     'NEXT_OPR_FLTNUM',\
                                     'POS','FF','TP','BC'])\
                           .agg({'MP': 'mean', 'F': 'mean', 'AD': 'sum', 'SD': 'sum',\
                                 'AMD': 'sum', 'SMD': 'sum'})\
                           .reset_index().sort_values(by=['F'])

        # Remove special classes.
        self.dc_df = self.dc_df[self.dc_df['BC'] != 'A'] 
        self.dc_df = self.dc_df[self.dc_df['BC'] != 'G']
        self.dc_df = self.dc_df[self.dc_df['BC'] != 'X']
        self.dc_df = self.dc_df[self.dc_df['BC'] != 'E']
        self.dc_df = self.dc_df[self.dc_df['BC'] != 'F']
        self.dc_df = self.dc_df[self.dc_df['BC'] != 'U']
       
        # Remove classes with negative marginal profits.
        self.dc_df = self.dc_df[self.dc_df['MP'] >= 0]
        self.dc_df = self.dc_df[self.dc_df['AMD'] > 0]
        self.dc_df['KEY'] = self.dc_df['BASE_OD_ORGN'].astype(str) +\
                            self.dc_df['BASE_OD_DSTN'].astype(str) +\
                            self.dc_df['BASE_OPR_CC'].astype(str) +\
                            self.dc_df['BASE_OPR_FLTNUM'].astype(str) +\
                            self.dc_df['BASE_OD_DEPT_DATE'].astype(str) +\
                            self.dc_df['GEO_ORGN'].astype(str) +\
                            self.dc_df['GEO_DSTN'].astype(str) +\
                            self.dc_df['PREV_VIA'].astype(str) +\
                            self.dc_df['PREV_OPR_CC'].astype(str) +\
                            self.dc_df['PREV_OPR_FLTNUM'].astype(str) +\
                            self.dc_df['NEXT_VIA'].astype(str) +\
                            self.dc_df['NEXT_OPR_CC'].astype(str) +\
                            self.dc_df['NEXT_OPR_FLTNUM'].astype(str) +\
                            self.dc_df['POS'].astype(str) +\
                            self.dc_df['TP'].astype(str) +\
                            self.dc_df['BC'].astype(str)
        self.dc_df = self.dc_df.reset_index(0)

        # Inventory data frame.
        invcsv = 's3://ay-emr-job/nrm/bif/'+toyear+'/'+tomonth+\
                                        '/INV_'+self.todate+'.csv.gz'
        self.inv_df = pd.read_csv(invcsv, low_memory = False).fillna('')
        self.inv_df = self.inv_df.loc[self.inv_df['DEPDT'] == int(self.depdate)] # flights for forecast date only.
        self.inv_df = self.inv_df.loc[(self.inv_df['ORGN'] == 'HEL') |\
                                      (self.inv_df['DSTN'] == 'HEL')]
        self.inv_df = self.inv_df.loc[(self.inv_df['CABIN'] == 'J') |\
                                      (self.inv_df['CABIN'] == 'Y')]


        # Yield data frame.
        yldcsv = 's3://ay-emr-job/nrm/yield/' + toyear + '/' + tomonth +\
                                          '/YIELD_' + self.todate + '.csv.gz'
        self.yld_df = pd.read_csv(yldcsv, low_memory = False).fillna('')
       
        # FF map data frame.
        ffmapcsv = 's3://ay-emr-jo/ffmap/FF_MAP.csv'
        self.ffmap_df = pd.read_csv(ffmapcsv, low_memory = False).fillna('')
        self.ffmap_df = self.ffmap_df.replace(np.nan, '', regex = True)
 

    def create_resources_map(self):
        '''
        Creates map fltnum + cabin -> index
        for fast retrieval of resource index.
        '''
        num = 0
        self.rownumd = {}
        self.rownum2cmpt = []
        self.cap = []
        for index, row in self.inv_df.iterrows():
            # Include next date flights departing before 3am.
            if int(row['DEPDT']) != int(self.depdate):
                if int(row['DEPTM']) > 300:
                    continue
            # Exclude this date flights departing before 3am.
            if int(row['DEPDT']) == int(self.depdate):
                if int(row['DEPTM']) <= 300:
                    continue
            actcap = max(0, int(row['CAPO']) - int(row['ESB'])
            fltnum, cabin = row['FLTNUM'], row['CABIN']
            if actcap > 0.0:
                k = str(int(fltnum)) + cabin + str(row['DEPDT'])
                self.cap.append(actcap)
                self.rownumd[k] = num
                lbl = row['CC'] + str(fltnum).zfill(4) + cabin + str(row['CABIN'])
                self.rownum2cmpt.append(lbl)
                num += 1
        self.cap = np.array(self.cap)
        return num


    def read(self):
        '''
        Calculates all parameters for LP.
        '''
        self.read_dfs()
        nrows = self.create_resources_map()
        
        self.A   = np.zeros((nrows, self.dc_df.shape[0]))  # Matrix of LP.
        self.f   = np.zeros(self.dc_df.shape[0])           # Prices (fares) of LP.
        self.p   = np.zeros(self.dc_df.shape[0])
        self.bkg = np.zeros(self.dc_df.shape[0])           # Bookings.
        self.smu = np.zeros(self.dc_df.shape[0])           # System demand.
        self.amu = np.zeros(self.dc_df.shape[0])           # Adjusted demand.

        self.v_idx2flowsh   = []  # Store map variable index -> geo flow.
        self.v_idx2flow     = []  
        self.v_flowsh2idx   = {}  # Store map goe flow -> variable index.
        num = 0
        for index, row in self.dcbkg_df.iterrows():
            geo_od_ts_key = row['GEO_OD_TS_KEY']
            base_od_orgn = row['BASE_OD_ORGN_dc']
            base_od_dstn = row['BASE_OD_DSTN_dc']
            base_opr_cc = row['BASE_OPR_CC_dc']
            oprccs = str(row['BASE_OPR_CC']).split('-')
            base_opr_fltnum = str(row['BASE_OPR_FLTNUM_dc'])
            oprfltnums = str(row['BASE_OPR_FLTNUM']).split('-')
            oprfltnums = [int(e) for e in oprfltnums]
            base_od_dept_date = str(row['BASE_OD_DEPT_DATE_dc'])
            geo_orgn = str(row['GEO_ORGN_dc'])
            geo_dstn = str(row['GEO_DSTN_dc'])
            prev_via = str(row['PREV_VIA_dc'])
            prev_opr_cc = str(row['PREV_OPR_CC_dc'])
            prev_opr_fltnum = str(row['PREV_OPR_FLTNUM_dc'])
            next_via = str(row['NEXT_VIA_dc'])
            next_opr_cc = str(row['NEXT_OPR_CC_dc'])
            next_opr_fltnum = str(row['NEXT_OPR_FLTNUM_dc'])
            pos = str(row['POS'])
            bc = str(row['BC'])
            ff = str(row['FF'])
            tp = str(row['TP'])
            flow = geo_od_ts_key+','+base_od_orgn+','+base_od_dstn+','+base_opr_cc+','+base_opr_fltnum+','+\
                   str(base_od_dept_date)+','+geo_orgn+','+\
                   geo_dstn+','+prev_via+','+prev_opr_cc+','+prev_opr_fltnum+','+\
                   next_via+','+next_opr_cc+','+\
                   next_opr_fltnum+','+pos+','+ff+','+bc+','+tp
            for fltnum in oprfltnums:
                try:
                    cmpt = get_cmpt(row['BC'])
                    k = str(fltnum) + cmpt
                    if k in self.rownumd.keys():
                        self.A[self.rownumd[k],num] = 1
                    else:
                        # Some leg might not have J cabin.
                        k = str(fltnum) + 'Y'
                        self.A[self.rownumd[k],num] = 1
                except Exception as e:
                    # There could be no flight on this date.
                    # Ignore this demand.
                    pass
            try:
                self.f[num] = row['MP']
            except Exception as e:
                print e      
            row['SMD'] = max(0.0, row['SMD'])
            row['AMD'] = max(0.0, row['AMD'])
            assert row['SMD'] < np.inf
            assert row['AMD'] < np.inf
            try:
                self.smu[num] = row['SMD']
                self.amu[num] = row['AMD'] 
            except Exception as e:
                print e 

            self.v_idx2flow.append(flow)
            self.v_flow2idx[flow] = num

            num += 1
        

    def get_A(self):
        return self.A


    def get_f(self):
        return self.f


    def get_smu(self):
        return self.smu


    def get_amu(self):
        return self.amu


    def get_cap(self):
        return self.cap


    def get_rownumd(self):
        return self.rownumd     


    def get_fcstcsv(self): 
        return self.fcstcsv


if __name__ == '__main__':
    lpreaderpwdc = LPReaderPWDC('20180821', '20180828', '20190609')
    lpreaderpwdc.read()


