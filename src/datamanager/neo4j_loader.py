import os
import sys
import ConfigParser

from datetime import date,timedelta

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector

class Neo4jLoader:

  def __init__(self):
    self.ads_curs = dbConnector.get_ads_curs()
    self.neo4j_conn = dbConnector.get_neo4j_conn()

  def load_fcst_err(self):
    pass

  def load_bkgs(self):
    pass

  def load_dbc(self):
    pass


if __name__ == '__main__':
  dt = date(2013,7,7)
  nl = Neo4jLoader()
  nl.daily_bookings(dt)

  
