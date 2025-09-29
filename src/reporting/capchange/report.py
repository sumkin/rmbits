import os
import sys
import ConfigParser
import numpy as np
from datetime import date, timedelta

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from flight import *
from departure import *

dfrom = date(2012,3,1)
dto = date(2013,3,1)

if __name__ == '__main__':

  flights = Flight.get_lh_managed_flights()
  print 'Number of flights:',len(flights)
  for orgn,dstn,fltnum in flights:
    fl = Flight(orgn,dstn,fltnum,dfrom,dto)
    st_m_1 = fl.get_vircap_stats(daysprior='-1',cmpt='J')
    st_5 = fl.get_vircap_stats(daysprior='5',cmpt='J')

    # Make dictionaries
    st_m_1_d = {}
    for k,v in st_m_1:
      st_m_1_d[k] = v
    st_5_d = {}
    for k,v in st_5:
      st_5_d[k] = v

    st_m_1_k = st_m_1_d.keys()
    st_5_k = st_5_d.keys()

    keys = list(set(st_m_1_k) & set(st_5_k))
    keys.sort()

    if len(keys) != 0:

      diff = [st_5_d[k]-st_m_1_d[k] for k in keys]
    
      # ORGN,DSTN,FLTNUM,LEN(diff)
      length = len(diff)
      mean = np.mean(diff)
      std = np.std(diff)

      length_pos = len([e for e in diff if e > 0])
      mean_pos = np.mean([e for e in diff if e > 0])
      std_pos = np.std([e for e in diff if e > 0])

      length_neg = len([e for e in diff if e < 0])
      mean_neg = np.mean([e for e in diff if e < 0])
      std_neg = np.std([e for e in diff if e < 0])

      print orgn,dstn,fltnum,length,mean,std,length_pos,mean_pos,std_pos,length_neg,mean_neg,std_neg

    else:

      print orgn,dstn,fltnum,len(keys)




