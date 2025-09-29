'''
Script reads s3://ay-emr-job/nrm/baf folder.
Find all the BAF files not compared to previous one.

Generates the difference and writes CSV file to s3.

Script should be run repeatedly to kepp OD availability
different up-to-date.

2018, Fedor Nikitin (AY49514)
'''
import os
import re
import subprocess
from datetime import datetime, timedelta

from s3baf2odjson import *

thisfiledir = os.path.dirname(os.path.realpath(__file__))


def get_prev_cur_info(fname):
    curdt  = datetime.strptime(fname.rsplit('/',1)[1].split('.')[0].split('_')[2], '%Y%m%d')
    prevdt = curdt - timedelta(1)
    prevfname = 'ay-emr-job/nrm/baf/'+str(prevdt.year)+\
                '/'+str(prevdt.month).zfill(2)+'/AV_OD_'+prevdt.strftime('%Y%m%d')+'.json.gz'
    difffname = 'ay-emr-job/nrm/baf/'+str(curdt.year)+\
               '/'+str(curdt.month).zfill(2)+'/AV_OD_DIFF_'+curdt.strftime('%Y%m%d')+\
               '-'+prevdt.strftime('%Y%m%d')+'.csv'
    locfname = 'ay-emr-job/nrm/baf/'+str(curdt.year)+\
               '/'+str(curdt.month).zfill(2)+'/AV_OD_LOCDIFF_'+curdt.strftime('%Y%m%d')+\
               '-'+prevdt.strftime('%Y%m%d')+'.csv'
    return prevdt,curdt,prevfname,difffname,locfname


def process(fname):
    print "Processing ", fname
    prevdt,curdt,prevfname,difffname,locfname = get_prev_cur_info(fname)
    if not s3fileexists(difffname) and s3fileexists(prevfname):
        print "Generating difference"
        subprocess.check_output(['spark-submit',\
                                 thisfiledir + '/av_diff_pyspark.py',\
                                 curdt.strftime('%Y-%m-%d'),\
                                 prevdt.strftime('%Y-%m-%d'),
                                 '>','~/tmp/spark-log.txt']) 
        # Copy files.
        names = [difffname, locfname]
        for name in names:
            print "Copying file ", name
            s3fnames = gets3files(name + '/') 
            s3fnames = filter(lambda s: 'part-000' in s, s3fnames)
            assert len(s3fnames) == 1
            s3fname = s3fnames[0]
            subprocess.check_output(['aws','s3','cp','s3://ay-emr-job/'+s3fname,\
                                     's3://' + name])

            # Deleting tmp folder.
            subprocess.check_output(['aws','s3','rm','--recursive',\
                                     's3://ay-emr-job/'+s3fname.rsplit('/',1)[0]+'/'])

        print "Done"


if __name__ == "__main__":
    # Get files in folder.
    fnames = gets3files('ay-emr-job/nrm/baf')

    # Filter out files.
    fnames = filter(lambda s: re.search('AV_OD_\d{8}.json.gz',s), fnames)

    # Go over files and process them.
    for fname in fnames:

        # Check that file is already processed.
        prevdt,curdt,prevfname,difffname,locname= get_prev_cur_info(fname)
        if s3fileexists(difffname):
            print difffname, 'exists'
            continue
        try:
            process(fname)
        except Exception as e:
            print e

    print 'Done.'



