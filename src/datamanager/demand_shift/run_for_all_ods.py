import os
import sys
import csv
import ConfigParser
from datetime import date
import pickle

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)
#print config.get('PATHS','datamanager')
sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector
from demand_shift_estimate import run
from oandd import *

if __name__ == '__main__':
    
    curs = dbConnector.get_or_curs()
    q = "SELECT path,sum(pax_cnt) as sm\
         FROM ra_data_ds_old\
         GROUP BY path HAVING sm > 100\
         ORDER BY sm DESC"
    curs.execute(q)
    rows = curs.fetchall()
    for row in rows:
        legs = row[0].split(' ')
        if len(legs) > 2:
            continue

        od = None
        if len(legs) == 2:
            first_leg  = legs[0].strip().split('-')
            second_leg = legs[1].strip().split('-')
            if (first_leg[1].strip() == second_leg[0].strip() == 'HEL') is False:
                continue
            od = OandD([first_leg[0].strip(),first_leg[1].strip(),second_leg[1].strip()])
        else:
            leg = legs[0].strip().split('-')
            if leg[0].strip() != 'HEL' and leg[1].strip() != 'HEL':
                continue
            od = OandD([leg[0].strip(),leg[1].strip()])

        # Check whether file already exists.
        # If it does, skip this OD.
        fname = 'output/'+od.to_str()+'.pkl'
        if os.path.isfile(fname):
            continue

        print '########################'
        print od.airports
        print '########################'
        dsm = run(od)
        f = open(fname,'wb')
        pickle.dump(dsm,f)
        f.close()
        print
        print

        





        
