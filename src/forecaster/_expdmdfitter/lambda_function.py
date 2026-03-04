import csv
import json
import boto3
import subprocess

from expdmdfitter import *


def lambda_handler(event, context):
    assert len(event['Records']) == 1

    record = event['Records'][0]
    fname = record['s3']['object']['key']
    fnames = fname.split('/')
    pcs = fnames[5].split('.')[0].split('_')
    if pcs[0] != 'FCST':
        return {
            'statusCode': 200,
            'body': json.dumps('not FCST_OD file')
        }
    if pcs[1] != 'OD':
        return {
            'statusCode': 200,
            'body': json.dumps('not FCST_OD file')
        }
    if pcs[2] == 'DCP':
        return {
            'statusCode': 200,
            'body': json.dumps('not FCST_OD file')
        }

    srcdate, depdate = pcs[2], pcs[3]
    csvfname3 = 'ay-rmp-home/nrm/expdmd/' + srcdate[:4] + '/' + srcdate[4:6] + '/' + srcdate[6:8] +\
                                     '/expdmd_' + srcdate + '_' + depdate + '.csv.gz'
    csvfname = 'expdmd_' + srcdate + '_' + depdate + '.csv'
    csvfname_fp = '/tmp/' + csvfname

    fitter = ExpDmdFitter(srcdate, depdate)

    with open(csvfname_fp, 'w') as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN',\
                            'POS','TP','FF','SV','SW','AV','AW']) 
        for r in fitter.rows():
            csvwriter.writerow(r)

    # Zip file.
    subprocess.check_output(['gzip', csvfname_fp])

    # Copy file to s3.
    s3_client = boto3.client('s3')
    subfolder = srcdate[:4] + '/' + srcdate[4:6] + '/' + srcdate[6:8] 
    s3_client.upload_file(csvfname_fp + '.gz', 'ay-rmp-home', 'nrm/expdmd/' + subfolder + '/' + csvfname + '.gz')

    # Remove sent file.
    subprocess.check_output(['rm',csvfname_fp+'.gz'])

    return {
        'statusCode': 200,
        'body': json.dumps('expdmdfitter has been processed')
    }



