from datetime import datetime, timedelta
from joblib import Parallel, delayed
import gzip
import pickle
import multiprocessing
import traceback

from yield_lookup import *
from emailutils import *
from s3utils import *
from funcutils import *


def process(fname, dtstr):
    print('Processing ', fname)

    pkl2check = 'ay-emr-job/nrm/yldlkppkl/' + dtstr[:4] +'/' + dtstr[4:6] +\
                                          '/yldlkppkl_' + dtstr + '.pkl.gz'
    if s3fileexists(pkl2check):
        print(pkl2check, ' exists')
        return 0

    yl = YieldLookup(dtstr)

    print('Pickling file...') 
    pklfnamegz = '/mnt/data/tmp/yldlkppkl_' + dtstr + '.pkl.gz'
    with gzip.open(pklfnamegz, 'wb') as fout:
        pickle.dump(yl, fout, protocol=4)

    print('Copying file to s3...')
    try:
        try_x_times(3, subprocess.check_output)(['aws','s3','cp',pklfnamegz,'s3://'+pkl2check])
    except:
        print('Failed on copy...')

    print('Cleaning-up...')
    try:
        try_x_times(3, subprocess.check_output(['rm', pklfnamegz]))
    except:
        print('Failed on removal...')

    return 1


if __name__ == "__main__":
    dt = datetime.now()
    for i in range(10):
        dtstr = datetime.strftime(dt, '%Y%m%d')
        dty,dtm,dtd = dtstr[:4],dtstr[4:6],dtstr[6:8]

        fname = 'ay-emr-job/nrm/yield/'+dty+'/'+dtm+'/YIELD_' + dtstr + '.csv.gz'
        if s3fileexists(fname):
            process(fname, dtstr)
        dt = dt - timedelta(days = 1)

