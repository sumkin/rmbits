import csv
import pandas as pd
import numpy as np

from cls import *
from s3utils import *


class FAReader:
    '''
    Read data for forecast accuracy analysis.
    '''

    def __init__(self, bkgdate, depdate):
        '''
        bkgdate YYYYMMDD string. Date for which quality of forecast is evaluated (booking date).
        depdate YYYYMMDD string. Departure date.
        '''
        self.bkgdate = bkgdate
        self.depdate = depdate
        
        pbkgdt = datetime.strptime(bkgdate, '%Y%m%d')
        pbkgdt = pbkgdt - timedelta(days = 1)
        self.pbkgdate = datetime.strftime(pbkgdt, '%Y%m%d')


    def read_dfs(self):
        bkgyear = self.bkgdate[:4]
        bkgmonth = self.bkgdate[4:6]
        bkgday = self.bkgdate[6:8]

        print('Reading dataframes...')
        # Read pwdc dataframe.
        s3prefix, startdt, enddt, within = s3getpwdcprefix(self.bkgdate)
        self.pwdf = pd.read_csv('s3://ay-rmp-home/'+s3prefix+\
                                '_'+self.depdate+'.csv.gz', low_memory = False)
        # Take only base flows, because for others we don't know availability.
        self.pwdf = self.pwdf.loc[(self.pwdf['PREV_OPR_CC'].isnull()) & (self.pwdf['NEXT_OPR_CC'].isnull())]

        # Read av dataframe.
        dtypes = {'ORGN': str,
                  'DSTN': str,
                  'VIA': str,
                  'CC': str,
                  'FLTNUM': str,
                  'OD_DEPT_DATE': int,
                  'OD_DEPT_DOW': int,
                  'SEG_DEPT_DATE': str,
                  'POS': str,
                  'J': int,
                  'C': int,
                  'D': int,
                  'I': int,
                  'F': int,
                  'U': int,
                  'Y': int,
                  'B': int,
                  'H': int,
                  'K': int,
                  'M': int,
                  'P': int,
                  'T': int,
                  'L': int,
                  'V': int,
                  'S': int,
                  'N': int,
                  'G': int,
                  'A': int,
                  'Q': int,
                  'O': int,
                  'Z': int,
                  'R': int,
                  'W': int,
                  'X': int,
                  'E': int,
                  'LOCJ': str,
                  'LOCIJ': int,
                  'LOCY': str,
                  'LOCIY': int,
                  'LOCJ_WOSC': str,
                  'LOCIJ_WOSC': int,
                  'LOCY_WOSC': str,
                  'LOCIY_WOSC': int,
                  'SRC_DATE': int}
        self.avdf = pd.read_csv('s3://ay-rmp-home/nrm/baf/'+bkgyear+'/'+bkgmonth+\
                                '/AV_OD_'+self.bkgdate+'.csv.gz', dtype = dtypes)
        self.avdf = self.avdf[self.avdf['OD_DEPT_DATE'] == int(self.depdate)]

        # Read bkg dataframe.
        self.bkgdf = pd.read_csv('s3://ay-rmp-home/nrm/bcd/'+bkgyear+'/'+bkgmonth+\
                                 '/bkgd_'+self.pbkgdate+'_'+self.bkgdate+'.csv.gz', low_memory = False)
        self.bkgdf = self.bkgdf[self.bkgdf['BASE_OD_DEPT_DATE'] == int(self.depdate)]

        print('Aggregating dataframes...')
        # Aggregate pwdc and bkg dataframes.
        self.pwdf['BASE_OD_DEPT_DATE'] = self.pwdf['BASE_OD_DEP_DATE']
        self.pwdf = self.pwdf.groupby(['BASE_OD_ORGN','BASE_OD_DSTN',\
                                       'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                       'BASE_OD_DEPT_DATE','POS','FF','BC'])\
                              .agg({'MP': 'mean', 'F': 'mean', 'AD': 'sum', 'SD': 'sum'})\
                              .reset_index()
        self.pwdf['AD'] = self.pwdf['AD'] / 7
        self.pwdf['SD'] = self.pwdf['SD'] / 7
        self.bkgdf = self.bkgdf.groupby(['BASE_OD_ORGN','BASE_OD_DSTN',\
                                         'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                         'BASE_OD_DEPT_DATE','ISO_COUNTRY','SELL_CLS'])\
                               .agg({'REFERENCE': 'count', 'YIELD': 'mean'})\
                               .reset_index()
        self.bkgdf['COUNT'] = self.bkgdf['REFERENCE']

        print('Melting AV dataframe...')
        self.avdf = self.avdf.melt(id_vars = ['ORGN','DSTN','VIA','CC','FLTNUM',\
                                              'OD_DEPT_DATE','OD_DEPT_DOW','SEG_DEPT_DATE',\
                                              'POS','POSTYPE'],\
                                   value_vars = ['J','C','D','I','F','U',\
                                                 'Y','B','H','K','M','P','T','L',\
                                                 'V','S','N','G','A','Q','O','Z','R','W','X','E'],\
                                   var_name = 'CLS', value_name = 'AV') 

        print('Merging dataframes...')
        self.pwdf = self.pwdf.replace(np.nan, '', regex = True)
        self.avdf = self.avdf.replace(np.nan, '', regex = True)
        self.bkgdf = self.bkgdf.replace(np.nan, '', regex = True)
        self.df = self.pwdf.merge(self.avdf, left_on = ['BASE_OD_ORGN','BASE_OD_DSTN',\
                                                        'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                                        'BASE_OD_DEPT_DATE','POS','BC'],\
                                             right_on = ['ORGN','DSTN','CC','FLTNUM',\
                                                         'OD_DEPT_DATE','POS','CLS'],\
                                             how = 'left')
        self.df = self.df.merge(self.bkgdf, left_on = ['BASE_OD_ORGN','BASE_OD_DSTN',\
                                                       'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                                       'BASE_OD_DEPT_DATE','POS','BC'],\
                                            right_on = ['BASE_OD_ORGN','BASE_OD_DSTN',\
                                                        'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                                        'BASE_OD_DEPT_DATE','ISO_COUNTRY','SELL_CLS'],\
                                            how = 'left')
        self.df = self.df[['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OPR_CC','BASE_OPR_FLTNUM',\
                           'BASE_OD_DEPT_DATE','POS','FF','BC','SD','AD','MP','F','AV','COUNT']]
        self.df['COUNT'] = self.df['COUNT'].fillna(0)
        self.df['FF'] = self.df['FF'].fillna('')
        # Join class dataframe.
        clsdf = pd.read_csv('s3://ay-rmp-home/static/clsorder.csv')
        self.df = self.df.merge(clsdf, left_on = ['BC'], right_on = ['CLS'])
        self.df = self.df.sort_values(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                       'BASE_OD_DEPT_DATE','POS','FF','ORDER']) 
       


    def rows(self):
        clss,sds,ads,mps,fs,avs,counts = [],[],[],[],[],[],[]
        porgn,pdstn,pcc,pfltnum,pdepdt,ppos,pff,pbc,psd,pad,pmp,pf,pav,pcount =\
            None,None,None,None,None,None,None,None,None,None,None,None,None,None
        num = 0
        for i,r in self.df.iterrows():
            num += 1
            orgn,dstn,cc,fltnum,depdt,pos,ff,bc,sd,ad,mp,f,av,count =\
                r['BASE_OD_ORGN'],r['BASE_OD_DSTN'],r['BASE_OPR_CC'],r['BASE_OPR_FLTNUM'],\
                r['BASE_OD_DEPT_DATE'],r['POS'],r['FF'],r['BC'],r['SD'],r['AD'],\
                r['MP'],r['F'],r['AV'],r['COUNT']
            if num == 1:
                clss.append(bc)
                sds.append(sd)
                ads.append(ad)
                mps.append(mp)
                fs.append(f)
                avs.append(av)
                counts.append(count)
            elif orgn == porgn and dstn == pdstn and cc == pcc and fltnum == pfltnum and\
               depdt == pdepdt and pos == ppos and ff == pff and ff != '':
                # Fare family continues.
                clss.append(bc)
                sds.append(sd)
                ads.append(ad)
                mps.append(mp)
                fs.append(f)
                avs.append(av)
                counts.append(count)
            else:
                assert len(clss) == len(sds)
                assert len(clss) == len(ads)
                assert len(clss) == len(mps)
                assert len(clss) == len(fs)
                assert len(clss) == len(avs)
                assert len(clss) == len(counts)
                # New fare family.
                sc,sscd,ascd,scyield,mpsc,avsc = '','','','','',''
                bkgcnt = 0
                bkgyieldsum = 0
                gc,sgcd,agcd,gcyield,mpgc = '','','','',''
                for i in range(len(clss)):
                    if avs[i] > 0:
                        sc = clss[i]
                        sscd = sds[i]
                        ascd = ads[i]
                        scyield = fs[i]
                        mpsc = mps[i]
                        avsc = avs[i]
                    bkgcnt += counts[i]     
                    bkgyieldsum += counts[i] * fs[i]               
                    if mps[i] >= 0:
                        gc = clss[i]
                        sgcd = sds[i]
                        agcd = ads[i]
                        gcyield = fs[i]
                        mpgc = mps[i]
                bym = 0
                if bkgcnt > 0:
                    bym = float(bkgyieldsum) / bkgcnt
                yield porgn,pdstn,pcc,pfltnum,pdepdt,ppos,pff,\
                      sc,sscd,ascd,scyield,mpsc,\
                      gc,sgcd,agcd,gcyield,mpgc,\
                      bkgcnt,bym,avsc,self.bkgdate    
                clss   = [bc]
                sds    = [sd]
                ads    = [ad]
                mps    = [mp]
                fs     = [f]
                avs    = [av]
                counts = [count]
            porgn,pdstn,pcc,pfltnum,pdepdt,ppos,pff,pbc,psd,pad,pmp,pf,pav,pcount =\
                orgn,dstn,cc,fltnum,depdt,pos,ff,bc,sd,ad,mp,f,av,count
    

if __name__ == "__main__":
    fardr = FAReader('20181217','20190419')
    fardr.read_dfs()
    with open('out.csv', 'w') as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OPR_CC','BASE_OPR_FLTNUM','BASE_OD_DEPT_DATE',\
                            'POS','FF',\
                            'SC','SSCD','ASCD','SCYIELD','MPSC',\
                            'GC','SGCD','AGCD','GCYIELD','MPGC',\
                            'BKGCNT','BKGYIELD','AVSC','BKGDATE'])  
        for r in fardr.rows():
            csvwriter.writerow(r)

