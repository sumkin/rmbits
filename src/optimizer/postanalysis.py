import pandas as pd


from postlpreader import *
#from glpsolver import *
from glpsolver import *
from bffreader import *


class PostAnalysis:


    def __init__(self, depdate):
        self.depdate = depdate
        self.lpr = PostLPReader(self.depdate)
        self.lpr.read()


    def solve(self):
        self.lps = GLPSolver(self.lpr.get_A(),\
                             self.lpr.get_cap(),\
                             self.lpr.get_d(),\
                             self.lpr.get_f(),\
                             self.lpr.get_prdt_names(),\
                             self.lpr.get_rsrc_names())
        val, sol = self.lps.solve('maxrev')
        return val, sol


    def solve_groups(self):
        depyear = self.depdate[:4]
        depmonth = self.depdate[4:6]

        print('solve_groups() called')
        print('self.depdate = ', self.depdate)

        bkgcsv = 's3://ay-emr-job/nrm/bof/'+depyear+'/'+depmonth+'/BKG_OD_'+self.depdate+'.csv.gz'
        bkgdf = pd.read_csv(bkgcsv, low_memory = False).fillna('')
        bkgdf = bkgdf.loc[bkgdf['BASE_OD_DEPT_DATE'] == int(self.depdate)]
        bkgdf = bkgdf.loc[bkgdf['SELL_CLS'] == 'G']
        bkgdf = bkgdf.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                               'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                               'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                               'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                               'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                               'BASE_OD_DEPT_DATE','BASE_SEG_DEPT_DATE','BASE_SEG_ARR_DATE',\
                               'GEO_ORGN','GEO_DSTN',\
                               'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM','PREV_MKT_CC','PREV_MKT_FLTNUM',\
                               'PREV_SEG_DEPT_DATE','PREV_SEG_ARR_DATE',\
                               'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM','NEXT_MKT_CC','NEXT_MKT_FLTNUM',\
                               'NEXT_SEG_DEPT_DATE','NEXT_SEG_ARR_DATE',\
                               'ISO_COUNTRY'])\
                     .agg({'REFERENCE': 'count', 'YIELD': 'sum'}).reset_index()
        bkgdf = bkgdf.loc[(bkgdf['BASE_OPR_CC'] == 'AY') | (bkgdf['BASE_OPR_CC'] == 'AY-AY')]

        for i, r in bkgdf.iterrows():
            ccs = r['BASE_OPR_CC'].split('-')
            cont = False
            for cc in ccs:
                if cc != 'AY':
                    cont = True
            if cont:
                continue
            ccs = r['BASE_OPR_CC'].split('-')
            fltnums = r['BASE_OPR_FLTNUM'].split('-')
            depdates = r['BASE_SEG_DEPT_DATE'].split('-')
            assert len(ccs) == len(fltnums)
            assert len(ccs) == len(fltnums)
            assert len(ccs) == len(depdates)
            base_cabins = []
            for i in range(len(ccs)):
                cabin = ccs[i] + str(int(fltnums[i])) + 'Y' + str(depdates[i])
                base_cabins.append(cabin)
            row = [r['BASE_OD_ORGN'],r['BASE_OD_DSTN'],r['BASE_OD_VIA'],\
                   '','','','',\
                   r['BASE_OPR_CC'],r['BASE_OPR_FLTNUM'],r['BASE_MKT_CC'],r['BASE_MKT_FLTNUM'],\
                   str(r['BASE_OD_DEPT_DATE']),r['BASE_SEG_DEPT_DATE'],r['BASE_SEG_ARR_DATE'],\
                   r['GEO_ORGN'],r['GEO_DSTN'],\
                   r['PREV_VIA'],r['PREV_OPR_CC'],r['PREV_OPR_FLTNUM'],\
                   r['PREV_MKT_CC'],r['PREV_MKT_FLTNUM'],r['PREV_SEG_DEPT_DATE'],r['PREV_SEG_ARR_DATE'],\
                   r['NEXT_VIA'],r['NEXT_OPR_CC'],r['NEXT_OPR_FLTNUM'],\
                   r['NEXT_MKT_CC'],r['NEXT_MKT_FLTNUM'],r['NEXT_SEG_DEPT_DATE'],r['NEXT_SEG_ARR_DATE'],\
                   r['ISO_COUNTRY'],'G','']
            geo_od_ts_key = BFFReader.get_geo_od_ts_key(row)
            flow = geo_od_ts_key + ',' + r['BASE_OD_ORGN'] + ',' + r['BASE_OD_DSTN'] + ',' + r['BASE_OD_VIA'] + ',' +\
                   r['BASE_OPR_CC'] + ',' + r['BASE_OPR_FLTNUM'] + ',' +\
                   r['BASE_MKT_CC'] + ',' + r['BASE_MKT_FLTNUM'] + ',' +\
                   str(r['BASE_OD_DEPT_DATE']) + ',' + str(r['BASE_SEG_DEPT_DATE']) + ',' + str(r['BASE_SEG_ARR_DATE']) + ',' +\
                   r['GEO_ORGN'] + ',' + r['GEO_DSTN'] + ',' +\
                   r['PREV_VIA'] + ',' + r['PREV_OPR_CC'] + ',' + r['PREV_OPR_FLTNUM'] + ',' +\
                   r['PREV_MKT_CC'] + ',' + r['PREV_MKT_FLTNUM'] + ',' +\
                   r['PREV_SEG_DEPT_DATE'] + ',' + r['PREV_SEG_ARR_DATE'] + ',' +\
                   r['NEXT_VIA'] + ',' + r['NEXT_OPR_CC'] + ',' + r['NEXT_OPR_FLTNUM'] + ',' +\
                   r['NEXT_MKT_CC'] + ',' + r['NEXT_MKT_FLTNUM'] + ',' + r['NEXT_SEG_DEPT_DATE'] + ',' + r['NEXT_SEG_ARR_DATE'] + ',' +\
                   r['ISO_COUNTRY'] + ',,G,L'
            flowsh = geo_od_ts_key+'-'+r['ISO_COUNTRY']+'--G-L'
            yld = float(r['YIELD']) / float(r['REFERENCE'])
            self.lpr.adjust_demand(flow, flowsh, yld, 2 * r['REFERENCE'], base_cabins)

        self.lps = GLPSolver(self.lpr.get_A(),\
                             self.lpr.get_cap(),\
                             self.lpr.get_d(),\
                             self.lpr.get_f(),\
                             self.lpr.get_prdt_names(),\
                             self.lpr.get_rsrc_names())
        val, sol = self.lps.solve('maxrev')
        return val, sol 


    def rows(self, sol):
        d = self.lpr.get_d()
        mp = self.lpr.get_f()
        f = self.lpr.get_p()

        for idx in range(len(sol)):
            yield self.lpr.get_flow(idx).split(',') +\
                  [mp[idx], f[idx], d[idx], sol[idx], 0] +\
                  [self.lpr.get_first_fcstdate(), self.lpr.get_last_fcstdate()]


if __name__ == "__main__":
    pa = PostAnalysis('20181212')
    val, sol = pa.solve_groups()
    print("val = ", val)

    

