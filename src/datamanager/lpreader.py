import pandas as pd
import numpy as np

from cls import *

class LPReader:
    """
    Read files from s3 bucket and produce LP vector and matrices.
    """

    def __init__(self, extdate, fcstextdate, fcstdate):
        """
        fcstextdate YYYYMMDD string (forecast extraction date)
        extdate YYYYMMDD string (extraction date for all files except forecast)
        fcstdate YYYYMMDD string (forecasting date)
        """
        self.extdate = extdate
        self.fcstextdate = fcstextdate
        self.fcstdate = fcstdate

    def read_dfs(self):
        """
        Read inventory and forecast data frames.
        """
        extyear  = self.extdate[:4]
        extmonth = self.extdate[4:6]
        extday   = self.extdate[6:8]

        fcstextyear  = self.fcstextdate[:4]
        fcstextmonth = self.fcstextdate[4:6]
        fcstextday   = self.fcstextdate[6:8]  

        # Forecast data frame.
        fcstcsv = 's3://ay-emr-job/nrm/bff/'+fcstextyear+'/'+fcstextmonth+'/'+fcstextday+\
                                         '/FCST_OD_'+self.fcstextdate+'_'+self.fcstdate+'.csv.gz'
        self.fcstcsv = fcstcsv
        self.fcst_df = pd.read_csv(fcstcsv).fillna('')
        self.fcst_df = self.fcst_df[self.fcst_df['BC'] != 'A'] # remove special classes.
        self.fcst_df = self.fcst_df[self.fcst_df['BC'] != 'G']
        self.fcst_df = self.fcst_df[self.fcst_df['BC'] != 'X']
        self.fcst_df = self.fcst_df[self.fcst_df['BC'] != 'E']
        self.fcst_df = self.fcst_df[self.fcst_df['BC'] != 'F']
        self.fcst_df = self.fcst_df[self.fcst_df['BC'] != 'U']
        
        # Inventory data frame.
        invcsv = 's3://ay-emr-job/nrm/bif/'+extyear+'/'+extmonth+\
                                        '/INV_'+self.extdate+'.csv.gz'
        self.inv_df = pd.read_csv(invcsv).fillna('')
        self.inv_df = self.inv_df.loc[self.inv_df['DEPDT'] == int(self.fcstdate)] # flights for forecast date only.
        self.inv_df = self.inv_df.loc[(self.inv_df['ORGN'] == 'HEL') |\
                                     (self.inv_df['DSTN'] == 'HEL')]
        self.inv_df = self.inv_df.loc[(self.inv_df['CABIN'] == 'J') |\
                                      (self.inv_df['CABIN'] == 'Y')]

        # Booking data frame.
        bkgcsv = 's3://ay-emr-job/nrm/bof/'+extyear+'/'+extmonth+\
                                        '/BKG_OD_'+self.extdate+'.csv.gz'
        self.bkg_df = pd.read_csv(bkgcsv).fillna('')
        self.bkg_df = self.bkg_df.loc[self.bkg_df['BASE_OD_DEPT_DATE'] == int(self.fcstdate)] # flights for forecast data only.
        self.bkg_df = self.bkg_df[self.bkg_df['SELL_CLS'] != 'A'] # remove spcial classes.
        self.bkg_df = self.bkg_df[self.bkg_df['SELL_CLS'] != 'G'] 
        self.bkg_df = self.bkg_df[self.bkg_df['SELL_CLS'] != 'X']
        self.bkg_df = self.bkg_df[self.bkg_df['SELL_CLS'] != 'E']
        self.bkg_df = self.bkg_df[self.bkg_df['SELL_CLS'] != 'F']
        self.bkg_df = self.bkg_df[self.bkg_df['SELL_CLS'] != 'U']

        # Yield data frame.
        yldcsv = 's3://ay-emr-job/nrm/yield/'+extyear+'/'+extmonth+\
                                          '/YIELD_'+self.extdate+'.csv.gz'
        self.yld_df = pd.read_csv(yldcsv).fillna('')
        
    def create_resources_map(self):
        """
        Creates map fltnum + cabin -> index
        for fast retrieval of resource index.
        """
        num = 0
        self.rownumd = {}
        for index, row in self.inv_df.iterrows():
            k = str(int(row['FLTNUM'])) + row['CABIN']
            self.rownumd[k] = num
            num += 1

    def read(self):
        """
        Calculates all parameters for LP.
        """
        self.read_dfs()
        self.create_resources_map()
        
        self.A   = np.zeros((self.inv_df.shape[0], self.fcst_df.shape[0]))  # Matrix of LP.
        self.f   = np.zeros(self.fcst_df.shape[0])                          # Prices (fares) of LP.
        self.smu = np.zeros(self.fcst_df.shape[0])                          # System demand.
        self.amu = np.zeros(self.fcst_df.shape[0])                          # Adjusted demand.
        self.cap = np.zeros(self.inv_df.shape[0])                           # Capacities. 

        num = 0
        for index, row in self.fcst_df.iterrows():
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
                try:
                    self.smu[num] = row['SFD']
                    self.amu[num] = row['AFD'] 
                except Exception as e:
                    print e 
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
    lpreader = LPReader('20180605', '20180605', '20190317')
    lpreader.read()


