import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from cls import *
#from s3utils import *
#from dfutils import *
from db_connector import *
from airport import *

ap = Airport()

class LPReaderFDCDB:
    '''
    Read demand curve from database and produce LP vector and matrices.
    '''
    @staticmethod
    def datetime_dates(fcstdatein, depdatein):
        fcstyear = fcstdatein[:4]
        fcstmonth = fcstdatein[4:6]
        fcstyear = fcstdatein[6:8]

        depyear = depdatein[:4]
        depmonth = depdatein[4:6]
        depday = depdatein[6:8]

        rs_curs = DBConnector.get_rs_curs()
         

        dcsvfname = 'ay-emr-job/nrm/bif/'+fcstyear+'/'+fcstmonth+\
                                      '/INV_'+fcstdatein+'.csv.gz'

        # FIXME: check forecast dates.
        if s3fileexists(dcsvfname):
            return fcstdatein, depdatein
        return None, None   


    def __init__(self, fcstdate, depdate, mode = 'remaining'):
        '''
        fcstdate YYYYMMDD string (from date for demand curve)
        depdate  YYYYMMDD string (departure date)
        '''
        self.fcstdate = fcstdate
        self.depdate = depdate
        self.next_depdate = datetime.strftime(datetime.strptime(self.depdate, '%Y%m%d') + timedelta(days = 1), '%Y%m%d')
        self.mode = mode # remaining or final

        fcstyear = self.fcstdate[:4]
        fcstmonth = self.fcstdate[4:6]
        fcstday = self.fcstdate[6:8]

        # Inventory data frame.
        invcsv = 's3://ay-emr-job/nrm/bif/'+fcstyear+'/'+fcstmonth+\
                                        '/INV_'+self.fcstdate+'.csv.gz'
        self.invdf = pd.read_csv(invcsv, low_memory = False).fillna('')
        self.invdf = self.invdf.loc[(self.invdf['DEPDT'] == int(self.depdate)) |
                                    (self.invdf['DEPDT'] == int(self.next_depdate))]
        self.invdf = self.invdf.loc[(self.invdf['ORGN'] == 'HEL') |\
                                    (self.invdf['DSTN'] == 'HEL')]
        self.invdf = self.invdf.loc[(self.invdf['CABIN'] == 'J') |\
                                    (self.invdf['CABIN'] == 'Y')]
        self.invdf = self.invdf.loc[(self.invdf['CAPO'] < 900)]
        self.invdf = optimize_bif(self.invdf)


    def read_dfs(self):
        pass


    def create_resources_map(self, cap_infl = None):
        '''
        Creates map fltnum + cabin + depdate -> index
        for fast retrieval of resource index.
        '''
        num = 0
        self.rownumd = {}
        self.rownum2cmpt = []
        self.cap = []
        self.fcap = [] # Full capacity.
        for index, row in self.invdf.iterrows():
            # Include next date flights from HEL departing before 3am.
            if int(row['DEPDT']) != int(self.depdate):
                if row['ORGN'] != 'HEL' or int(row['DEPTM']) > 300:
                    continue
            # Exclude this date flights from HEL departing before 3am.
            if int(row['DEPDT']) == int(self.depdate):
                if row['ORGN'] == 'HEL' and int(row['DEPTM']) <= 300:
                    continue
            if self.mode == 'remaining':
                actcap = max(0, int(row['CAPO']) - int(row['ESB']))
            else:
                actcap = max(0, int(row['CAPO']))
            if cap_infl is not None:
                actcap = cap_infl(row, actcap)
            fltnum, cabin = row['FLTNUM'], row['CABIN']
            if actcap > 0.0:
                k = str(int(fltnum)) + cabin + str(row['DEPDT'])
                self.cap.append(actcap)
                self.fcap.append(int(row['CAPO']))
                self.rownumd[k] = num
                lbl = row['CC'] + str(fltnum).zfill(4) + cabin + str(row['DEPDT'])
                self.rownum2cmpt.append(lbl)
                num += 1 
        self.cap = np.array(self.cap)
        self.fcap = np.array(self.fcap)
        return num


    def read(self, dmd_infl = None, cap_infl = None, yld_infl = None):
        '''
        Calculates all parameters for LP.
        '''
        self.read_dfs()
        nrows = self.create_resources_map(cap_infl)

        self.A

 
