import os
import sys
import csv
import ConfigParser
from datetime import date,datetime,timedelta

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)
sys.path.append(config.get('PATHS','datamanager'))

from flight import *

def main():
    csv_file = csv.writer(open('standbys.csv','wb'),delimiter=',') 
    dto = datetime.now()
    dlt = timedelta(days=365)
    dfrom = dto - dlt
    flights = flight.get_flights()
    for e in flights:
        print e
        fl = flight(e[0],e[1],e[2],dfrom,dto)
        num_deps = fl.get_num_deps()
        num_standbys = fl.get_num_standbys()
        print 'Row written'
        csv_file.writerow([e[0],e[1],e[2],num_deps,num_standbys])

if __name__ == '__main__':
    main()
 
