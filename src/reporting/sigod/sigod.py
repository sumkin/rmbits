import os
import sys
import pickle
from datetime import date,datetime
import ConfigParser

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))
sys.path.append(config.get('PATHS','emailui'))

from db_connector import dbConnector

path_to_data = config.get('PATHS','sigod_data')

SIGOD_LENGTH = 2400

def get_sigod_list(dfrom,dto):
  sigod_list = []
  curs = dbConnector.get_or_curs()
  q = "SELECT trip_orgn,online_orgn,\
              online_dstn,trip_dstn,\
              SUM(tot_client_net_net_rev) as sm\
       FROM ra_data\
       GROUP BY trip_orgn,online_orgn,\
                online_dstn,trip_dstn\
       ORDER BY sm DESC LIMIT "+str(SIGOD_LENGTH)
  curs.execute(q)
  row = curs.fetchone()
  while row is not None:
    sigod_list.append(row)
    row = curs.fetchone()
  return sigod_list

def compare_with_last(sigod_list):
  """
  Returns dictionary
    'added' => ['HEL-OSL', ...]
    'removed' => ['LHR-BKK', ...]
  """

  # Find the latest
  fnames = []
  for fname in os.listdir(path_to_data):
    fnames.append(fname)
  fnames.sort()

  # Last one is just created, the second is correct one
  fname = fnames[len(fnames)-2]
  
  sigod_list_old = pickle.load(open(path_to_data+'/'+fname,'rb'))

  so_new = [e[:4] for e in sigod_list]
  so_old = [e[:4] for e in sigod_list_old]

  added = list( set(so_new) - set(so_old) )
  removed = list( set(so_old) - set(so_new) )

  return added,removed

if __name__ == '__main__':

  dfrom = date(2012,1,1)
  dto = date(2013,1,1)

  sigod_list = get_sigod_list(dfrom,dto)

  fname = 'sigod_'+datetime.now().strftime('%Y-%m-%d_%H:%M')+'.pkl'
  pickle.dump(sigod_list,open(path_to_data+'/'+fname,'wb+'))

  print 'File created...'

  added,removed = compare_with_last(sigod_list)

  print added,removed





