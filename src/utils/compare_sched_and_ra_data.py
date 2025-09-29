import os
import sys
import csv
import ConfigParser
from datetime import date

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)
sys.path.append(config.get('PATHS','datamanager'))

from db_connector import *

if __name__ == '__main__':
    curs = dbConnector.get_or_curs()
    q = "SELECT DISTINCT path, flight_nums, dep_dates\
         FROM ra_data"
    curs.execute(q)
    rows = curs.fetchall()
    for row in rows:

        paths = row[0]
        flight_nums = row[1]
        dep_dates = row[2]

        paths_l = paths.split(' ')
        flight_nums_l = flight_nums.split(' ')
        dep_dates_l = dep_dates.split(' ')

        if len(paths_l) != len(flight_nums_l) or\
           len(flight_nums_l) != len(dep_dates_l):
            print 'Weird entry: ',paths_l,
            print flight_nums_l,
            print dep_dates_l
            continue

        for i in range(0,len(paths_l)):
            path = paths_l[i].strip()
            flight_num = flight_nums_l[i].strip()
            dep_date = dep_dates_l[i].strip()
            year = int(dep_date[0:4])
            month = int(dep_date[4:6])
            day = int(dep_date[6:8])
            dt = date(year,month,day)
            orgn = path.split('-')[0].strip()
            dstn = path.split('-')[1].strip()

            q = "SELECT * FROM sched_tmp WHERE\
                 lo = '" + orgn + "' AND\
                 ld = '" + dstn + "' AND\
                 fn = '" + flight_num[1:] + "' AND\
                 ddt = '" + dt.strftime('%Y-%m-%d') + " 00:00:00'"
            curs.execute(q)
            sub_row = curs.fetchone()
            if sub_row is None:
                print 'Exception: ',orgn,dstn,flight_num,dt.strftime('%Y-%m-%d')

   





