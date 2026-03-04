import os
import gc
import sys
import csv
import re
import subprocess
from joblib import Parallel, delayed
import multiprocessing
from datetime import datetime
import traceback

from bofreader import *
from s3utils import *
#from emailutils import *

def process(fname):
    dt_s = datetime.now()

    print("Processing ", fname)

    print("Copying to local file...")
    fnames = fname.split('/')
    lfname = '/mnt/data/tmp/' + fnames[5]
    print(fnames)
    subprocess.check_output(['aws','s3','cp', 's3://ay-dp-prod-data-inbound-nrm/'+fname,lfname])

    src_dt = datetime.strptime(fnames[5].split('.')[4][1:], "%y%m%d")
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
    od_csv_fname = 'BKG_OD_' + str(src_dt.year) + str(src_dt.month).zfill(2) + str(src_dt.day).zfill(2) + '.csv' 
    seg_csv_fname = 'BKG_SEG_' + str(src_dt.year) + str(src_dt.month).zfill(2) + str(src_dt.day).zfill(2) + '.csv'
    od_csv_fname_fp = '/mnt/data/tmp/' + od_csv_fname
    seg_csv_fname_fp = '/mnt/data/tmp/' + seg_csv_fname

    try:
        bofReader = BOFReader(lfnamewogz, src_dt)
    except Exception as e:
        print(e)
        subprocess.check_output(['rm', lfnamewogz])
        return 0

    with open(od_csv_fname_fp, 'w') as od_fout:
        with open(seg_csv_fname_fp, 'w') as seg_fout:
            od_csvwriter = csv.writer(od_fout)
            od_csvwriter.writerow(['GEO_OD_TS_KEY',\
                                   'BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                                   'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                                   'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                                   'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                   'BASE_MKT_CC','BASE_MKT_FLTNUM','BASE_OD_DEPT_DATE','DAYSPRIOR',\
                                   'BASE_SEG_DEPT_DATE','BASE_SEG_ARR_DATE',\
                                   'GEO_ORGN','GEO_DSTN',\
                                   'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM','PREV_MKT_CC','PREV_MKT_FLTNUM',\
                                   'PREV_SEG_DEPT_DATE','PREV_SEG_ARR_DATE',\
                                   'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM','NEXT_MKT_CC','NEXT_MKT_FLTNUM',\
                                   'NEXT_SEG_DEPT_DATE','NEXT_SEG_ARR_DATE',\
                                   'RLOCATOR','TDIRECTION',\
                                   'BKG_TYPE','PSEUDO_CITY_CODE','ISO_COUNTRY','ISO_REGION','AGDUTY_CODE','REQUESTOR_ID',\
                                   'SELL_CLS','CABIN','REFERENCE','YIELD','SRC_DATE'])
            seg_csvwriter = csv.writer(seg_fout)
            seg_csvwriter.writerow(['ORGN','DSTN','OPR_CC','OPR_FLTNUM','MKT_CC','MKT_FLTNUM','DEPT_DATE','ARR_DATE','DAYSPRIOR',\
                                    'GEO_ORGN','GEO_DSTN',\
                                    'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM','PREV_MKT_CC','PREV_MKT_FLTNUM',\
                                    'PREV_SEG_DEPT_DATE','PREV_SEG_ARR_DATE',\
                                    'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM','NEXT_MKT_CC','NEXT_MKT_FLTNUM',\
                                    'NEXT_SEG_DEPT_DATE','NEXT_SEG_ARR_DATE',\
                                    'RLOCATOR','TDIRECTION',\
                                    'BKG_TYPE','PSEUDO_CITY_CODE','ISO_COUNTRY','ISO_REGION','AGDUTY_CODE','REQUESTOR_ID',\
                                    'SELL_CLS','CABIN','REFERENCE','SRC_DATE'])
            
            for bts in bofReader.btss():
                for csvline in bofReader.get_od_csv_lines(bts, src_dt, src_week): 
                    od_csvwriter.writerow(csvline)
                for csvline in bofReader.get_seg_csv_lines(bts, src_dt, src_week):
                    seg_csvwriter.writerow(csvline)
    
    print("Zipping file...")
    try:
        subprocess.check_output(['gzip', od_csv_fname_fp]) 
        subprocess.check_output(['gzip', seg_csv_fname_fp])
    except Exception as e:
        print(e)
        subprocess.check_output(['rm', od_csv_fname_fp])
        subprocess.check_output(['rm', seg_csv_fname_fp])
        return

    print("Copying file to s3...")
    subfolder = str(src_dt.year) + '/' + str(src_dt.month).zfill(2)
    od_s3fname = 's3://ay-rmp-home/nrm/bof/' + subfolder + '/' + od_csv_fname + '.gz'
    seg_s3fname = 's3://ay-rmp-home/nrm/bof/' + subfolder + '/' + seg_csv_fname + '.gz'
    subprocess.check_output(['aws','s3','cp', od_csv_fname_fp + '.gz', od_s3fname])
    subprocess.check_output(['aws','s3','cp', seg_csv_fname_fp + '.gz', seg_s3fname])

    print("Cleaning-up...")
    print(od_csv_fname + '.gz', lfname)
    print(seg_csv_fname + '.gz', lfname)
    subprocess.check_output(['rm', od_csv_fname_fp + '.gz'])
    subprocess.check_output(['rm', seg_csv_fname_fp + '.gz'])
    subprocess.check_output(['rm', lfnamewogz])
    dt_e = datetime.now()

def process_parallel(fnames):
    num_cores = multiprocessing.cpu_count()
    results = Parallel(n_jobs = 5)(delayed(process)(fname) for fname in fnames)
    return sum(results)

def process_non_parallel(fnames):
    for fname in fnames:
        process(fname)

if __name__ == "__main__":
    # Get files in folder.
    fnames = gets3files('ay-dp-prod-data-inbound-nrm/boomi/bof/')

    # Filter out not BAF files.
    fnames = filter(lambda s: 'PRD.NGI.IBAONDXML.ODB_FEED.' in s, fnames)
    fnames = sorted(fnames, reverse=True)

    # Go over files and process them.
    fnames_to_process = []
    for fname in fnames[:100]:
        # Check that file is already processed.
        dt = datetime.strptime(fname.rsplit('/',1)[1].split('.')[4][1:], '%y%m%d')
        csv2check = 'ay-rmp-home/nrm/bof/'+str(dt.year)+'/'+\
                    str(dt.month).zfill(2)+'/BKG_OD_'+dt.strftime('%Y%m%d')+'.csv.gz'
        if s3fileexists(csv2check):
            print(csv2check, 'exists')
            continue
        print(fname)
        fnames_to_process.append(fname)

    process_non_parallel(fnames_to_process)

    print("Done.")




