import pandas as pd
import numpy as np

from cls import *


class LPReaderBasePWDC:
    '''
    Read demand curve files from s3 bucket and produce LP
    vector and matrices for base OD.
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
        dccsv = 's3://ay-rmp-home/nrm/pwdc/'+toyear+'/'+tomonth+'/'+today+\
                                        '/dc_' + self.fromdate + '_' + self.todate + '_' + self.depdate + '.csv.gz'
        self.dccsv = dccsv
        dc_dfo = pd.read_csv(dccsv, low_memory = False)
        self.dc_df = dc_dfo.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OPR_FLTNUM','POS','FF','BC'])\
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


        # Inventory data frame.
        invcsv = 's3://ay-rmp-home/nrm/bif/'+toyear+'/'+tomonth+\
                                        '/INV_'+self.todate+'.csv.gz'
        self.inv_df = pd.read_csv(invcsv, low_memory = False)
        self.inv_df = self.inv_df.loc[self.inv_df['DEPDT'] == int(self.depdate)] # flights for forecast date only.
        self.inv_df = self.inv_df.loc[(self.inv_df['ORGN'] == 'HEL') |\
                                      (self.inv_df['DSTN'] == 'HEL')]
        self.inv_df = self.inv_df.loc[(self.inv_df['CABIN'] == 'J') |\
                                      (self.inv_df['CABIN'] == 'Y')]

        # Booking data frame.
        bkgcsv = 's3://ay-rmp-home/nrm/bof/' + toyear + '/' + tomonth+\
                                        '/BKG_OD_' + self.todate + '.csv.gz'
        bkg_dfo = pd.read_csv(bkgcsv, low_memory = False)
        self.bkg_df = bkg_dfo.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEPT_DATE','ISO_COUNTRY','SELL_CLS'])\
                             .agg(['count'])\
                             .reset_index()
        self.bkg_df = self.bkg_df.loc[self.bkg_df['BASE_OD_DEPT_DATE'] == int(self.depdate)] # flights for forecast data only.
        # Remove special classes.
        self.bkg_df = self.bkg_df[self.bkg_df['SELL_CLS'] != 'A'] 
        self.bkg_df = self.bkg_df[self.bkg_df['SELL_CLS'] != 'G'] 
        self.bkg_df = self.bkg_df[self.bkg_df['SELL_CLS'] != 'X']
        self.bkg_df = self.bkg_df[self.bkg_df['SELL_CLS'] != 'E']
        self.bkg_df = self.bkg_df[self.bkg_df['SELL_CLS'] != 'F']
        self.bkg_df = self.bkg_df[self.bkg_df['SELL_CLS'] != 'U']

        # Yield data frame.
        yldcsv = 's3://ay-rmp-home/nrm/yield/' + toyear + '/' + tomonth +\
                                          '/YIELD_' + self.todate + '.csv.gz'
        self.yld_df = pd.read_csv(yldcsv, low_memory = False)
        

    def create_resources_map(self):
        '''
        Creates map fltnum + cabin -> index
        for fast retrieval of resource index.
        '''
        num = 0
        self.rownumd = {}
        self.capl = []
        for index, row in self.inv_df.iterrows():
            k = str(int(row['FLTNUM'])) + row['CABIN']
            self.capl.append(row['CAPO'])
            self.rownumd[k] = num
            num += 1


    def read(self):
        '''
        Calculates all parameters for LP.
        '''
        self.read_dfs()
        self.create_resources_map()
        
        self.A   = np.zeros((self.inv_df.shape[0], self.dc_df.shape[0]))    # Matrix of LP.
        self.f   = np.zeros(self.dc_df.shape[0])                            # Prices (fares) of LP.
        self.smu = np.zeros(self.dc_df.shape[0])                            # System demand.
        self.amu = np.zeros(self.dc_df.shape[0])                            # Adjusted demand.
        self.cap = np.zeros(self.inv_df.shape[0])                           # Capacities. 

        self.v_idx2flow = [] # Store map variable index -> base flow.
        self.v_flow2idx = {} # Store map base flow -> variable index.
        num = 0
        for index, row in self.dc_df.iterrows():
            fltnums = row['BASE_OPR_FLTNUM'].split('-')
            fltnums = [int(e) for e in fltnums]
            for fltnum in fltnums:
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

            flow = row['BASE_OD_ORGN']+','+row['BASE_OD_DSTN']+','+row['BASE_OPR_FLTNUM']+','+row['POS']+','+row['FF']+','+row['BC']
            self.v_idx2flow.append(flow)
            self.v_flow2idx[flow] = num

            num += 1
        
        num = 0
        for c in self.capl:
            self.cap[num] = self.capl[num]
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
    lpreaderpwdc = LPReaderBasePWDC('20180821', '20180828', '20190609')
    lpreaderpwdc.read()


