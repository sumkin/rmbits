import os
import sys
import csv
import re
import subprocess
from datetime import datetime, timedelta
import traceback

from bafreader import *
from s3utils import *
#from emailutils import *


def process(fname):
    dt_b = datetime.now()
    print("Processing ", fname)

    print("Copying to local file...")
    fnames = fname.split('/')
    lfname = '/mnt/data/tmp/' + fnames[5]
    subprocess.check_output(['aws','s3','cp', 's3://ay-dp-prod-data-inbound-nrm/'+fname,lfname])

    dt = datetime.strptime(fnames[5].split('.')[4][1:], "%y%m%d")

    print("Unzipping...")
    try:
        subprocess.check_output(['gunzip',lfname])
    except Exception as e:
        print(e)
        subprocess.check_output(['rm',lfname])
        return

    print("Generating csv...")
    lfnamewogz = lfname.rsplit('.',1)[0]
    csv_fname = 'AV_OD_' + str(dt.year) + str(dt.month).zfill(2) + str(dt.day).zfill(2) + '.csv' 
    csv_fname_fp = '/mnt/data/tmp/' + csv_fname
    bafReader = BAFReader(lfnamewogz, dt)
    with open(csv_fname_fp, 'w') as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(['ORGN','DSTN','VIA','CC','FLTNUM',\
                            'OD_DEPT_DATE','OD_DEPT_DOW','SEG_DEPT_DATE',\
                            'POS','POSTYPE',\
                            'J','C','D','I','F','U',\
                            'Y','B','H','K','M','P',\
                            'T','L','V','S','N','G',\
                            'A','Q','O','Z','R','W',\
                            'X','E',\
                            'LOCJ', 'LOCIJ', 'LOCY', 'LOCIY',\
                            'LOCJ_WOSC','LOCIJ_WOSC','LOCY_WOSC',\
                            'LOCIY_WOSC','SRC_DATE'])
        for od in bafReader.ods():
            csvline = bafReader.get_csv_line(od)
            csvwriter.writerow(csvline)
    
    print("Zipping file...")
    try:
        subprocess.check_output(['gzip', csv_fname_fp]) 
    except Exception as e:
        print(e)
        subprocess.check_output(['rm', csv_fname_fp])
        return

    print("Copying file to s3...")
    subfolder = str(dt.year) + '/' + str(dt.month).zfill(2)
    s3fname = 's3://ay-rmp-home/nrm/baf/'+subfolder+'/'+csv_fname+'.gz'
    subprocess.check_output(['aws','s3','cp',csv_fname_fp+'.gz',s3fname])

    print("Cleaning-up...")
    print(csv_fname + '.gz', lfname)
    subprocess.check_output(['rm', csv_fname_fp+'.gz'])
    subprocess.check_output(['rm', lfnamewogz])
    dt_e = datetime.now()

    '''
    seconds = int((dt_e - dt_b).seconds)
    hours = seconds / 3600
    minutues = (seconds - hours * 3600) / 60
    seconds = (seconds - hours * 3600 - minutes * 60)
    sbj = csv_fname + ' has been processed.'
    body = 'Processed in ' + str(hours) + ' hours ' + str(minutes) + ' minutes ' + str(seconds) + ' seconds'
    send_quick('fedor.nikitin@finnair.com', 'fedor.nikitin@finnair.com', sbj, body)
   '''


if __name__ == "__main__":
    # Get files in folder.
    fnames = gets3files('ay-dp-prod-data-inbound-nrm/boomi/baf/')

    # Filter out not BAF files.
    fnames = filter(lambda s: 'PRD.NGI.BAF_OUTPUT_BAF.AVL.' in s or 'PRD.NGI.BAF_OUTPUT.AVL.' in s, fnames)
    fnames = sorted(fnames, reverse=True)

    # Go over files and process them.
    for fname in fnames[:30]:
        # Check that file is already processed.
        dt = datetime.strptime(fname.rsplit('/',1)[1].split('.')[4][1:], '%y%m%d')
        csv2check = 'ay-rmp-home/nrm/baf/'+str(dt.year)+\
                      '/'+str(dt.month).zfill(2)+'/AV_OD_'+dt.strftime('%Y%m%d')+'.csv.gz'

        if s3fileexists(csv2check):
            print(csv2check, 'exists')
            continue
        try:
            process(fname)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            traceback.print_tb(exc_tb)

    print("Done.")




