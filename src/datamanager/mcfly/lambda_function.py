import json
import boto3
import subprocess

from mcflyreader import *
from yieldlookuploader import *


def lambda_handler(event, context):
    assert len(event['Records']) == 1
    
    record = event['Records'][0]
    fname = record['s3']['object']['key']
    fnames = fname.split('/')
    srcdate, depdate, bkgdate = fnames[5].split('.')[0].split('_')[1:4]

    #srcyl = YieldLookup(srcdate)
    srcyl = YieldLookupLoader(srcdate).get()

    csvfnames3 = 'ay-rmp-home/nrm/mcfly/' + srcdate[:4] + '/' + srcdate[4:6] + '/' + srcdate[6:8] +\
                                     '/MCFLY_' + srcdate + '_' + depdate + '_' + bkgdate + '.csv.gz'
    mcflyreader = McFlyReader(srcdate, depdate, bkgdate, srcyl)
    mcflyreader.read_dfs() 

    csvfname = 'MCFLY_' + srcdate + '_' + depdate + '_' + bkgdate + '.csv'
    csvfname_fp = '/tmp/' + csvfname

    with open(csvfname_fp, 'w') as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(['OPR_OD_TS_KEY','GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_DEPT_DATE',\
                            'GEO_ORGN','GEO_DSTN',\
                            'POS','FF','BKGDATE',\
                            'SCYIELD','MCFLYSD','MCFLYAD','SGCYIELD','AGCYIELD',\
                            'SGCD','AGCD','SCFOUND'])
        for r in mcflyreader.rows():
            csvwriter.writerow(r)

    # Zip file.
    subprocess.check_output(['gzip', csvfname_fp])

    # Copy file to s3.
    s3_client = boto3.client('s3')
    subfolder = srcdate[:4] + '/' + srcdate[4:6] + '/' + srcdate[6:8] + '/' + depdate
    s3_client.upload_file(csvfname_fp + '.gz', 'ay-rmp-home', 'nrm/mcfly/' + subfolder + '/' + csvfname + '.gz')

    # Remove sent file.
    subprocess.check_output(['rm',csvfname_fp+'.gz'])

    return {
        'statusCode': 200,
        'body': json.dumps('mcfly has been processed')
    }


