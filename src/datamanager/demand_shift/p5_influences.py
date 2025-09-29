import os
import sys
import csv
import ConfigParser

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector
from cls import *
from leg import *

def old_dmd(leg,cls):
    curs = dbConnector.get_or_curs()
    q = "SELECT SUM(pax_cnt) FROM ra_data_ds_old\
         WHERE cls = '" + cls + "' AND\
               path LIKE '%" + leg[0] + "-" + leg[1] + "%'"
    curs.execute(q)
    row = curs.fetchone()
    if row[0] is None:
        res = 0
    else:
        res = row[0]
    return res

def new_dmd(leg,cls):
    curs = dbConnector.get_or_curs()
    q = "SELECT SUM(pax_cnt) FROM ra_data_ds_new\
         WHERE cls = '" + cls + "' AND\
               path LIKE '%" + leg[0] + "-" + leg[1] + "%'"
    curs.execute(q)
    row = curs.fetchone()
    if row[0] is None:
        res = 0
    else:
        res = row[0]
    return res

def get_all_legs():
    curs = dbConnector.get_or_curs()
    q = "SELECT DISTINCT online_orgn,online_dstn\
         FROM ra_data_ds_old\
         WHERE online_orgn = 'HEL' or online_dstn = 'HEL'"
    curs.execute(q)
    rows = curs.fetchall()
    res = [[e[0],e[1]] for e in rows]
    return res

if __name__ == '__main__':
    legs = leg.get_managed_legs()
    writer = csv.writer(open('p5_influences.csv','wb'))
    for leg in legs:
        for cls in get_clss_():
            old_d = old_dmd(leg,cls)
            new_d = new_dmd(leg,cls)
            print leg,cls,': ',old_d,' > ',new_d
            writer.writerow([leg[0],leg[1],cls,old_d,new_d])
        print '#########################'


