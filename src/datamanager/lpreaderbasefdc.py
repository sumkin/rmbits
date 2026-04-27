import pandas as pd
import numpy as np

from cls import *


class LPReaderBaseFDC:
    '''
    Read demand curve files from s3 bucket and produce LP
    vector and matrice for base OD.
    '''

    def __init__(self, fcstdate, depdate):
        '''
        fcstdate YYYYMMDD string (from date for demand curve)
        depdate  YYYYMMDD string (departure date)
        '''
        self.fcstdate = fcstdate
        self.depdate  = depdate


    def read_dfs(self):
        '''
        Read inventory and demand curve data frames.
        '''
        fcstyear  = self.fcstdate[:4]
        fcstmonth = self.fcstdate[4:6]
        fcstday   = self.fcstdate[6:8]

        depyear  = self.depdate[:4]
        depmonth = self.depdate[4:6]
        depday   = self.depdate[6:8]  

        # Demand curve data frame.
        dccsv = 's3://ay-rmp-home/nrm/fdc/'+fcstyear+'/'+fcstmonth+'/'+fcstday+\
                                       '/dc_'+self.fcstdate+'_'+self.depdate+'.csv.gz'
        self.dccsv = dccsv
        dc_dfo = pd.read_csv(dccsv, low_memory = False).fillna('')
        self.dc_df = dc_dfo.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OPR_FLTNUM','POS','FF','BC'])\
                           .agg({'MP': 'mean', 'F': 'mean', 'AD': 'sum', 'SD': 'sum',\
                                 'AMD': 'sum', 'SMD': 'sum'})\
                           .reset_index()

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
        self.dc_df['KEY'] = self.dc_df['BASE_OD_ORGN'] +\
                            self.dc_df['BASE_OD_DSTN'] +\
                            self.dc_df['BASE_OPR_FLTNUM'] +\
                            self.dc_df['POS'] +\
                            self.dc_df['BC']
        self.dc_df = self.dc_df.reset_index(0)

        # Inventory data frame.
        invcsv = 's3://ay-rmp-home/nrm/bif/'+fcstyear+'/'+fcstmonth+\
                                        '/INV_'+self.fcstdate+'.csv.gz'
        self.inv_df = pd.read_csv(invcsv, low_memory = False).fillna('')
        self.inv_df = self.inv_df.loc[self.inv_df['DEPDT'] == int(self.depdate)] # flights for forecast date only.
        self.inv_df = self.inv_df.loc[(self.inv_df['ORGN'] == 'HEL') |\
                                      (self.inv_df['DSTN'] == 'HEL')]
        self.inv_df = self.inv_df.loc[(self.inv_df['CABIN'] == 'J') |\
                                      (self.inv_df['CABIN'] == 'Y')]

        # Booking data frame.
        bkgcsv = 's3://ay-rmp-home/nrm/bof/' + fcstyear + '/' + fcstmonth+\
                                        '/BKG_OD_' + self.fcstdate + '.csv.gz'
        bkg_dfo = pd.read_csv(bkgcsv, low_memory = False).fillna('')
        self.bkg_df = bkg_dfo[['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OPR_FLTNUM','BASE_OD_DEPT_DATE','ISO_COUNTRY','SELL_CLS','REFERENCE']]\
                             .groupby(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OPR_FLTNUM','BASE_OD_DEPT_DATE','ISO_COUNTRY','SELL_CLS'])\
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
        self.bkg_df.columns = ['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OPR_FLTNUM','BASE_OD_DEPT_DATE','POS','BC','COUNT']
        self.bkg_df['KEY'] = self.bkg_df['BASE_OD_ORGN'] +\
                             self.bkg_df['BASE_OD_DSTN'] +\
                             self.bkg_df['BASE_OPR_FLTNUM'] +\
                             self.bkg_df['POS'] +\
                             self.bkg_df['BC']
        self.bkg_df = self.bkg_df.reset_index(0)
        # Merge data frames.
        self.dcbkg_df = self.dc_df.merge(self.bkg_df,\
                                         on = 'KEY',\
                                         suffixes = ('_dc','_bkg'),
                                         how='left')
        self.dcbkg_df = self.dcbkg_df.reset_index()
        self.dcbkg_df = self.dcbkg_df.replace(np.nan, '', regex = True)
        self.dcbkg_df['COUNT'] = self.dcbkg_df['COUNT'].replace('', 0, regex = True)

        # Yield data frame.
        yldcsv = 's3://ay-rmp-home/nrm/yield/' + fcstyear + '/' + fcstmonth +\
                                          '/YIELD_' + self.fcstdate + '.csv.gz'
        self.yld_df = pd.read_csv(yldcsv, low_memory = False).fillna('')

        # FF map data frame.
        ffmapcsv = 's3://ay-rmp-home/ffmap/FF_MAP_LV.csv'
        self.ffmap_df = pd.read_csv(ffmapcsv, low_memory = False).fillna('')
        self.ffmap_df = self.ffmap_df.replace(np.nan, '', regex=True)
        

    def create_resources_map(self):
        '''
        Creates map fltnum + cabin -> index
        for fast retrieval of resource index.
        '''
        num = 0
        self.rownumd = {}
        self.capl = []
        for index, row in self.inv_df.iterrows():
            k = row['CC'] + row['ORGN'] + row['DSTN'] + str(int(row['FLTNUM'])) + row['CABIN'] + row['BASE_OD_DEP_DATE']
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
        self.bkg = np.zeros(self.dc_df.shape[0])                            # Bookings.
        self.smu = np.zeros(self.dc_df.shape[0])                            # System demand.
        self.amu = np.zeros(self.dc_df.shape[0])                            # Adjusted demand.
        self.cap = np.zeros(self.inv_df.shape[0])                           # Capacities. 

        self.v_idx2flow = [] # Store map variable index -> base flow.
        self.v_flow2idx = {} # Store map base flow -> variable index.
        num = 0
        for index, row in self.dcbkg_df.iterrows():
            base_od_orgn = row['BASE_OD_ORGN_dc']
            base_od_dstn = row['BASE_OD_DSTN_dc']
            base_opr_fltnum = row['BASE_OPR_FLTNUM_dc']
            fltnums = row['BASE_OPR_FLTNUM_dc'].split('-')
            fltnums = [int(e) for e in fltnums]
            pos = row['POS_dc']
            bc = row['BC_dc']
            ff = row['FF']
            flow = base_od_orgn+','+base_od_dstn+','+base_opr_fltnum+','+pos+' '+ff+','+bc

            for fltnum in fltnums:
                try:
                    cmpt = get_cmpt(row['BC_dc'])
                    k = row['CC_dc'] + base_od_orgn + base_od_dstn + str(fltnum) + cmpt + row['BASE_OD_DEP_DATE']
                    if k in self.rownumd.keys():
                        self.A[self.rownumd[k],num] = 1
                    else:
                        # Some leg might not have J cabin.
                        k = row['CC_dc'] + base_od_orgn + base_od_dstn + str(fltnum) + 'Y' + row['BASE_OD_DEP_DATE']
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
                self.bkg[num] = row['COUNT']
                self.smu[num] = row['SMD']
                self.amu[num] = row['AMD'] 
            except Exception as e:
                print e 

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


    def get_bkg(self):
        return self.bkg


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


    def get_flow(self, idx):
        return self.v_idx2flow[idx]


if __name__ == '__main__':
    lpreaderfdc = LPReaderBaseFDC('20180828', '20180903')
    lpreaderfdc.read()


