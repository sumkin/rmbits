import os
import sys
import ConfigParser
from datetime import date, timedelta
import numpy as np
from matplotlib import mlab, pyplot as plt

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector

gdb = dbConnector.get_neo4j_conn()

def get_code_list(thrsh=None):
  ans = []
  num = 0
  q = "START n = node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       RETURN n.code?,SUM(r.rev) AS rev\
       ORDER BY rev DESC"
  results = gdb.query(q)
  for result in results:
    code = result[0]
    npax = result[1]
    if code is not None:
      if thrsh is not None and num > thrsh:
        break
      ans.append(code)
    num += 1

  # Take other direction
  q = "START n=node(*)\
       MATCH (n)<-[r:FROM_TO_DAILY]-(m)\
       RETURN n.code?,SUM(r.rev) AS rev\
       ORDER BY rev DESC"
  results = gdb.query(q)
  for result in results:
    code = result[0]
    npax = result[1]
    if code is not None:
      if thrsh is not None and num > thrsh:
        break
      if code not in ans:
        ans.append(code)
    num += 1
  return ans

def rev_ts():
  ans = []
  q = "START n=node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       RETURN r.dt AS dt,SUM(r.rev)\
       ORDER BY dt"
  results = gdb.query(q)
  for result in results:
    ans.append([result[0],result[1]])
  return ans

def npax_ts():
  ans = []
  q = "START n=node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       RETURN r.dt AS dt,SUM(r.num_pax)\
       ORDER BY dt"
  results = gdb.query(q)
  for result in results:
    ans.append([result[0],result[1]])
  return ans

def p2p_npax_ts():
  ans = []
  q = "START n=node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       WHERE n.code? = 'HEL' OR m.code? = 'HEL'\
       RETURN r.dt AS dt,SUM(r.num_pax)\
       ORDER BY dt"
  results = gdb.query(q)
  for result in results:
    ans.append([result[0],result[1]])
  return ans

def yield_ts():
  ans = []
  q = "START n=node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       RETURN r.dt AS dt,SUM(r.rev)/SUM(r.num_pax)\
       ORDER BY dt"
  results = gdb.query(q)
  for result in results:
    ans.append([result[0],result[1]])
  return ans

def nedge_ts():
  ans = []
  q = "START n=node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       RETURN r.dt AS dt,COUNT(r)\
       ORDER BY dt"
  results = gdb.query(q)
  for result in results:
    ans.append([result[0],result[1]])
  return ans

def p2p_npax_ratio_ts():
  ans = []
  npax_data = npax_ts()
  p2p_npax_data = p2p_npax_ts()

  assert len(npax_data) == len(p2p_npax_data)

  for i in range(len(npax_data)):
    ans.append([npax_data[i][0],float(p2p_npax_data[i][1])/npax_data[i][1]])
  return ans

def rw_matrix_day(dt,code_list):
  """
  Returns stochastic matrix of random walk
  where transition probabilities calculated
  based on the number of passengers.

  @arg dt --- date
  """

  # Initialize matrix with zeroes
  m = np.matrix(np.zeros( (len(code_list),len(code_list)) ))

  # Query the data
  q = "START n = node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       WHERE r.dt = '" + dt.strftime('%Y-%m-%d')+"'\
       RETURN n.code?,m.code?,SUM(r.num_pax)"
  results = gdb.query(q)
  for result in results:
    orgn = result[0]
    dstn = result[1]
    npax = result[2]

    try:
      # Define row and column number
      # and fill the element.
      nrow = code_list.index(orgn)
      ncol = code_list.index(dstn)
      m[nrow,ncol] = npax
    except Exception as e:
      print e

  # Add 1 to all elements in order to
  # avoid zeroes in matrix.
  # FIXME: describe what it is needed for.
  # (some properties of graphs...)
  # Laplace smoothing with one.
  m = m + np.ones( m.shape )

  # Do stochastic
  m = do_matrix_stochastic(m)

  return m

def get_min_dt():
  q = "START n=node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       RETURN MIN(r.dt)"
  results = gdb.query(q)
  dt_s = results[0][0]
  dt_l = dt_s.split('-')
  return date(int(dt_l[0]),int(dt_l[1]),int(dt_l[2]))

def get_max_dt():
  q = "START n=node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       RETURN MAX(r.dt)"
  results = gdb.query(q)
  dt_s = results[0][0]
  dt_l = dt_s.split('-')
  return date(int(dt_l[0]),int(dt_l[1]),int(dt_l[2]))

def do_matrix_stochastic(m):
  # Convert all elements to float
  m = m.astype(np.float)

  # Sums all columns
  sm = m.sum(axis=1)

  # Calculate transition probabilities
  for i in range(sm.size):
    for j in range(m[i].size):
      m[i,j] = float(m[i,j])/float(sm[i,0])
  return m

def stat_distr(m):
  """
  Returns stationarity distribution
  of matrix m. By Perron-Frobenius
  theorme this is eigen vector corresponding
  to eigen value 1.
  """

  # np.linalg.eig calculates right
  # eigen vector. That's why transform
  # matrix before calculations.
  m = m.transpose()

  eig_vals, eig_vecs = np.linalg.eig(m)

  eig_val = eig_vals[0]
  eig_vec = eig_vecs[:,0]

  # Eigenvector could be positive or negative.
  # But should be the same sign.
  # Mutiply by -1 if negative.
  if eig_vec[0] < 0:
    eig_vec = -eig_vec

  return eig_vec.astype(np.float)

def feature_matrix():
  code_list = get_code_list(thrsh=70)
  min_dt = get_min_dt()
  max_dt = get_max_dt()

  dt = min_dt
  ans = stat_distr(rw_matrix_day(dt,code_list))

  while dt <= max_dt:
    m = rw_matrix_day(dt,code_list)
    sd = stat_distr(m)
    ans = np.concatenate((ans,sd),axis=1)
    dt = dt + timedelta(days=1)
    print dt
  return ans

def get_pc0(m):
  dfrom = get_min_dt()
  dto = get_max_dt()

  results = mlab.PCA(m.transpose())
  pcs = results.Y
  ws = results.Wt

  pc0 = pcs[:,0]
  return pc0

if __name__ == '__main__':
  m = feature_matrix()
  pc0 = get_pc0(m)

  plt.plot(pc0)
  plt.show()


