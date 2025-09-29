import json
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, request, render_template, send_from_directory

template_dir = "/home/ay49514/rmbits/src/reporting/templates"
app = Flask(__name__, template_folder = template_dir)

from pyairport.airport import Airport
from emailutils import *

dows = ['All','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

class PAReport:


    def __init__(self, dfrom, dto):
        self.dates = []
        if dfrom is None and dto is None:
            dt = datetime.now()
            dow = dt.isocalendar()[2]
            while dow != 7:
                dt = dt - timedelta(days = 1)
                dow = dt.isocalendar()[2]
            self.year, self.week_num, dow = dt.isocalendar()
            self.dates = []
            for i in range(0,7):
                self.dates.append(datetime.strftime(dt, "%Y%m%d"))
                dt = dt - timedelta(days = 1)
            self.dates.reverse()
        else:
            self.year, self.week_num, dow = None, None, None
            dfromdt = datetime.strptime(dfrom, "%Y%m%d")
            dtodt = datetime.strptime(dto, "%Y%m%d")
            dt = dfromdt
            while dt <= dtodt:
                self.dates.append(datetime.strftime(dt, "%Y%m%d"))
                dt = dt + timedelta(days = 1)


    def dfrom(self):
        return self.dates[0]


    def dto(self):
        return self.dates[len(self.dates)-1]


    def read_dfs(self):
        # Read bookings.
        print 'Reading bookings...'
        self.bof = None
        for date in self.dates:
            n_date = datetime.strftime(datetime.strptime(date,'%Y%m%d') + timedelta(days=1),'%Y%m%d')
            print date, n_date
            path = 's3://ay-emr-job/nrm/bof/'+n_date[:4]+'/'+n_date[4:6]+'/BKG_OD_'+n_date+'.csv.gz'
            if self.bof is None:
                self.bof = pd.read_csv(path, low_memory = False)
                self.bof = self.bof.loc[self.bof['DAYSPRIOR'] == -1]
                self.bof['DOW'] = pd.to_datetime(self.bof['BASE_OD_DEPT_DATE'], format='%Y%m%d').dt.weekday_name
            else:
                df = pd.read_csv(path, low_memory = False)
                df = df.loc[df['DAYSPRIOR'] == -1]
                df['DOW'] = pd.to_datetime(df['BASE_OD_DEPT_DATE'], format='%Y%m%d').dt.weekday_name
                self.bof = self.bof.append(df)
        print "self.bof['DOW'].unique() = ", self.bof['DOW'].unique()

        # Read inventory.
        print 'Reading inventory...'
        self.bif = None
        for date in self.dates:
            n_date = datetime.strftime(datetime.strptime(date,'%Y%m%d') + timedelta(days=1),'%Y%m%d')
            print date, n_date
            path = 's3://ay-emr-job/nrm/bif/'+n_date[:4]+'/'+n_date[4:6]+'/INV_'+n_date+'.csv.gz'
            if self.bif is None:
                self.bif = pd.read_csv(path, low_memory = False)
                self.bif = self.bif.loc[self.bif['CC'] == 'AY']
                self.bif = self.bif.loc[self.bif['DAYSPRIOR'] == -1]
                self.bif = self.bif.loc[self.bif['CAPO'] < 900]
                self.bif['DOW'] = pd.to_datetime(self.bif['DEPDT'], format='%Y%m%d').dt.weekday_name
            else:
                df = pd.read_csv(path, low_memory = False)
                df = df.loc[df['CC'] == 'AY']
                df = df.loc[df['DAYSPRIOR'] == -1]
                df = df.loc[df['CAPO'] < 900]
                df['DOW'] = pd.to_datetime(df['DEPDT'], format='%Y%m%d').dt.weekday_name
                self.bif = self.bif.append(df)
        print "self.bif['DOW'].unique() = ", self.bif['DOW'].unique()

        # Read pag dataframes.
        print 'Reading post analysis groups...'
        self.pag = None
        for date in self.dates:
            print date 
            path = 's3://ay-emr-job/nrm/pa/'+date[:4]+'/'+date[4:6]+'/pag_'+date+'.csv.gz'
            if self.pag is None:
                self.pag = pd.read_csv(path, low_memory = False)
                self.pag = self.pag.loc[self.pag['BC'] == 'G']
                self.pag['DOW'] = pd.to_datetime(self.pag['BASE_OD_DEPT_DATE'], format='%Y%m%d').dt.weekday_name
            else:
                df = pd.read_csv(path, low_memory = False)
                df = df.loc[df['BC'] == 'G']
                df['DOW'] = pd.to_datetime(df['BASE_OD_DEPT_DATE'], format='%Y%m%d').dt.weekday_name
                self.pag = self.pag.append(df)
        print "self.pag['DOW'].unique() = ", self.pag['DOW'].unique() 


    def num_pax(self):
        return self.bof.shape[0]


    def rev(self):
        return int(self.bof['YIELD'].sum())


    def yld(self):
        return round(self.bof['YIELD'].mean(), 2)


    def p2p_bkg_ratio(self):
        totbkg = self.bof.shape[0]
        p2pbkg = self.bof[self.bof['BASE_OD_VIA'].isnull()].shape[0]
        return round(float(p2pbkg) / totbkg, 2)


    def p2p_rev_ratio(self):
        totrev = self.bof['YIELD'].sum()
        p2prev = self.bof[self.bof['BASE_OD_VIA'].isnull()]['YIELD'].sum()
        return round(float(p2prev) / totrev, 2)


    def empty_seats_ratio(self):
        self.bif = self.bif.assign(ESEATS = lambda x: x.CAPO - x.BKC)
        eseats = self.bif['ESEATS'].sum()    
        totseats = self.bif['CAPO'].sum()
        return round(float(eseats) / totseats, 2)


    def groups_bkg_ratio(self):
        totbkg = self.bof.shape[0]
        groupsbkg = self.bof[self.bof['SELL_CLS'] == 'G'].shape[0]
        return round(float(groupsbkg) / totbkg, 2)


    def groups_rev_ratio(self):
        totrev = self.bof['YIELD'].sum()
        groupsrev = self.bof[self.bof['SELL_CLS'] == 'G']['YIELD'].sum()
        return round(float(groupsrev) / totrev, 2)

    '''
    def osgroups_lines(self):
        df = self.pag.groupby(['BASE_OD_ORGN','BASE_OD_DSTN'])\
                     .agg({'MP': 'mean', 'AMD': 'sum', 'LPC_AMD': 'sum'}).reset_index()
        df = df.loc[df['AMD'] > 5]
        df = df[(df['AMD'] > df['LPC_AMD'] + 5)]
        df['DIFF'] = df['AMD'] - df['LPC_AMD']
        df = df[df['DIFF'] > 0].sort_values(by = ['BASE_OD_ORGN','BASE_OD_DSTN','DIFF'], ascending = False)
        diffmax = df['DIFF'].max()
     
        lines = []
        for i, r in df.iterrows():
            orgn = r['BASE_OD_ORGN']
            dstn = r['BASE_OD_DSTN']
            ap_orgn = Airport(orgn)
            ap_dstn = Airport(dstn)
            line = []
            p = {}
            p['latitude'] = ap_orgn.get_latitude()
            p['longitude'] = ap_orgn.get_longitude()
            line.append(p)
            p = {}
            p['latitude'] = ap_dstn.get_latitude()
            p['longitude'] = ap_dstn.get_longitude()
            line.append(p)
            lines.append(line)
        return lines
    '''

    def groups_pos(self):
        pdf = self.pag.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','POS','DOW'])\
                      .agg({'MP': 'mean', 'AMD': 'sum', 'LPC_AMD': 'sum'}).reset_index()
        bdf = self.bof[self.bof['SELL_CLS'] == 'G'].groupby(['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','DOW'])\
                                                   .agg({'REFERENCE': 'count'}).reset_index()
        df = bdf.merge(pdf, left_on = ['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','DOW'],\
                            right_on = ['BASE_OD_ORGN','BASE_OD_DSTN','POS','DOW'],\
                            how = 'left')
        df['POS'].fillna('', inplace = True)
        df['LPC_AMD'].fillna(0, inplace = True)
        df['DIFF'] = df['REFERENCE'] - df['LPC_AMD']

        res = {}
        for dow in dows:
            if dow == 'All':
                ldf = df.groupby(['ISO_COUNTRY']).agg({'DIFF': 'sum'}).reset_index()
                result = []
                maxabsval = 0
                for i, r in ldf.iterrows():
                    pos = r['ISO_COUNTRY']
                    val = r['DIFF']
                    maxabsval = max(val, maxabsval)
                    result.append({'id': pos, 'pos': pos, 'value': val})
                res['All'] = [maxabsval, result]
            else:
                ldf = df.loc[df['DOW'] == dow].groupby(['ISO_COUNTRY']).agg({'DIFF': 'sum'}).reset_index()
                result = []
                maxabsval = 0
                for i, r in ldf.iterrows():
                    pos = r['ISO_COUNTRY']
                    val = r['DIFF']
                    maxabsval = max(val, maxabsval)
                    result.append({'id': pos, 'pos': pos, 'value': val})
                res[dow] = [maxabsval, result]
        return res


    def osgroups_pos_table(self):
        pdf = self.pag.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','POS','DOW'])\
                      .agg({'MP': 'mean', 'AMD': 'sum', 'LPC_AMD': 'sum'}).reset_index()
        bdf = self.bof[self.bof['SELL_CLS'] == 'G'].groupby(['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','DOW'])\
                                                   .agg({'REFERENCE': 'count'}).reset_index()     
 
        df = bdf.merge(pdf, left_on = ['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','DOW'],\
                            right_on = ['BASE_OD_ORGN','BASE_OD_DSTN','POS','DOW'],\
                            how = 'left')
        df['POS'].fillna('', inplace = True)
        df['LPC_AMD'].fillna(0, inplace = True)
        df['DIFF'] = df['REFERENCE'] - df['LPC_AMD']

        res = {}
        for dow in dows:
            if dow == 'All':
                ldf = df.groupby(['ISO_COUNTRY']).agg({'DIFF': 'sum'}).reset_index()
                ldf = ldf.loc[ldf['DIFF'] >= 0]
                ldf = ldf.sort_values(by = 'DIFF', ascending = False)
                ldf.columns = ['POS','DIFF']
                ldf.DIFF = ldf.DIFF.astype(int)
                res['All'] = ldf.head(23).to_html(index = False, classes = 'osgroups_pos_table', border = 0)
            else:
                ldf = df.loc[df['DOW'] == dow].groupby(['ISO_COUNTRY']).agg({'DIFF': 'sum'}).reset_index()
                ldf = ldf.loc[ldf['DIFF'] >= 0]
                ldf = ldf.sort_values(by = 'DIFF', ascending = False)
                ldf.columns = ['POS','DIFF']
                ldf.DIFF = ldf.DIFF.astype(int)
                res[dow] = ldf.head(23).to_html(index = False, classes = 'osgroups_pos_table', border = 0)
        return res


    def usgroups_pos_table(self):
        pdf = self.pag.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','POS','DOW'])\
                      .agg({'MP': 'mean', 'AMD': 'sum', 'LPC_AMD': 'sum'}).reset_index()
        bdf = self.bof[self.bof['SELL_CLS'] == 'G'].groupby(['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','DOW'])\
                                                   .agg({'REFERENCE': 'count'}).reset_index()

        df = bdf.merge(pdf, left_on = ['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','DOW'],\
                            right_on = ['BASE_OD_ORGN','BASE_OD_DSTN','POS','DOW'],\
                            how = 'left')
        df['POS'].fillna('', inplace = True)
        df['LPC_AMD'].fillna(0, inplace = True)
        df['DIFF'] = df['REFERENCE'] - df['LPC_AMD']

        res = {}
        for dow in dows:
            if dow == 'All':
                ldf = df.groupby(['ISO_COUNTRY']).agg({'DIFF': 'sum'}).reset_index()
                ldf = ldf.loc[ldf['DIFF'] < 0]
                ldf = ldf.sort_values(by = 'DIFF', ascending = True)
                ldf.columns = ['POS','DIFF']
                ldf.DIFF = ldf.DIFF.astype(int)
                res['All'] = ldf.head(23).to_html(index = False, classes = 'usgroups_pos_table', border = 0) 
            else:
                ldf = df.loc[df['DOW'] == dow].groupby(['ISO_COUNTRY']).agg({'DIFF': 'sum'}).reset_index()
                ldf = ldf.loc[ldf['DIFF'] < 0]
                ldf = ldf.sort_values(by = 'DIFF', ascending = True)
                ldf.columns = ['POS','DIFF']
                ldf.DIFF = ldf.DIFF.astype(int)
                res[dow] = ldf.head(23).to_html(index = False, classes = 'usgroups_pos_table', border = 0)
        return res


    def osgroups_ond_pos_tables(self):
        pdf = self.pag.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','POS','DOW'])\
                      .agg({'MP': 'mean', 'AMD': 'sum', 'LPC_AMD': 'sum'}).reset_index()
        gbdf = self.bof[self.bof['SELL_CLS'] == 'G'].groupby(['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','DOW'])\
                                                    .agg({'REFERENCE': 'count', 'YIELD': 'mean'}).reset_index()
        ibdf = self.bof[self.bof['SELL_CLS'] != 'G'].groupby(['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','DOW'])\
                                                    .agg({'REFERENCE': 'count', 'YIELD': 'mean'}).reset_index()
        bdf = gbdf.merge(ibdf, left_on = ['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','DOW'],\
                               right_on = ['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','DOW'],\
                               how = 'left',\
                               suffixes = ['g','i'])
        df = bdf.merge(pdf, left_on = ['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','DOW'],\
                            right_on = ['BASE_OD_ORGN','BASE_OD_DSTN','POS','DOW'],\
                            how = 'left')
        df['POS'].fillna('', inplace = True)
        df['LPC_AMD'].fillna(0, inplace = True)
        df['DIFF'] = df['REFERENCEg'] - df['LPC_AMD']
        df = df.loc[df['DIFF'] >= 0]

        res = {}
        for dow in dows:
            result = {}
            for pos in df['ISO_COUNTRY'].unique():
                if dow == 'All':
                    ldf = df.loc[df['ISO_COUNTRY'] == pos]
                    ldf = ldf.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY'])\
                             .agg({'YIELDg': 'mean', 'YIELDi': 'mean', 'AMD': 'sum',\
                                   'REFERENCEg': 'sum', 'REFERENCEi': 'sum',\
                                   'LPC_AMD': 'sum', 'DIFF': 'sum'}).reset_index()
                else:
                    ldf = df.loc[(df['ISO_COUNTRY'] == pos) & (df['DOW'] == dow)]
                ldf = ldf.sort_values(by = 'DIFF', ascending = False)
                ldf = ldf[['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','YIELDg','YIELDi','AMD','REFERENCEg','REFERENCEi','LPC_AMD','DIFF']]
                ldf.columns = ['ORGN','DSTN','POS','GF','IF','DMD','GTKN','ITKN','OPT','DIFF']
                ldf.fillna(0, inplace = True)
                ldf.OPT = ldf.OPT.astype(int)
                ldf.DMD = ldf.DMD.astype(int)
                ldf.GF = ldf.GF.astype(int)
                ldf.IF = ldf.IF.astype(int)
                ldf.GTKN = ldf.GTKN.astype(int)
                ldf.ITKN = ldf.ITKN.astype(int)
                ldf.DIFF = ldf.DIFF.astype(int)
                result[pos] = ldf.head(23).to_html(index = False, classes = 'osgroups_table', border = 0)
            res[dow] = result
        return res


    def usgroups_ond_pos_tables(self):
        pdf = self.pag.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','POS','DOW'])\
                      .agg({'MP': 'mean', 'AMD': 'sum', 'LPC_AMD': 'sum'}).reset_index()
        gbdf = self.bof[self.bof['SELL_CLS'] == 'G'].groupby(['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','DOW'])\
                                                    .agg({'REFERENCE': 'count', 'YIELD': 'mean'}).reset_index()
        ibdf = self.bof[self.bof['SELL_CLS'] != 'G'].groupby(['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','DOW'])\
                                                    .agg({'REFERENCE': 'count', 'YIELD': 'mean'}).reset_index()
      
    
        bdf = gbdf.merge(ibdf, left_on = ['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','DOW'],\
                               right_on = ['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','DOW'],\
                               how = 'left',\
                               suffixes = ['g','i'])
        df = bdf.merge(pdf, left_on = ['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','DOW'],\
                            right_on = ['BASE_OD_ORGN','BASE_OD_DSTN','POS','DOW'],\
                            how = 'left')
        df['POS'].fillna('', inplace = True)
        df['LPC_AMD'].fillna(0, inplace = True)
        df['DIFF'] = df['REFERENCEg'] - df['LPC_AMD']
        df = df.loc[df['DIFF'] < 0]

        res = {}
        for dow in dows:
            result = {}
            for pos in df['ISO_COUNTRY'].unique():
                if dow == 'All':
                    ldf = df.loc[df['ISO_COUNTRY'] == pos]
                    ldf = ldf.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY'])\
                             .agg({'YIELDg': 'mean', 'YIELDi': 'mean', 'AMD': 'sum',\
                                   'REFERENCEg': 'sum', 'REFERENCEi': 'sum',\
                                   'LPC_AMD': 'sum', 'DIFF': 'sum'}).reset_index()
                else:
                    ldf = df.loc[(df['ISO_COUNTRY'] == pos) & (df['DOW'] == dow)]
                ldf = ldf.sort_values(by = 'DIFF')
                ldf = ldf[['BASE_OD_ORGN','BASE_OD_DSTN','ISO_COUNTRY','YIELDg','YIELDi','AMD','REFERENCEg','REFERENCEi','LPC_AMD','DIFF']]
                ldf.columns = ['ORGN','DSTN','POS','GF','IF','DMD','GTKN','ITKN','OPT','DIFF']
                ldf.fillna(0, inplace = True)
                ldf.OPT = ldf.OPT.astype(int)
                ldf.DMD = ldf.DMD.astype(int)
                ldf.GF = ldf.GF.astype(int)
                ldf.IF = ldf.IF.astype(int)
                ldf.GTKN = ldf.GTKN.astype(int)
                ldf.ITKN = ldf.ITKN.astype(int)
                ldf.DIFF = ldf.DIFF.astype(int)
                result[pos] = ldf.head(23).to_html(index = False, classes = 'usgroups_table', border = 0)
            res[dow] = result
        return res


if __name__ == "__main__":   
    par = PAReport('20180801','20180830')
    par.read_dfs()

    tpl = "pareport.html"

    dfrom = par.dfrom()
    dto = par.dto()
    num_pax = par.num_pax()
    rev = par.rev()
    yld = par.yld()
    print 'p2p bkg ratio...'
    p2p_bkg_ratio = par.p2p_bkg_ratio()
    print 'p2p rev ratio...'
    p2p_rev_ratio = par.p2p_rev_ratio()
    print 'empty seats ratio...'
    empty_seats_ratio = par.empty_seats_ratio()
    print 'bkg ratio...'
    groups_bkg_ratio = par.groups_bkg_ratio()
    print 'rev ratio...'
    groups_rev_ratio = par.groups_rev_ratio()

    groups_pos = par.groups_pos()
    print 'os pos table...'
    osgroups_pos_table = par.osgroups_pos_table()
    print 'osgroups pos table...'
    usgroups_pos_table = par.usgroups_pos_table()
    print 'osgroups ond pos tables...'
    osgroups_ond_pos_tables = par.osgroups_ond_pos_tables()
    print 'usgroups ond pos tables...'
    usgroups_ond_pos_tables = par.usgroups_ond_pos_tables()

    with app.app_context():
        html = render_template(tpl,\
                               year = '',\
                               week_num = '',\
                               dfrom = dfrom,\
                               dto = dto,\
                               num_pax = num_pax,\
                               rev = rev,\
                               yld = yld,\
                               p2p_bkg_ratio = p2p_bkg_ratio,\
                               p2p_rev_ratio = p2p_rev_ratio,\
                               empty_seats_ratio = empty_seats_ratio,\
                               groups_bkg_ratio = groups_bkg_ratio,\
                               groups_rev_ratio = groups_rev_ratio,\
                               groups_pos = groups_pos,\
                               osgroups_pos_table = osgroups_pos_table,\
                               usgroups_pos_table = usgroups_pos_table,\
                               osgroups_ond_pos_tables = osgroups_ond_pos_tables,\
                               usgroups_ond_pos_tables = usgroups_ond_pos_tables)
        sbj = "post analysis"
        body = "find report attached"
        fname = "/home/ay49514/tmp/pa.html"
        with open(fname, 'w') as fout:
            fout.write(html)
        send_multipart("fedor.nikitin@finnair.com",\
                       "fedor.nikitin@finnair.com",\
                       sbj, body, [fname])




