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

from cls import *
from db_connector import dbConnector

if __name__ == '__main__':
    curs = dbConnector.get_or_curs()
    for cls in get_clss_():
        if cls is None:
            continue
        tbl_name = 'paras_used_' + cls
        q = "CREATE TABLE " + tbl_name + "(\
             id INT PRIMARY KEY AUTO_INCREMENT,\
             fst_tkt VARCHAR(255),\
             flightdate DATE,\
             depairport CHAR(3),\
             arrairport CHAR(3),\
             carrier CHAR(2),\
             pax INT,\
             bkg_cre_dt_tm DATETIME,\
             bookingclass CHAR(1))"
        curs.execute(q)
        print 'Table ',tbl_name, 'is created'
