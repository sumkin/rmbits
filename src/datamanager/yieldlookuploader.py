import gzip
import pickle
import boto3
import subprocess
from io import BytesIO


class YieldLookupLoader:

    def __init__(self, srcdate):
        self.srcdate = srcdate


    def get(self):
        srcyear = self.srcdate[:4]
        srcmonth = self.srcdate[4:6]
        srcday = self.srcdate[6:8]

        bucket = 'ay-rmp-home'
        fname = 'yldlkppkl_' + self.srcdate + '.pkl.gz'
        lfname = '/tmp/' + fname

        # Copy file.
        s3 = boto3.resource('s3')
        with open(lfname, 'wb') as data:
            s3.Bucket(bucket).download_fileobj('nrm/yldlkppkl/' + srcyear + '/' + srcmonth + '/' + fname, data)
        
        # Load model.
        yl = None
        with gzip.open(lfname, 'rb') as fout:
            yl = pickle.load(fout)
        assert yl is not None
 
        # Remove file.
        subprocess.check_output(['rm', lfname])

        return yl


if __name__ == '__main__':
    srcdate = '20200129'
    yll = YieldLookupLoader(srcdate)
    yl = yll.get()
    print('yl = ', yl)
    print('Done')



