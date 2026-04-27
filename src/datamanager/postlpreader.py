import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from defs import *
from cls import *
from s3utils import *


class PostLPReader:
    '''
    Read demand curves files from s3 bucket and produce
    static post LP vector and matrices.
    '''

    def __init__(self, depdate):
        '''
        depdate   YYYYMMDD string (departure date)
        '''
        print('PostLPReader.__init__() called')
        self.depdate = depdate
        self.next_depdate = datetime.strftime(datetime.strptime(self.depdate, '%Y%m%d') + timedelta(days = 1), '%Y%m%d')
        self.first_fcstdate = ''
        self.last_fcstdate  = ''


    def get_first_fcstdate(self):
        return self.first_fcstdate


    def get_last_fcstdate(self):
        return self.last_fcstdate


    def calc_periods(self):
        '''
        Calculates list of periods for given departure date.
        '''
        self.periods = []

        daysdelta = 1 
        dt = datetime.strptime(self.depdate, '%Y%m%d')
        for i in range(365):
            dtyear = datetime.strftime(dt, '%Y')
            dtmonth = datetime.strftime(dt, '%m')
            dtday = datetime.strftime(dt, '%d')
            dts = dtyear + dtmonth + dtday
            fname = 'ay-rmp-home/nrm/bff/' + dtyear + '/' + dtmonth+'/' + dtday + '/FCST_OD_' + dts+'_' + self.depdate+'.csv.gz'
            if s3fileexists(fname):
                daysdelta = 1
                print('dts = ', dts)
                self.periods.append(dts)
            else:
                if daysdelta == 10:
                    break
            dt = dt - timedelta(days = daysdelta)
        self.periods = list(reversed(self.periods))
        self.first_fcstdate = self.periods[0]
        self.last_fcstdate = self.periods[len(self.periods) - 1]
        print('first_fcstdate = ', self.first_fcstdate)
        print('last_fcstdate = ', self.last_fcstdate)


    def read_dfs(self):
        assert len(self.periods) > 0
        last_fcstyear = self.last_fcstdate[:4]
        last_fcstmonth = self.last_fcstdate[4:6]
        last_fcstday = self.last_fcstdate[6:8]
        last_fcstdate = last_fcstyear + last_fcstmonth + last_fcstday

        # Read demand curves dataframes and union them.
        dccsv = 's3://ay-rmp-home/nrm/fdc/'+last_fcstyear+'/'+last_fcstmonth+'/'+last_fcstday+\
                                       '/fdc_'+last_fcstdate+'_'+self.depdate+'.csv.gz'
        next_dccsv = 's3://ay-rmp-home/nrm/fdc/'+last_fcstyear+'/'+last_fcstmonth+'/'+last_fcstday+\
                                            '/fdc_'+last_fcstdate+'_'+self.next_depdate + '.csv.gz'
        ldc_df = pd.read_csv(dccsv, low_memory = False).fillna('')
        next_ldc_df = pd.read_csv(next_dccsv, low_memory = False).fillna('')
        ldc_df = ldc_df.append(next_ldc_df)

        ldc_df = ldc_df.loc[ldc_df['MP'] > 0]
        ldc_df = ldc_df.replace(np.nan, '', regex = True)
        ldc_df = ldc_df.groupby(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                                 'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                 'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                                 'BASE_OD_DEPT_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE',\
                                 'GEO_ORGN','GEO_DSTN',\
                                 'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM',\
                                 'PREV_MKT_CC','PREV_MKT_FLTNUM','PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                                 'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM',\
                                 'NEXT_MKT_CC','NEXT_MKT_FLTNUM','NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE',\
                                 'POS','FF','TP','BC'])\
                       .agg({'MP': 'mean', 'AFD': 'sum', 'GCC_ARMD': 'sum', 'GCC_AFMD': 'sum'})\
                       .reset_index()
        ldc_df = ldc_df[ldc_df['GCC_AFMD'] > EPS]
        ldc_df['KEY'] = ldc_df['GEO_OD_TS_KEY']+ldc_df['POS']+ldc_df['FF']+ldc_df['TP']+ldc_df['BC']
        ldc_df['AMD'] = ldc_df['GCC_ARMD']
        ldc_df['BASE_OD_DEP_DATE'] = ldc_df['BASE_OD_DEPT_DATE']
        ldc_df['SRC_DATE'] = last_fcstdate
        self.dc_df = ldc_df

        prev_fcstdate = self.periods[0]
        for period in self.periods[1:]:
            print("period = ", period)
            fcstdate  = period
            fcstyear  = fcstdate[:4]
            fcstmonth = fcstdate[4:6]
            fcstday   = fcstdate[6:8]

            dccsv = 's3://ay-rmp-home/nrm/pwdc/'+fcstyear+'/'+fcstmonth+'/'+fcstday+\
                                           '/dc_'+prev_fcstdate+'_'+fcstdate+'_'+self.depdate+'.csv.gz'
            dc_df = pd.read_csv(dccsv, low_memory = False).fillna('')
            dc_df = dc_df.loc[dc_df['MP'] > 0]
            dc_df = dc_df.replace(np.nan, '', regex = True)
            dc_df['MP'] = dc_df['MP'].replace('', 0.0, regex = True)
            dc_df['AMD'] = dc_df['AMD'].replace('', 0.0, regex = True)
            dc_df['MP'] = dc_df['MP'].astype(float)
            dc_df['AMD'] = dc_df['AMD'].astype(float)
            dc_df = dc_df.groupby(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                                   'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                   'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                                   'BASE_OD_DEP_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE',\
                                   'GEO_ORGN','GEO_DSTN',\
                                   'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM',\
                                   'PREV_MKT_CC','PREV_MKT_FLTNUM','PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                                   'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM',\
                                   'NEXT_MKT_CC','NEXT_MKT_FLTNUM','NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE',\
                                   'POS','FF','TP','BC'])\
                         .agg({'MP': 'mean', 'AMD': 'sum'})\
                         .reset_index()
            dc_df['SRC_DATE'] = fcstdate
            self.dc_df = self.dc_df.append(dc_df)

            prev_fcstdate = fcstdate

        # Take weighted average MP by demand.
        self.dc_df['AMDMP'] = self.dc_df['AMD'] * self.dc_df['MP']
        self.dc_df = self.dc_df.groupby(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                                         'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                         'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                                         'BASE_OD_DEP_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE',\
                                         'GEO_ORGN','GEO_DSTN',\
                                         'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM',\
                                         'PREV_MKT_CC','PREV_MKT_FLTNUM','PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                                         'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM',\
                                         'NEXT_MKT_CC','NEXT_MKT_FLTNUM','NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE',\
                                         'POS','FF','TP','BC'])\
                               .agg({'AMDMP': 'sum', 'AMD': 'sum'})\
                               .reset_index()
        self.dc_df['KEY'] = self.dc_df['GEO_OD_TS_KEY']+self.dc_df['POS']+self.dc_df['FF']+self.dc_df['TP']+self.dc_df['BC']
        self.dc_df = self.dc_df.loc[self.dc_df['AMD'] > 0]
        self.dc_df['MP'] = self.dc_df['AMDMP'] / self.dc_df['AMD']

        # Merge weighted average MP with final demand.
        self.dc_df = ldc_df.merge(self.dc_df, left_on = ['KEY'], right_on = ['KEY'], how = 'left')
        self.dc_df = self.dc_df[self.dc_df['GCC_AFMD'].notnull()]

        # Read inventory data frame for the first forecasting date.
        first_fcstyear = self.first_fcstdate[:4]
        first_fcstmonth = self.first_fcstdate[4:6]
        invcsv = 's3://ay-rmp-home/nrm/bif/'+first_fcstyear+'/'+first_fcstmonth+\
                                        '/INV_'+self.first_fcstdate+'.csv.gz'
        self.inv_df = pd.read_csv(invcsv, low_memory = False).fillna('')
        self.inv_df = self.inv_df.replace(np.nan, '', regex = True)
        self.inv_df = self.inv_df.loc[(self.inv_df['DEPDT'] == int(self.depdate)) |
                                      (self.inv_df['DEPDT'] == int(self.next_depdate))] # flights for forecast date only.
        self.inv_df = self.inv_df.loc[(self.inv_df['ORGN'] == 'HEL') | (self.inv_df['DSTN'] == 'HEL')]
        self.inv_df = self.inv_df.loc[(self.inv_df['CABIN'] == 'J') | (self.inv_df['CABIN'] == 'Y')]
        self.inv_df = self.inv_df.loc[(self.inv_df['CAPO'] < 900)]
        print('Data frames read.')


    def create_resources_map(self):
        '''
        Creates map fltnum + cabin + depdate -> index
        for fast retrieval of resource index.
        '''
        num = 0
        self.rownumd = {}
        self.rownum2cmpt = []
        self.cap = []
        for index, row in self.inv_df.iterrows():
            # Include next date flights from HEL departing before 3am.
            if int(row['DEPDT']) != int(self.depdate):
                if row['ORGN'] != 'HEL' or int(row['DEPTM']) > 300:
                    continue
            # Exclude this date flights from HEL departing before 3am.
            if int(row['DEPDT']) == int(self.depdate):
                if row['ORGN'] == 'HEL' and int(row['DEPTM']) <= 300:
                    continue
            try:
                actcap = int(row['CAPO']) - int(row['ESB'])
                fltnum, cabin = row['FLTNUM'], row['CABIN']
            except:
                continue
            if actcap > 0:
                k = row['CC'] + row['ORGN'] + row['DSTN'] + str(int(row['FLTNUM'])) + cabin + str(row['DEPDT'])
                self.cap.append(actcap)
                self.rownumd[k] = num
                lbl = row['CC'] + str(fltnum).zfill(4) + cabin + str(row['DEPDT'])
                self.rownum2cmpt.append(lbl)
                num += 1
        self.cap = np.array(self.cap)
        return num


    def read(self):
        '''
        Calculates all parameters for LP.
        '''
        self.calc_periods()
        print('self.calc_periods() has finished')
        self.read_dfs()
        print('self.read_dfs() has finished')

        nrows = self.create_resources_map()
        ncols = self.dc_df.shape[0]

        self.A   = np.zeros((nrows, ncols))   # Matrix LP.
        self.f   = np.zeros(ncols)            # Prices (fares) of LP.
        self.p   = np.zeros(ncols)            # Original fare.
        self.bkg = np.zeros(ncols)            # Bookigns.
        self.amu = np.zeros(ncols)            # Adjusted demand.
        self.d = np.zeros(ncols)              # Demand.

        self.v_idx2flow = []

        self.v_idx2flowsh  = []  # Store map variable index -> geo flow.
        self.v_flowsh2idx = {}  # Store map geo flow -> variable index.

        num = 0
        for index, row in self.dc_df.iterrows():
            geo_od_ts_key = str(row['GEO_OD_TS_KEY_x'])
            base_od_orgn = str(row['BASE_OD_ORGN_x'])
            base_od_dstn = str(row['BASE_OD_DSTN_x'])
            base_od_via = str(row['BASE_OD_VIA_x'])
            base_opr_cc = str(row['BASE_OPR_CC_x'])
            oprccs = str(row['BASE_OPR_CC_x']).split('-')
            base_opr_fltnum = str(row['BASE_OPR_FLTNUM_x'])
            oprfltnums = str(row['BASE_OPR_FLTNUM_x']).split('-')
            oprfltnums = [int(e) for e in oprfltnums]
            base_mkt_cc = str(row['BASE_MKT_CC_x'])
            base_mkt_fltnum = str(row['BASE_MKT_FLTNUM_x'])
            base_od_dept_date = str(row['BASE_OD_DEP_DATE_x'])
            base_seg_dep_date = str(row['BASE_SEG_DEP_DATE_x'])
            base_seg_dep_dates = base_seg_dep_date.split('-')
            base_seg_arr_date = str(row['BASE_SEG_ARR_DATE_x'])
            geo_orgn = str(row['GEO_ORGN_x'])
            geo_dstn = str(row['GEO_DSTN_x'])
            prev_via = str(row['PREV_VIA_x'])
            prev_opr_cc = str(row['PREV_OPR_CC_x'])
            prev_opr_fltnum = str(row['PREV_OPR_FLTNUM_x'])
            prev_mkt_cc = str(row['PREV_MKT_CC_x'])
            prev_mkt_fltnum = str(row['PREV_MKT_FLTNUM_x'])
            prev_seg_dep_date = str(row['PREV_SEG_DEP_DATE_x'])
            prev_seg_arr_date = str(row['PREV_SEG_ARR_DATE_x'])
            next_via = str(row['NEXT_VIA_x'])
            next_opr_cc = str(row['NEXT_OPR_CC_x'])
            next_opr_fltnum = str(row['NEXT_OPR_FLTNUM_x'])
            next_mkt_cc = str(row['NEXT_MKT_CC_x'])
            next_mkt_fltnum = str(row['NEXT_MKT_FLTNUM_x'])
            next_seg_dep_date = str(row['NEXT_SEG_DEP_DATE_x'])
            next_seg_arr_date = str(row['NEXT_SEG_ARR_DATE_x'])
            pos = str(row['POS_x'])
            bc = str(row['BC_x'])
            ff = str(row['FF_x'])
            tp = str(row['TP_x'])

            if is_special_cls(bc):
                d = max(0.0, row['AFD'])
            else:
                d = max(0.0, row['GCC_AFMD'])
            flow = geo_od_ts_key+','+base_od_orgn+','+base_od_dstn+','+base_od_via+','+\
                   base_opr_cc+','+base_opr_fltnum+','+\
                   base_mkt_cc+','+base_mkt_fltnum+','+\
                   str(base_od_dept_date)+','+str(base_seg_dep_date)+','+str(base_seg_arr_date)+','+\
                   geo_orgn+','+geo_dstn+','+\
                   prev_via+','+prev_opr_cc+','+prev_opr_fltnum+','+\
                   prev_mkt_cc+','+prev_mkt_fltnum+','+prev_seg_dep_date+','+prev_seg_arr_date+','+\
                   next_via+','+next_opr_cc+','+next_opr_fltnum+','+\
                   next_mkt_cc+','+next_mkt_fltnum+','+next_seg_dep_date+','+next_seg_arr_date+','+\
                   pos+','+ff+','+bc+','+tp
            flowsh = geo_od_ts_key+'-'+pos+'-'+ff+'-'+bc+'-'+tp
            cmpt = get_cmpt(bc)
            skip = False
            for i, fltnum in enumerate(oprfltnums):
                k = oprccs[i] + base_od_orgn + base_od_dstn + str(int(fltnum)) + cmpt + str(base_seg_dep_dates[i])
                if k in self.rownumd.keys():
                    self.A[self.rownumd[k], num] = 1
                else:
                    skip = True
                    break
            try:
                if skip:
                    self.f[num] = 0
                else:
                    self.f[num] = row['MP_x']
            except Exception as e:
                print('postlpreader 1', e)
            try:
                self.d[num] = d
            except Exception as e:
                print('postlpreader 2', e)

            self.v_idx2flow.append(flow)
            self.v_idx2flowsh.append(flowsh)
            self.v_flowsh2idx[flowsh] = num

            num += 1


    def adjust_demand(self, flow, flowsh, f, d, cabins):
        try:
            idx = self.v_flowsh2idx[flowsh]
            self.f[idx] = f
            self.d[idx] = max(self.d[idx], d)
        except Exception as e:
            print('Flow ', flowsh, ' not found')
            print('Adding flow...')
            idx = len(self.v_idx2flowsh)
            self.v_idx2flowsh.append(flowsh)
            self.v_idx2flow.append(flow)
            self.v_flowsh2idx[flowsh] = idx

            nrows,ncols = self.A.shape
            col = np.zeros((nrows,1))
            self.A = np.append(self.A, col, axis = 1)
            self.f = np.append(self.f, f)
            self.d = np.append(self.d, d)
            self.p = np.append(self.p, f)
            self.bkg = np.append(self.bkg, 0)

            for c in cabins:
                if c in self.rownumd.keys():
                    self.A[self.rownumd[c],idx] = 1
                else:
                    # Could happen if second segment on next day later than 3am.
                    print(c, ' is not found')
                    #assert False
            print('Flow is added.')


    def get_A(self):
        return self.A


    def get_f(self):
        return self.f


    def get_p(self):
        return self.p


    def get_bkg(self):
        return self.bkg


    def get_amu(self):
        return self.amu    


    def get_d(self):
        return self.d


    def get_cap(self):
        return self.cap


    def get_rownumd(self):
        return self.rownumd


    def get_fcstcsv(self):
        return self.fcstcsv


    def get_flowsh(self, idx):
        return self.v_idx2flowsh[idx]


    def get_flow(self, idx):
        return self.v_idx2flow[idx]


    def get_prdt_names(self):
        return self.v_idx2flowsh


    def get_prdt_idx(self, flowsh):
        for i in range(len(self.v_idx2flowsh)):
            if flowsh == self.v_idx2flowsh[i]:
                return i


    def get_rsrc_names(self):
        return self.rownum2cmpt


if __name__ == '__main__':
    postlpreader = PostLPReader('20181119')
    postlpreader.read()



