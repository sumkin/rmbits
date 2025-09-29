import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from joblib import Parallel, delayed
import multiprocessing

from plotly.offline import download_plotlyjs, offline, plot, iplot
import plotly.graph_objs as go
from plotly import tools

from s3utils import *
from emailutils import *

num_processes = multiprocessing.cpu_count()
daysahead = 350
frcstdate = datetime.strftime(datetime.now() - timedelta(days=1), '%Y%m%d')

def prepare_data():
    ######################################
    #
    #  Check that all files are presented.
    #
    ######################################
    frcstyear,frcstmonth,frcstday = frcstdate[:4],frcstdate[4:6],frcstdate[6:8]
    frcstdt = datetime.strptime(frcstdate, '%Y%m%d')

    # We need files: yield, bookings, availability and constrained forecast.
    if not s3yieldfilepresent(frcstdate):
        print 'No yield for ', frcstdate
        exit()
    print 'Yield file found.'
    if not s3boffilepresent(frcstdate):
        print 'No bof file for ', frcstdate
        exit()
    print 'BOF file found.'
    if not s3baffilepresent(frcstdate):
        print 'No baf file for ', frcstdate
        exit()
    print 'BAF file found.'
    if not s3cffilespresent(frcstdate, daysahead):
        print 'Some constrained forecast files miising for', frcstdate
    else:
        print 'CF files found.'

    # Class dataframe.
    clsdf = pd.read_csv('s3://ay-emr-job/static/clsorder.csv').fillna('')
    print 'Class order dataframe shape = ', clsdf.shape

    # Bookings dataframe.
    bkgdf = pd.read_csv('s3://ay-emr-job/nrm/bof/'+frcstyear+'/'+frcstmonth+'/BKG_OD_'+frcstdate+'.csv.gz', low_memory = False).fillna('')
    bkgdf['BASE_OD_ORGN'] = bkgdf['BASE_OD_ORGN'].astype(str)
    bkgdf['BASE_OD_DSTN'] = bkgdf['BASE_OD_DSTN'].astype(str)
    bkgdf['ISO_COUNTRY'] = bkgdf['ISO_COUNTRY'].astype(str)
    bkgdf['SELL_CLS'] = bkgdf['SELL_CLS'].astype(str)
    print 'Booking dataframe shape = ', bkgdf.shape

    # Availability dataframe.
    adf = pd.read_csv('s3://ay-emr-job/nrm/baf/'+frcstyear+'/'+frcstmonth+'/AV_OD_'+frcstdate+'.csv.gz', low_memory = False).fillna('')
    print 'Availability dataframe shape = ', adf.shape

    print 'Reading constrained forecast...'
    def reads3df(depdate):
        try:
            df = pd.read_csv('s3://ay-emr-job/nrm/cf/'+frcstyear+'/'+frcstmonth+'/'+frcstday+\
                             '/cf_'+frcstdate+'_'+depdate+'.csv.gz', low_memory = False).fillna('')
            df = df.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                             'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                             'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                             'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                             'BASE_OD_DEPT_DATE','BASE_SEG_DEP_DATE',\
                             'POS','FF','BC']).agg({'GCC_ARMD': 'sum', 'D': 'sum', 'LPC_D': 'sum',\
                                                    'CREV': 'sum', 'MP': 'mean', 'F': 'mean'}).reset_index()
            df['POSKEY'] = df['BASE_OD_ORGN'].astype(str) + df['BASE_OD_DSTN'].astype(str) +\
                           df['BASE_OPR_CC'].astype(str) + df['BASE_OPR_FLTNUM'].astype(str) +\
                           df['BASE_OD_DEPT_DATE'].astype(str) + df['BASE_SEG_DEP_DATE'].astype(str) + df['POS'].astype(str)
            return df
        except Exception as e:
            print e
            # Fix for missing data.
            df = pd.read_csv('s3://ay-emr-job/nrm/cf/'+frcstyear+'/'+frcstmonth+'/'+frcstday+\
                             '/cf_'+frcstdate+'_'+frcstdate+'.csv.gz', low_memory = False).fillna('')
            df = df.groupby(['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                             'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                             'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                             'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                             'BASE_OD_DEPT_DATE','BASE_SEG_DEP_DATE',\
                             'POS','FF','BC']).agg({'GCC_ARMD': 'sum', 'D': 'sum', 'LPC_D': 'sum',\
                                                    'CREV': 'sum', 'MP': 'mean', 'F': 'mean'}).reset_index()
            df['POSKEY'] = df['BASE_OD_ORGN'].astype(str) + df['BASE_OD_DSTN'].astype(str) +\
                           df['BASE_OPR_CC'].astype(str) + df['BASE_OPR_FLTNUM'].astype(str) +\
                           df['BASE_OD_DEPT_DATE'].astype(str) + df['BASE_SEG_DEP_DATE'].astype(str) + df['POS'].astype(str)
            return df.iloc[0:0]

    depdates = []
    for delta in range(daysahead):
        depdate = frcstdt + timedelta(days = delta)
        depdate = datetime.strftime(depdate, '%Y%m%d')
        depdates.append(depdate)

    cfdfs = Parallel(n_jobs = num_processes - 1)(delayed(reads3df)(depdate) for depdate in depdates)
    return adf,cfdfs,bkgdf,clsdf,frcstdate



