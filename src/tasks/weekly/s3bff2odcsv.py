import os
import re
import sys
import csv
import glob
import subprocess
from joblib import Parallel, delayed
import multiprocessing
from datetime import datetime
import traceback

from bffreader2 import *
from s3utils import *

def process(fname):
    # Check that file is already processed.
    dt = datetime.strptime(fname.rsplit('/',1)[1].split('.')[4][1:], '%y%m%d')
    dtstr = datetime.strftime(dt, '%Y%m%d')
    depdt = datetime.strptime(fname.rsplit('/',1)[1].split('.')[8][2:], '%y%m%d')
    csv2check = 'ay-rmp-home/nrm/bff/'+str(dt.year)+\
                '/'+str(dt.month).zfill(2)+\
                '/'+str(dt.day).zfill(2)+\
                '/FCST_OD_'+dt.strftime('%Y%m%d')+'_'+\
                depdt.strftime('%Y%m%d')+'.csv.gz'
    csv2checkdcp = 'ay-rmp-home/nrm/bff/'+str(dt.year)+\
                   '/'+str(dt.month).zfill(2)+\
                   '/'+str(dt.day).zfill(2)+\
                   '/FCST_OD_DCP_'+dt.strftime('%Y%m%d')+'_'+\
                   depdt.strftime('%Y%m%d')+'.csv.gz'

    csv_exists = s3fileexists(csv2check)
    csv_exists_dcp = s3fileexists(csv2checkdcp)

    if csv_exists and csv_exists_dcp:
        print(csv2check, 'and', csv2checkdcp, ' exists')
        return 0

    print("Processing ", fname)

    print("Copying to local file...")
    fnames = fname.split('/')
    lfname = '/mnt/data/tmp/' + fnames[5]
    s3copy('s3://ay-dp-prod-data-inbound-nrm/' + fname, lfname)

    src_date_s = fnames[5].split('.')[4][1:]
    src_date = datetime.strptime(src_date_s, "%y%m%d")
    src_week = str(src_date.year) + '-' + str(src_date.isocalendar()[1])
    depdt = datetime.strptime(fnames[5].split('.')[8][2:], "%y%m%d")

    print("Unzipping...")
    try:
        subprocess.check_output(['gunzip',lfname])
    except Exception as e:
        print(e)
        subprocess.check_output(['rm',lfname])
        return 0

    lfnamewogz = lfname.rsplit('.',1)[0]
    bffReader = BFFReader2(lfnamewogz)

    if not csv_exists:
        print("Generating FCST_OD csv...")
        csv_fname =  'FCST_OD_' + str(src_date.year) + str(src_date.month).zfill(2) +\
                      str(src_date.day).zfill(2) +\
                      '_' + str(depdt.year) + str(depdt.month).zfill(2) + str(depdt.day).zfill(2) +\
                      '.csv'
        csv_fname_fp = '/mnt/data/tmp/' + csv_fname

        with open(csv_fname_fp, 'w') as fout:
            csvwriter = csv.writer(fout)
            csvwriter.writerow(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                                'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                                'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                                'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                                'BASE_OD_DEP_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE',\
                                'GEO_ORGN','GEO_DSTN',\
                                'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM','PREV_MKT_CC','PREV_MKT_FLTNUM',\
                                'PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                                'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM','NEXT_MKT_CC','NEXT_MKT_FLTNUM',\
                                'NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE',\
                                'POS','BC','FF','SMP','SMPWA','AMP','AMPWA','TP','PB',\
                                'SFD','SRD','SRDSUM','SRGCCD','SGCD','SRGCD',\
                                'AFD','ARD','ARDSUM','ARGCCD','AGCD','ARGCD',\
                                'SRC_DATE'])
            for bts in bffReader.btss():
                for csvline in BFFReader2.get_csv_lines(bts, src_date, src_week):
                    csvwriter.writerow(csvline)
 
        print("Zipping file...")
        subprocess.check_output(['gzip',csv_fname_fp]) 

        print("Copying file to s3...")
        subfolder = str(src_date.year) + '/' + str(src_date.month).zfill(2) + '/' + str(src_date.day).zfill(2)
        s3fname = 's3://ay-rmp-home/nrm/bff/'+subfolder+'/'+csv_fname+'.gz'
        s3copy(csv_fname_fp+'.gz',s3fname)

    if not csv_exists_dcp:
        print("Generating FCST_OD_DCP csv...")
        csv_fname_dcp = 'FCST_OD_DCP_' + str(src_date.year) + str(src_date.month).zfill(2) +\
                        str(src_date.day).zfill(2) +\
                        '_' + str(depdt.year) + str(depdt.month).zfill(2) + str(depdt.day).zfill(2) +\
                        '.csv'
        csv_fname_fp_dcp = '/mnt/data/tmp/' + csv_fname_dcp
        with open(csv_fname_fp_dcp, 'w') as fout:
            ap = AirportS3()
            csvwriter = csv.writer(fout)
            csvwriter.writerow(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                                'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                                'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                                'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                'BASE_MKT_CC','BASE_MKT_FLTNUM',\
                                'BASE_OD_DEP_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE',\
                                'GEO_ORGN','GEO_DSTN',\
                                'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM','PREV_MKT_CC','PREV_MKT_FLTNUM',\
                                'PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                                'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM','NEXT_MKT_CC','NEXT_MKT_FLTNUM',\
                                'NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE',\
                                'POS','BC','FF','TP',\
                                'DCP','SMP','AMP','SRD','SGCD','ARD','AGCD',\
                                'SRC_DATE'])
            for bts in bffReader.btss():
                for csvline in BFFReader2.get_dcp_csv_lines(bts, src_date_s, ap):
                    csvwriter.writerow(csvline)

        print("Zipping file...")
        subprocess.check_output(['gzip',csv_fname_fp_dcp])

        print("Copying file to s3...")
        subfolder = str(src_date.year) + '/' + str(src_date.month).zfill(2) + '/' + str(src_date.day).zfill(2)
        s3fname = 's3://ay-rmp-home/nrm/bff/'+subfolder+'/'+csv_fname_dcp+'.gz'
        s3copy(csv_fname_fp_dcp+'.gz',s3fname)

    print("Cleaning-up...")
    if not csv_exists:
        subprocess.check_output(['rm', csv_fname_fp+'.gz'])
    if not csv_exists_dcp:
        subprocess.check_output(['rm', csv_fname_fp_dcp+'.gz'])
    subprocess.check_output(['rm', lfnamewogz])
    return 1

