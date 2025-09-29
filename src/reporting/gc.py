import pandas as pd
from datetime import datetime, timedelta

from heatmap import *
from s3utils import *
from emailutils import *


def produce_country_7(country, dpl, dph):
    # Read dataframes.
   
    print 'Reading dataframes...'
    dt = datetime.now()
    for i in range(7):
        print i,
        dt = dt - timedelta(days = 1)
        prevdt = dt - timedelta(days = 1)
        dts = datetime.strftime(dt, '%Y%m%d')
        prevdts = datetime.strftime(prevdt, '%Y%m%d')
        df = pd.read_csv('s3://ay-emr-job/nrm/bcd/'+dts[:4]+'/'+dts[4:6]+'/cnld_'+prevdts+'_'+dts+'.csv.gz', low_memory = False).fillna('')
        df = df.loc[df['ISO_COUNTRY'] == country]
        dfg = df.loc[(df['SELL_CLS'] == 'G') & (df['DAYSPRIOR'] >= dpl) & (df['DAYSPRIOR'] <= dph)]
        if i == 0:
            df7 = dfg
        else:
            df7 = df7.append(dfg)

        # Read booking dataframe.
        bdf = pd.read_csv('s3://ay-emr-job/nrm/bof/'+dts[:4]+'/'+dts[4:6]+'/BKG_OD_'+dts+'.csv.gz', low_memory = False).fillna('')
        bdf = bdf.loc[bdf['ISO_COUNTRY'] == country]
        bdfg = bdf.loc[(bdf['SELL_CLS'] == 'G') & (bdf['DAYSPRIOR'] >= dpl) & (bdf['DAYSPRIOR'] <= dph)]
        if i == 0:
            bdf7 = bdfg
        else:
            bdf7 = bdf7.append(bdfg)

    df7 = df7.groupby(['BASE_OD_ORGN_COUNTRY','BASE_OD_DSTN_COUNTRY']).REFERENCE.nunique().reset_index()
    #df7['COUNT'] = df7['REFERENCE']

    bdf7 = bdf7.groupby(['BASE_OD_ORGN_COUNTRY','BASE_OD_DSTN_COUNTRY']).REFERENCE.nunique().reset_index()
    #bdf7['COUNT'] = bdf7['REFERENCE']
    print

    orgn_cntr = list(df7['BASE_OD_ORGN_COUNTRY'].unique())
    dstn_cntr = list(df7['BASE_OD_DSTN_COUNTRY'].unique())
    orgn_cntr = sorted(orgn_cntr, reverse = True)
    dstn_cntr = sorted(dstn_cntr, reverse = True)

    if len(orgn_cntr) == 0 or len(dstn_cntr) == 0:
        return ''

    print 'Producing data...'
    xnames = orgn_cntr
    ynames = dstn_cntr
    counts = np.zeros((len(orgn_cntr), len(dstn_cntr)))
    percs = np.zeros((len(orgn_cntr), len(dstn_cntr)))
    for i,orgn in enumerate(orgn_cntr):
        for j,dstn in enumerate(dstn_cntr):
            try:
                counts[i,j] = df7[(df7['BASE_OD_ORGN_COUNTRY'] == orgn) &\
                                  (df7['BASE_OD_DSTN_COUNTRY'] == dstn)]['REFERENCE'].iloc[0]
                tot = bdf7[(bdf7['BASE_OD_ORGN_COUNTRY'] == orgn) &\
                           (bdf7['BASE_OD_DSTN_COUNTRY'] == dstn)]['REFERENCE'].iloc[0]
                percs[i,j] = int(100 * float(counts[i,j]) / tot)
            except:
                counts[i,j] = 0
                percs[i,j] = 0

    print 'Making plot...'
    maxcount = np.log(df7['REFERENCE'].max())
    title = 'Group pax from ' + country + ' cancelled in ' + str(dpl) + ' ... ' + str(dph) + ' days prior departure for last 7 days'
    html = heatmap(xnames, ynames, counts, percs, maxcount, 'red', title, 'Group pax cancellations ' + country)
    return html