def gen_report(orgn_ap, orgn_cntr, orgn_rgn,\
               dstn_ap, dstn_cntr, dstn_rgn,\
               daysahead,\
               adf, cfdfs, bkgdf,clsdf,\
               frcstdate, emails):

    dates = []
    brevs, revs, crevs, mincrevs, avrevs = [], [], [], [], []
    bpaxes, paxes, avpaxes = [], [], []

    frcstdt = datetime.strptime(frcstdate,'%Y%m%d')
    for delta in range(daysahead):
        depdate = frcstdt + timedelta(days = delta)
        depdate = datetime.strftime(depdate, '%Y%m%d')
        dates.append(datetime.strptime(depdate, '%Y%m%d'))
        print depdate

        dadf = adf.loc[adf['OD_DEPT_DATE'] == int(depdate)]
    
        cfdf = cfdfs[delta]

        bkgdfdt = bkgdf.loc[bkgdf['BASE_OD_DEPT_DATE'] == int(depdate)]

        if orgn_ap is not None:
            cfdf = cfdf.loc[cfdf['BASE_OD_ORGN'] == orgn_ap]
            bkgdfdt = bkgdfdt.loc[bkgdfdt['BASE_OD_ORGN'] == orgn_ap]
        if dstn_ap is not None:
            cfdf = cfdf.loc[cfdf['BASE_OD_DSTN'] == dstn_ap]
            bkgdfdt = bkgdfdt.loc[bkgdfdt['BASE_OD_DSTN'] == dstn_ap]
        if orgn_cntr is not None:
            cfdf = cfdf.loc[cfdf['BASE_OD_ORGN_COUNTRY'] == orgn_cntr]
            bkgdfdt = bkgdfdt.loc[bkgdfdt['BASE_OD_ORGN_COUNTRY'] == orgn_cntr]
        if dstn_cntr is not None:
            cfdf = cfdf.loc[cfdf['BASE_OD_DSTN_COUNTRY'] == dstn_cntr]
            bkgdfdt = bkgdfdt.loc[bkgdfdt['BASE_OD_DSTN_COUNTRY'] == dstn_cntr]
        if orgn_rgn is not None:
            cfdf = cfdf.loc[cfdf['BASE_OD_ORGN_REGION'] == orgn_rgn]
            bkgdfdt = bkgdfdt.loc[bkgdfdt['BASE_OD_ORGN_REGION'] == orgn_rgn]
        if dstn_rgn is not None:
            cfdf = cfdf.loc[cfdf['BASE_OD_DSTN_REGION'] == dstn_rgn]
            bkgdfdt = bkgdfdt.loc[bkgdfdt['BASE_OD_DSTN_REGION'] == dstn_rgn]

        # Merge constrained forecast with availability.
        madf = pd.melt(dadf, id_vars = ['ORGN','DSTN','CC','FLTNUM','OD_DEPT_DATE','SEG_DEPT_DATE','POS'],\
                             value_vars = ['J','C','D','F','U',\
                                           'Y','B','H','K','M','P','T','L','V','S','N','G','A','Q','O','Z','R','W','X','E'],\
                             var_name = 'BC',\
                             value_name = 'AV')
        madf = madf.merge(clsdf, left_on = ['BC'], right_on = ['CLS'], how = 'left')

        df = cfdf.merge(madf, left_on = ['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                         'BASE_OD_DEPT_DATE','BASE_SEG_DEP_DATE','POS','BC'],\
                              right_on = ['ORGN','DSTN','CC','FLTNUM','OD_DEPT_DATE','SEG_DEPT_DATE','POS','BC'], how = 'left')
        df = df[['BASE_OD_ORGN','BASE_OD_DSTN','BASE_OPR_CC','BASE_OPR_FLTNUM',\
                 'BASE_OD_DEPT_DATE','BASE_SEG_DEP_DATE','POS','FF','POSKEY','BC','D','MP','F','AV','ORDER']]
        df = df.sort_values(by = ['POSKEY','FF','ORDER'], ascending = False)
 
        avrev, avtaken = 0, 0
        taken, rev = 0, 0
        prevk = None
        prevav = 0

        for idx, r in df.iterrows():
            k = r['POSKEY']
            if k == prevk:
                # POS continues.
                t = min(r['D'], max(0, r['AV'] - taken))
                taken += t
                rev += r['MP'] * t
            else:
                # New POS.
                avrev += rev
                avtaken += taken
 
                taken = min(r['D'], r['AV'])
                rev = r['MP'] * taken
            prevk = k
            prevav = r['AV']

        avrevs.append(avrev)
        avpaxes.append(avtaken)

        ncrev = cfdf['CREV'].sum()
        npaxes = cfdf['D'].sum()

        crevs.append(ncrev)
        paxes.append(npaxes)

        bpaxes.append(bkgdfdt.shape[0])
        brevs.append(bkgdfdt['YIELD'].sum())

    # Draw figures.
    brev_data = go.Scatter(x = dates, y = brevs,\
                           mode = 'lines', fill = 'tozeroy',\
                           line = dict(color = ('rgb(205, 12, 24)'), width = 3),\
                           name = 'Booked Revenue')
    crev_data = go.Scatter(x = dates, y = [e1+e2 for e1,e2 in zip(crevs,brevs)],\
                           mode = 'lines', fill = 'tozeroy',\
                           line = dict(color = ('rgb(250, 75, 75)'), width = 2),\
                           name = 'Coming Revenue')
    avrev_data = go.Scatter(x = dates, y = [e1+e2 for e1,e2 in zip(brevs,avrevs)],\
                            mode = 'lines',\
                            line = dict(color = ('rgb(128, 0, 0)'), width = 3),\
                            name = 'Availability Revenue')

    bpaxes_data = go.Scatter(x = dates, y = bpaxes,
                             mode = 'lines', fill = 'tozeroy',\
                             line = dict(color = ('rgb(0, 153, 51)'), width = 3),\
                             name = 'Booked Paxes')
    paxes_data = go.Scatter(x = dates, y = [e1+e2 for e1,e2 in zip(paxes,bpaxes)],\
                            mode = 'lines', fill = 'tozeroy',\
                            line = dict(color = ('rgb(102, 250, 102)'), width = 2),\
                            name = 'Coming Paxes')
    avpaxes_data = go.Scatter(x = dates, y = [e1+e2 for e1,e2 in zip(bpaxes,avpaxes)],\
                              mode = 'lines',\
                              line = dict(color=('rgb(0, 128, 0)'), width = 3),\
                              name = 'Availability Paxes')

    tfrom, tto = '', ''
    if orgn_ap is not None:
        tfrom = orgn_ap
    if dstn_ap is not None:
        tto = dstn_ap
    if orgn_cntr is not None:
        tfrom = orgn_cntr
    if dstn_cntr is not None:
        tto = dstn_cntr
    if orgn_rgn is not None:
        tfrom = orgn_rgn
    if dstn_rgn is not None:
        tto = dstn_rgn

    fig = tools.make_subplots(rows = 3, cols = 1, specs = [[{}], [{}], [{}]],\
                              shared_xaxes = True, shared_yaxes = False,\
                              vertical_spacing = 0.05)
    fig.append_trace(brev_data, 1, 1)
    fig.append_trace(crev_data, 1, 1)
    fig.append_trace(avrev_data, 1, 1)

    fig.append_trace(bpaxes_data, 2, 1)
    fig.append_trace(paxes_data, 2, 1)
    fig.append_trace(avpaxes_data, 2, 1)

    fig['layout'].update(title = 'Constrained Revenue for ' + tfrom + '-' + tto)

    lclfname = '/home/ay49514/tmp/constr_frcst_' + tfrom + '-' + tto + '_' + frcstdate + '.html'
    plot(fig, filename = lclfname, auto_open = False)
    rmtfname = 's3://ay-emr-job/nrm/reporting/cf/'+frcstdate[:4]+'/'+frcstdate[4:6]+'/'+frcstdate[6:8]+'/'+\
               'constr_frcst_' + tfrom + '-' + tto + '_' + frcstdate + '.html'
    copy2s3(lclfname, rmtfname)

    '''
    # Send email.
    for email in emails:
        sbj = 'Constrained Forecast ' + tfrom + '-' + tto + ' for ' + frcstdate
        txt = 'Find report attached.'
        try:
            send_multipart('fedor.nikitin@finnair.com', email, sbj, txt, [lclfname])
        except Exception as e:
            print e
            # Sleep and try again.
            time.sleep(5)
            send_multipart('fedor.nikitin@finnair.com', email, sbj, txt, [lclfname]) 
    '''

    # Clean-up.
    subprocess.check_output(['rm',lclfname])


if __name__ == "__main__":

    if len(sys.argv) == 1:
        adf,cfdfs,bkgdf,clsdf,frcstdate = prepare_data()
        ###################################################################################################
        #
        #  Generate default reports.
        #
        ###################################################################################################
        gen_report(None,None,'EUROPE','BKK',None,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report('BKK',None,None,None,None,'EUROPE',350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report(None,None,'EUROPE','SIN',None,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report('SIN',None,None,None,None,'EUROPE',350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report(None,'FI',None,'BKK',None,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report('BKK',None,None,None,'FI',None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report(None,'SE',None,'BKK',None,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report('BKK',None,None,None,'SE',None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report(None,'GB',None,'BKK',None,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report('BKK',None,None,None,'GB',None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report(None,'NO',None,'BKK',None,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report('BKK',None,None,None,'NO',None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report(None,'DE',None,'BKK',None,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report('BKK',None,None,None,'DE',None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report(None,'NL',None,'BKK',None,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report('BKK',None,None,None,'NL',None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report(None,'GB',None,'SIN',None,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report('SIN',None,None,None,'GB',None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report(None,'NO',None,'SIN',None,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report('SIN',None,None,None,'NO',None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report(None,'DE',None,'SIN',None,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report('SIN',None,None,None,'DE',None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report(None,'FI',None,None,'GB',None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report(None,'GB',None,None,'FI',None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report(None,'GB',None,None,'HK',None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])
        gen_report(None,'HK',None,None,'GB',None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['tatu.seppa@finnair.com','fedor.nikitin@finnair.com'])


        gen_report(None,None,None,None,None,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,['fedor.nikitin@finnair.com'])
        gen_report(None,None,'EUROPE',None,None,'ASIA',350,adf,cfdfs,bkgdf,clsdf,frcstdate,['fedor.nikitin@finnair.com'])
        gen_report(None,None,'ASIA',None,None,'EUROPE',350,adf,cfdfs,bkgdf,clsdf,frcstdate,['fedor.nikitin@finnair.com'])
        gen_report(None,None,'EUROPE',None,None,'EUROPE',350,adf,cfdfs,bkgdf,clsdf,frcstdate,['fedor.nikitin@finnair.com'])
        gen_report(None,None,'EUROPE',None,None,'NAMER',350,adf,cfdfs,bkgdf,clsdf,frcstdate,['fedor.nikitin@finnair.com'])
        gen_report(None,None,'NAMER',None,None,'EUROPE',350,adf,cfdfs,bkgdf,clsdf,frcstdate,['fedor.nikitin@finnair.com'])

    elif len(sys.argv) == 4:
        adf,cfdfs,bkgdf,clsdf,frcstdate = prepare_data()
        orgn = sys.argv[1]
        dstn = sys.argv[2]
        email = sys.argv[3]
        
        if len(orgn) == 3 and len(dstn) == 3:
            print 'Airport to airport'
            gen_report(orgn,None,None,dstn,None,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,[email])
        elif len(orgn) == 3 and len(dstn) == 2:
            print 'Airport to country'
            gen_report(orgn,None,None,None,dstn,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,[email])
        elif len(orgn) == 2 and len(dstn) == 3:
            print 'Country to airport'
            gen_report(None,orgn,None,dstn,None,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,[email])
        elif len(orgn) == 2 and len(dstn) == 2:
            print 'Country to country'
            gen_report(None,orgn,None,None,dstn,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,[email])
        else:
            if len(orgn) > 3:
                if len(dstn) == 3:
                    print 'Region to airport'
                    gen_report(None,None,orgn,dstn,None,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,[email])
                elif len(dstn) == 2:
                    print 'Region to country'
                    gen_report(None,None,orgn,None,dstn,None,350,adf,cfdfs,bkgdf,clsdf,frcstdate,[email])
            elif len(dstn) > 3:
                if len(orgn) == 3:
                    print 'Airport to region'
                    gen_report(orgn,None,None,None,None,dstn,350,adf,cfdfs,bkgdf,clsdf,frcstdate,[email])
                elif len(orgn) == 2:
                    print 'Country to region'
                    gen_report(None,orgn,None,None,None,dstn,350,adf,cfdfs,bkgdf,clsdf,frcstdate,[email])




