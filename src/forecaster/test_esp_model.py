import os
import sys
import shlex
import ConfigParser

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))
sys.path.append(config.get('PATHS','forecaster'))

from fcst_data_reader import *
from split_history import *
from esp_model import *
from cls import *

#sh = splitHistory('014')
#fdr = fcstDataReader('HEL','RIX','03765','W',1,6,sh)
#print fdr.get_fcst_minus_booked_vals('uncons',0)

print get_esp_params([['HEL','RIX','03749'],
                      ['RIX','HEL','03750'],
                      ['HEL','RIX','03765'],
                      ['RIX','HEL','03766'],
                      ['HEL','RIX','03767'],
                      ['RIX','HEL','03768'],
                      ['HEL','RIX','03769'],
                      ['RIX','HEL','03770']],
                      [1,2,3,4,5,6,7],'006',[0],get_clss_())
