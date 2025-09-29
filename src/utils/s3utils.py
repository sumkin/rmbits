import re
import subprocess
from datetime import datetime, timedelta
from time import sleep
import boto3
import botocore

s3 = boto3.resource('s3')

NUM_TRIES = 5

def gets3files(fldr, wpath=True):
    #
    # Get the content of s3 bucket folder.
    #
    for i in range(NUM_TRIES):
        try:
            out = subprocess.check_output(['aws','s3','ls','--recursive',fldr])
            lines = out.decode().split('\n')
            res = []
            for l in lines:
                if l.strip() == "":
                    continue
                f = re.sub('( |\t) +', ' ', l).split(' ')[3]
                res.append(f)
            if wpath:
                return res
            else:
                return [e.rsplit('/',1)[1] for e in res]
        except Exception as e:
            sleep(1)
    return []

def s3copy(orig, dstn):
    for i in range(NUM_TRIES):
        try:
            out = subprocess.check_output(['aws', 's3', 'cp', orig, dstn])
        except Exception as e:
            print('copy2s3 e = ', e)
            sleep(1)
            continue

def s3fileexists(fname):
    #
    # Checks whether file exists or not on s3.
    #
    bucket, obj = fname.split('/',1)
    try:
        s3.Object(bucket, obj).load()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise
    return True

def s3filesize(fname):
    for i in range(NUM_TRIES):
        try:
            out = subprocess.check_output(['aws','s3','ls','s3://'+fname])
            outs = out.decode('utf-8').split(' ')
            outs = [e.strip() for e in outs]
            outs = [e for e in outs if e != '']
            return int(outs[2])
        except Exception as e:
            print('filesizes3 e = ', e)
            sleep(1)
    return None

def s3filesexists(fnames, fldr):
    try:
        fldrfiles = gets3files(fldr)
        for fname in fnames:
            if fname not in fldrfiles:
                return False
    except Exception as e:
        raise e
        return False
    return True

def s3getlastavfile():
    dt = datetime.now()
    s3fname = []
    while True:
        s3fname = 'ay-emr-job/nrm/baf/' + str(dt.year).zfill(2) + '/' + \
                                          str(dt.month).zfill(2) + '/' + \
                                          'AV_OD_' + datetime.strftime(dt,'%Y%m%d') + '.csv.gz'
        if s3fileexists(s3fname):
            break      
        dt = dt - timedelta(days=1) 
    return s3fname

def s3getlastinvfile():
    dt = datetime.now()
    s3fname = None
    while True:
        s3fname = 'ay-emr-job/nrm/bif/' + str(dt.year).zfill(2) + '/' + \
                                          str(dt.month).zfill(2) + '/' + \
                                          'INV_' + datetime.strftime(dt,'%Y%m%d') + '.csv.gz'
        if s3fileexists(s3fname):
            break;
        dt = dt - timedelta(days=1)
    return s3fname

def s3getlastfcstfiles(dt = None):
    if dt is None:
        dt = datetime.now()
    s3fnames = []
    while True:
        year = str(dt.year).zfill(2)
        month = str(dt.month).zfill(2)
        day = str(dt.day).zfill(2)
        dts = datetime.strftime(dt, '%Y%m%d')
        s3fname = 'ay-emr-job/nrm/bff/' + year + '/' + \
                                          month + '/' + \
                                          day + '/' + \
                                          'FCST_OD_' + dts + '_' + dts + '.csv.gz'
        if s3fileexists(s3fname):
            s3fnames = gets3files('ay-emr-job/nrm/bff/' + year + '/' + \
                                                          month + '/' + \
                                                          day + '/')
            return dt,s3fnames
        dt = dt - timedelta(days=1)    
    return datetime(1970,1,1), []

def s3getpwdcprefix(valdate):
    fnames = gets3files('ay-emr-job/nrm/pwdc/')

    latest_parts = None
    latest_nms = '00000000'
    latest_nmss = None
    for fname in fnames:
        parts = fname.split('/')
        nm = parts[5]
        nms = nm.split('_')
        if nms[1] <= valdate and valdate <= nms[2]:
            res = '/'.join(parts[:5]) + '/' + '_'.join(nms[:3])
            return res, nms[1], nms[2], True   
        if latest_nms < nms[2]:
            latest_nms = nms[2]
            latest_nmss = nms
            latest_parts = parts
    return '/'.join(parts[:5]) + '/' + '_'.join(nms[:3]), nms[1], nms[2], False

def s3yieldfilepresent(dtstr):
    year = dtstr[:4]
    month = dtstr[4:6]
    s3fname = 'ay-emr-job/nrm/yield/' + year + '/' + month + '/YIELD_' + dtstr + '.csv.gz'
    if s3fileexists(s3fname):
        return True
    else:
        return False

def s3boffilepresent(dtstr):
    year  = dtstr[:4]
    month = dtstr[4:6]
    s3fname = 'ay-emr-job/nrm/bof/' + year + '/' + month + '/BKG_OD_' + dtstr + '.csv.gz'
    if s3fileexists(s3fname):
        return True
    else:
        return False

def s3baffilepresent(dtstr):
    year  = dtstr[:4]
    month = dtstr[4:6]
    s3fname = 'ay-emr-job/nrm/baf/' + year + '/' + month + '/AV_OD_' + dtstr + '.csv.gz'
    if s3fileexists(s3fname):
        return True
    else:
        return False

def s3cffilespresent(dtstr, daysahead = 350):
    year  = dtstr[:4]
    month = dtstr[4:6]
    day   = dtstr[6:8]   
    dt = datetime.strptime(dtstr, '%Y%m%d')
    s3fnames = []
    for d in range(daysahead):
        depdt = dt + timedelta(days=d)
        depdtstr = datetime.strftime(depdt, '%Y%m%d') 
        s3fname = 'nrm/cf/' + year + '/' + month + '/' + day + '/cf_' + dtstr + '_' + depdtstr + '.csv.gz'
        s3fnames.append(s3fname)
        #if not s3fileexists(s3fname):
        #    return False
    s3fldr = 'ay-emr-job/nrm/cf/' + year + '/' + month + '/' + day
    if not s3filesexists(s3fnames, s3fldr):
        return False
    return True
                                         
if __name__ == '__main__':
    gets3files('ay-emr-job/nrm/bff/2019/02/13/')

  

