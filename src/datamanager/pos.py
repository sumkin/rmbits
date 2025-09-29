import pandas as pd

from s3utils import *


class POS:

    def __init__(self):
        pass

    @staticmethod
    def get_av_all():
        '''
        Find all POS from the last availability file.
        '''
        lastavfile = s3getlastavfile()
        df = pd.read_csv('s3://'+lastavfile)
        res = df['POS'].unique()
        return res


    @staticmethod
    def get_fcst_all():
        ''' 
        Find all POS from last forecast files.
        '''
        res = None
        fnames = s3getlastfcstfiles()
        for fname in fnames:
            print fname
            df = pd.read_csv('s3://ay-emr-job/'+fname)
            if res is None:
                res = df[['POS']].drop_duplicates()
            else:
                res = pd.concat([res, df[['POS']]]).drop_duplicates().reset_index(drop=True)
        return res


if __name__ == '__main__':
    poses = POS.get_fcst_all()
    print 'len(poses) = ', len(poses)
    print 'poses = ', poses





