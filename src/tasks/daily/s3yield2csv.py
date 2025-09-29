import csv
import re
import subprocess
from datetime import datetime
import traceback

from yieldreader import *
from s3utils import *
#from emailutils import *


def process(fname):
    dt_s = datetime.now()

    print("Processing ", fname)

    print("Copying to local file...")
    fnames = fname.split('/')
    lfname = '/mnt/data/tmp/' + fnames[5]
    subprocess.check_output(['aws','s3','cp', 's3://ay-dp-prod-data-inbound-nrm/'+fname,lfname])

    src_dt = datetime.strptime(fnames[5].split('.')[5][1:], "%y%m%d")
    src_week = str(src_dt.year) + '-' + str(src_dt.isocalendar()[1])

    print("Unzipping...")
    try:
        subprocess.check_output(['gunzip',lfname])
    except Exception as e:
        print(e)
        subprocess.check_output(['rm',lfname])
        return

    print("Generating csv...")
    lfnamewogz = lfname.rsplit('.',1)[0]
    csv_fname = 'YIELD_' + str(src_dt.year) + str(src_dt.month).zfill(2) + str(src_dt.day).zfill(2) + '.csv' 
    csv_fname_fp = '/mnt/data/tmp/' + csv_fname
    yieldReader = YieldReader(lfnamewogz)
    with open(csv_fname_fp, 'w') as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(['ORGN','DSTN','TRVLFROM','TRVLTO','SALESFROM','SALESTO','DOWS','CC',\
                            'CNX','AVS','MAN','CLSD','POS','CLS','GBL_AM','GBL_CR',\
                            'YQ_AM','YQ_CR','TAX_AM','TAX_CR','WEIGHT','SRC_DATE'])
        for l in yieldReader.yields():
            csvwriter.writerow([l[0],l[1],\
                                datetime.strftime(l[2],'%Y%m%d'),datetime.strftime(l[3],'%Y%m%d'),\
                                datetime.strftime(l[4],'%Y%m%d'),datetime.strftime(l[5],'%Y%m%d'),\
                                l[6],l[7],l[8],l[9],l[10],l[11],l[12],l[13],l[14],\
                                l[15],l[16],l[17],l[18],l[19],l[20],datetime.strftime(l[21],'%Y%m%d')])

    print("Zipping file...")
    try:
        subprocess.check_output(['gzip', csv_fname_fp]) 
    except Exception as e:
        print(e)
        subprocess.check_output(['rm', csv_fname_fp])
        return

    print("Copying file to s3...")
    subfolder = str(src_dt.year) + '/' + str(src_dt.month).zfill(2)
    s3fname = 's3://ay-emr-job/nrm/yield/'+subfolder+'/'+csv_fname+'.gz'
    subprocess.check_output(['aws','s3','cp',csv_fname_fp+'.gz',s3fname])

    print("Cleaning-up...")
    print(csv_fname + '.gz', lfname)
    subprocess.check_output(['rm', csv_fname_fp+'.gz'])
    subprocess.check_output(['rm', lfnamewogz])
    dt_e = datetime.now()

    '''
    sbj = csv_fname + ' has been processed.'
    _seconds = int((dt_e - dt_s).seconds)
    hours = _seconds / 3600
    minutes = (_seconds - hours * 3600) / 60
    seconds = (_seconds - hours * 3600 - minutes * 60)
    body = 'Processed in ' + str(hours) + ' hours ' + str(minutes) + ' minutes ' + str(seconds) + ' seconds.'
    send_quick('fedor.nikitin@finnair.com', 'fedor.nikitin@finnair.com', sbj, body)
    '''


if __name__ == "__main__":
    # Get files in folder.
    fnames = gets3files("ay-dp-prod-data-inbound-nrm/boomi/yield/")

    # Filter out not BAF files.
    fnames = filter(lambda s: 'PRD.NGI.OND.YIELD.' in s, fnames)
    fnames = sorted(fnames, reverse=True)

    # Go over files and process them.
    for fname in fnames[:100]:

        # Check that file is already processed.
        dt = datetime.strptime(fname.rsplit('/',1)[1].split('.')[5][1:], '%y%m%d')
        csv2check = 'ay-emr-job/nrm/yield/'+str(dt.year)+\
                      '/'+str(dt.month).zfill(2)+'/YIELD_'+dt.strftime('%Y%m%d')+'.csv.gz'

        if s3fileexists(csv2check):
            print(csv2check, 'exists')
            continue
        try:
            process(fname)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            traceback.print_tb(exc_tb)

    print("Done.")




