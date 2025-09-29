import os
import sys
import ConfigParser

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(__file__,'../../../rw.cfg')
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from fcst_data_reader import fcstDataReader
from split_history import splitHistory
from outlier_sd_detector import OutlierSdDetector

if __name__ == '__main__':

    orgn      = sys.argv[1]
    dstn      = sys.argv[2]
    fltnum    = sys.argv[3]
    cls       = sys.argv[4]
    daysprior = sys.argv[5]
    dow       = sys.argv[6]
    shid      = sys.argv[7]  # split history id
    pool_id   = sys.argv[8]  # pool id

    # create splitHistory object
    sh = splitHistory(shid) 

    # create fcstDataReader object
    fdr = fcstDataReader(orgn,dstn,fltnum,\
                         cls,daysprior,dow,sh)

    fcst_vals_d = fdr.get_fcst_vals('uncons',pool_id)
    fcst_vals = fcst_vals_d.values()    

    # create outlier detection object
    lower_sd = 1.45
    upper_sd = 2.88

    osd = OutlierSdDetector(lower_sd,upper_sd)

    print 'Forecast values: '
    fcst_vals.sort()
    print fcst_vals
    print 'Outliers: '
    print osd.get_outliers(fcst_vals)     
    print 'PROS outliers: '
    print [v for v in fdr.get_fcst_outl_vals('uncons',pool_id).values()]





