import os
import sys
import ConfigParser
from datetime import date, datetime, timedelta

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)
sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector
from crm_case import crmCase

if __name__ == '__main__':
  dt_start = date(2012,12,20)
  dt = dt_start
  while dt < datetime.now().date():
    num_pax = crmCase.get_db_cases(dt,dt)[0]
    print dt,num_pax
    dt = dt + timedelta(days=1)
