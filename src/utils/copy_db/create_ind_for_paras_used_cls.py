import os
import sys
from datetime import date
import ConfigParser

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)
sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector
from cls import *

if __name__ == '__main__':

    curs = dbConnector.get_or_curs()
    for cls in get_clss_():
        tbl_name = 'paras_used_' + cls.lower()
        ind_name = 'paras_used_' + cls.lower() + '_dep_arr_airport'
        q = "create index " + ind_name + " on " + tbl_name + "(depairport,arrairport)"
        curs.execute(q)
        print 'Index for ' + tbl_name + ' is created'
        