def produce_region_7(region, dpl, dph):
    # Read data frames.

    print 'Reading dataframes... '
    dt = datetime.now()
    for i in range(7):
        print i,
        dt = dt - timedelta(days = 1)
        prevdt = dt - timedelta(days = 1)
        dts = datetime.strftime(dt, '%Y%m%d')
        prevdts = datetime.strftime(prevdt, '%Y%m%d')
        df = pd.read_csv('s3://ay-emr-job/nrm/bcd/'+dts[:4]+'/'+dts[4:6]+'/cnld_'+prevdts+'_'+dts+'.csv.gz', low_memory = False).fillna('')
        df = df.loc[df['ISO_REGION'] == region]
        dfg = df.loc[(df['SELL_CLS'] == 'G') & (df['DAYSPRIOR'] >= dpl) & (df['DAYSPRIOR'] <= dph)]
        if i == 0:
            df7 = dfg
        else:
            df7 = df7.append(dfg)

        # Read booking dataframe.
        bdf = pd.read_csv('s3://ay-emr-job/nrm/bof/'+dts[:4]+'/'+dts[4:6]+'/BKG_OD_'+dts+'.csv.gz', low_memory = False).fillna('')
        bdf = bdf.loc[bdf['ISO_REGION'] == region]
        bdfg = bdf.loc[(bdf['SELL_CLS'] == 'G') & (bdf['DAYSPRIOR'] >= dpl) & (bdf['DAYSPRIOR'] <= dph)]
        if i == 0:
            bdf7 = bdfg
        else:
            bdf7 = bdf7.append(bdfg)

    df7 = df7.groupby(['BASE_OD_ORGN_COUNTRY','BASE_OD_DSTN_COUNTRY']).REFERENCE.nunique().reset_index()
    #df7['COUNT'] = df7['REFERENCE']

    bdf7 = bdf7.groupby(['BASE_OD_ORGN_COUNTRY','BASE_OD_DSTN_COUNTRY']).REFERENCE.nunique().reset_index()
    #bdf7['COUNT'] = bdf7['REFERENCE']
    print 

    orgn_cntr = list(df7['BASE_OD_ORGN_COUNTRY'].unique())
    dstn_cntr = list(df7['BASE_OD_DSTN_COUNTRY'].unique())
    orgn_cntr = sorted(orgn_cntr, reverse = True)
    dstn_cntr = sorted(dstn_cntr, reverse = True)       

    print 'Producing data...'
    xnames = orgn_cntr
    ynames = dstn_cntr
    counts = np.zeros((len(orgn_cntr), len(dstn_cntr)))
    percs = np.zeros((len(orgn_cntr), len(dstn_cntr)))
    for i,orgn in enumerate(orgn_cntr):
        for j,dstn in enumerate(dstn_cntr):
            try:
                counts[i,j] = df7[(df7['BASE_OD_ORGN_COUNTRY'] == orgn) &\
                                  (df7['BASE_OD_DSTN_COUNTRY'] == dstn)]['REFERENCE'].iloc[0]
                tot = bdf7[(bdf7['BASE_OD_ORGN_COUNTRY'] == orgn) &\
                           (bdf7['BASE_OD_DSTN_COUNTRY'] == dstn)]['REFERENCE'].iloc[0]
                percs[i,j] = int(100 * float(counts[i,j]) / tot)
            except:
                counts[i,j] = 0
                percs[i,j] = 0

    print 'Making plot...'
    maxcount = np.log(df7['REFERENCE'].max())
    title = 'Group pax from ' + region + ' cancelled in ' + str(dpl) + ' ... ' + str(dph) + ' days prior departure for last 7 days'
    html = heatmap(xnames, ynames, counts, percs, maxcount, 'red', title, 'Group pax cancellations ' + region)
    return html


def produce_country(country):
    html_30_59 = produce_country_7(country, 30, 59)
    html_7_29 = produce_country_7(country, 7, 29)
    html_0_6 = produce_country_7(country, 0, 6)
   
    currdt = datetime.now()
    currdts = datetime.strftime(currdt, '%Y%m%d')
    prevdt = currdt - timedelta(days = 1)
    prevdts = datetime.strftime(prevdt, '%Y%m%d')
    
    fname = '/home/ay49514/tmp/GC_7_60_' + country + '_' + currdts + '.html'
    f = open(fname, 'w')
    if html_30_59 != '':
        f.write(html_30_59)
    if html_7_29 != '':
        f.write(html_7_29)
    if html_0_6 != '':
        f.write(html_0_6)
    f.close()

    print 'Saving plot to s3...'
    s3name = 's3://ay-emr-job/nrm/reporting/gc/'+currdts[:4]+'/'+currdts[4:6]+'/GC_7_60_' + country + '_' + currdts + '.html'
    copy2s3(fname, s3name)
    return fname


def produce_region(region):
    html_30_59 = produce_region_7(region, 30, 59)
    html_7_29 = produce_region_7(region, 7, 29)
    html_0_6 = produce_region_7(region, 0, 6)

    currdt = datetime.now()
    currdts = datetime.strftime(currdt, '%Y%m%d')
    prevdt = currdt - timedelta(days = 1)
    prevdts = datetime.strftime(prevdt, '%Y%m%d')

    fname = '/home/ay49514/tmp/GC_7_60_' + region + '_' + currdts + '.html'
    f = open(fname, 'w')
    if html_30_59 != '':
        f.write(html_30_59)
    if html_7_29 != '':
        f.write(html_7_29)
    if html_0_6 != '':
        f.write(html_0_6)
    f.close()

    print 'Saving plot to s3...'
    s3name = 's3://ay-emr-job/nrm/reporting/gc/'+currdts[:4]+'/'+currdts[4:6]+'/GC_7_60_' + region + '_'+currdts+'.html'
    copy2s3(fname, s3name)

    return fname


if __name__ == "__main__":
    fname_europe = produce_region('EUROPE')
    fname_cn = produce_country('CN')
    fname_jp = produce_country('JP')
    fname_kr = produce_country('KR')
    fname_sg = produce_country('SG')
    fname_hk = produce_country('HK')
    fname_th = produce_country('TH')
    fname_in = produce_country('IN')
    fname_namer = produce_region('NAMER')

    print 'Sending email...'
    for i in range(10):
        try:
            send_multipart('fedor.nikitin@finnair.com',\
                           'fedor.nikitin@finnair.com',\
                           'Group cancellations weekly',\
                           'Find report attached',\
                           [fname_europe,fname_asia,fname_namer])
            break
        except:
            pass

    subprocess.check_output(['rm',fname_europe])
    subprocess.check_output(['rm',fname_cn])
    subprocess.check_output(['rm',fname_jp])
    subprocess.check_output(['rm',fname_kr])
    subprocess.check_output(['rm',fname_sg])
    subprocess.check_output(['rm',fname_hk])
    subprocess.check_output(['rm',fname_th])
    subprocess.check_output(['rm',fname_in])
    subprocess.check_output(['rm',fname_namer])


         
