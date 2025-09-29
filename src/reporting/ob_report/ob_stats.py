import os
import sys
import pickle
import ConfigParser
from datetime import date

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

ob_data_path = config.get('PATHS','ob_data')

gains = 0.0
costs = 0.0

for fname in os.listdir(ob_data_path):
  if fname.split('.')[1] != 'pkl':
    continue
  data = pickle.load(open(ob_data_path+'/'+fname,'rb'))
  
  """Data format is the following
  ['YYYY-MM-DD': [actual ob,allowed ob, gains, costs]
  """
  gains += sum([e[1][2] for e in data if e[1][2] is not None])
  costs += sum([e[1][3] for e in data if e[1][3] is not None])

print 'gains:',int(gains),'EUR'
print 'costs:',int(costs),'EUR'