def process_parallel(fnames):
    num_cores = multiprocessing.cpu_count()
    results = Parallel(n_jobs = int(num_cores / 2))(delayed(process)(fname) for fname in fnames)
    return sum(results)

def process_non_parallel(fnames):
    res = 0
    for fname in fnames:
        r = process(fname)
        res += 1
    return res

if __name__ == "__main__":
    dt = datetime.now()
    for i in range(100):
        # Get files in folder.
        path = 'ay-dp-prod-data-inbound-nrm/boomi/bff/yyyy='+str(dt.year).zfill(4)+\
                                                    '/mm='+str(dt.month).zfill(2)+\
                                                    '/dd='+str(dt.day).zfill(2)
        fnames = gets3files(path)

        # Filter out not BFF files.
        fnames = filter(lambda s: 'PRD.RMS.NFS.XML.' in s, fnames)
        fnames = sorted(fnames, reverse = True)

        # Go over files and process them.
        dt_s = datetime.now()
        try:
            process_parallel(fnames)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            traceback.print_tb(exc_tb)
        dt_e = datetime.now()

        sbj = 'Forecast files have been processed.'
        txt = ''
        seconds = int((dt_e - dt_s).seconds)
        hours = seconds / 3600
        minutes = (seconds - hours * 3600) / 60
        seconds = (seconds - hours * 3600 - minutes * 60)

        txt += 'Processed in ' + str(hours) + ' hours ' + str(minutes) + ' minutes ' + str(seconds) + ' seconds.'
        #send_quick('fedor.nikitin@finnair.com', 'fedor.nikitin@finnair.com', sbj, txt)

        print("Done.")
        dt = dt - timedelta(days = 1)




