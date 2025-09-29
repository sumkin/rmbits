import sys
import csv
import gzip
import subprocess
from joblib import Parallel, delayed
import multiprocessing
import time
from datetime import datetime
import traceback
import random

from bffreader2 import *
from s3utils import *
#from emailutils import *


def process(fname):
    # Check that file is already processed.
    # We check one booking date only.
    dt = datetime.strptime(fname.rsplit('/',1)[1].split('.')[4][1:], '%y%m%d')
    dtstr = datetime.strftime(dt, '%Y%m%d')
    depdt = datetime.strptime(fname.rsplit('/',1)[1].split('.')[8][2:], '%y%m%d')
    depdt_s = depdt.strftime('%Y%m%d')

    csv2check = 'ay-emr-job/nrm/fullbff/'+str(dt.year)+'/'+str(dt.month).zfill(2)+'/'+str(dt.day).zfill(2)+\
                '/FCST_'+dt.strftime('%Y%m%d')+'_'+depdt_s+'_'+depdt_s+'.csv.gz'

    csv_exists = s3fileexists(csv2check)
    if csv_exists:
        print(csv2check, ' exists')
        return 0

    print("Processing ", fname)

    print("Copying to local file...")
    fnames = fname.split('/')
    lfname = '/mnt/data/tmp/' + fnames[6]
    subprocess.check_output(['aws','s3','cp', 's3://ay-dp-prod-data-inbound-nrm/'+fname,lfname]) 

    src_date = datetime.strptime(fnames[6].split('.')[4][1:], "%y%m%d")
    depdt = datetime.strptime(fnames[6].split('.')[8][2:], "%y%m%d")

    print("Unzipping...")
    try:
        subprocess.check_output(['gunzip',lfname])
    except Exception as e:
        print(e)
        subprocess.check_output(['rm',lfname])
        return 0

    lfnamewogz = lfname.rsplit('.',1)[0]
    bffReader = BFFReader2(lfnamewogz)
    ap = Airport()
    src_date_s = datetime.strftime(src_date, '%Y%m%d')

    csv_fnames = {}
    csv_fname_fps = {}
    fouts = {}
    csvwriters = {}
    nums = {}
    for bts in bffReader.btss():
        for csvline in BFFReader2.get_bkgdate_csv_lines(bts, src_date, src_date_s, ap):
            k = csvline[3] + '-' + csvline[17]
            if k not in csv_fnames.keys():
                assert k not in csv_fname_fps.keys()
                assert k not in csvwriters.keys()

                csv_fname =  'FCST_' + str(src_date.year) + str(src_date.month).zfill(2) + str(src_date.day).zfill(2) +\
                                 '_' + csvline[3] + '_' + csvline[17] + '.csv.gz'
                csv_fname_fp = '/mnt/data/tmp/' + csv_fname
              
                fout = gzip.open(csv_fname_fp, 'wt')  
                csvwriter = csv.writer(fout)
                csvwriter.writerow(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN',\
                                    'BASE_OD_DEP_DATE',\
                                    'GEO_ORGN','GEO_DSTN',\
                                    'POS','BC','FF','TP',\
                                    'SMP','AMP','SRD','SGCD','ARD','AGCD',\
                                    'SRC_DATE','BKG_DATE'])
                csv_fnames[k] = csv_fname
                csv_fname_fps[k] = csv_fname_fp
                fouts[k] = fout
                csvwriters[k] = csvwriter
                nums[k] = 1
            csvwriters[k].writerow(csvline) 
            nums[k] += 1

    for k in csv_fnames.keys(): 
        fouts[k].close()

        print("Copying file to s3...")
        subfolder = str(src_date.year) + '/' + str(src_date.month).zfill(2) + '/' + str(src_date.day).zfill(2)
        s3fname = 's3://ay-emr-job/nrm/fullbff/'+subfolder+'/'+csv_fnames[k]
        subprocess.check_output(['aws','s3','cp',csv_fname_fps[k],s3fname])
        subprocess.check_output(['rm', csv_fname_fps[k]])
        time.sleep(random.randint(0,3))

    subprocess.check_output(['rm', lfnamewogz])
    return 1


def process_parallel(fnames):
    num_cores = multiprocessing.cpu_count()
    results = Parallel(n_jobs = int(num_cores / 2))(delayed(process)(fname) for fname in fnames)
    return sum(results)


def process_non_parallel(fnames):
    res = 0
    for fname in fnames:
        res = process(fname)
        res += 1
    return res


if __name__ == "__main__":
    #dt = datetime.now() - timdelta(days = 1)
    #dt = datetime(2019,12,16)

    dt = datetime.now()
    for i in range(5):
        # Get files in folder.
        path = 'ay-dp-prod-data-inbound-nrm/uncompressed/boomi/bff/yyyy='+str(dt.year).zfill(4)+\
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
            print(e)
        dt_e = datetime.now()

        sbj = 'Forecast files have been processed.'
        txt = ''
        seconds = int((dt_e - dt_s).seconds)
        hours = seconds / 3600
        minutes = (seconds - hours * 3600) / 60
        seconds = (seconds - hours * 3600 - minutes * 60)

        txt += 'Processed in ' + str(hours) + ' hours ' + str(minutes) + ' minutes ' + str(seconds) + ' seconds.'
        send_quick('fedor.nikitin@finnair.com', 'fedor.nikitin@finnair.com', sbj, txt)
    
        dt = dt - timedelta(days = 1)

    print("Done.")




