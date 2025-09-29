#!/usr/bin/env python

"""feature.py: Module calculates different features 
for the network on daily/weekly/monthly level. For
the whole network as well as for specific airport"""

__author__ = 'Fedor Nikitin'
__maintainer__ = 'Fedor Nikitin'
__email__ = 'fedor.nikitin@finnair.com'

#############################
#
# Import third party modules
#
#############################
import numpy as np
import pickle
from isoweek import Week
from neo4jrestclient.client import GraphDatabase
import matplotlib.pyplot as plt
from datetime import date, timedelta

#####################
#
# Import own modules
#
#####################

################################
#
# Global variables and settings
#
################################

# Neo4j database
gdb = GraphDatabase('http://localhost:7474/db/data')

# Numpy printing settings
np.set_printoptions(precision=3,suppress=True)

# List of all airpots
code_list = []

#######
#
# Code 
#
#######

def fill_code_list_npax(thrsh=None):
  global code_list
  code_list = get_code_list(thrsh)

def get_code_list(thrsh=None):
  ans = []
  q = "START n=node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       RETURN n.code?,SUM(r.rev) AS rev\
       ORDER BY rev DESC LIMIT "+str(thrsh)
  results = gdb.query(q)
  num = 0
  for result in results:
    num += 1
    code = result[0]
    rev= result[1]
    if code is not None:
      if thrsh is not None and num > thrsh:
        break
      if code not in ans:
        ans.append(code)
  return ans

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

def npax_day(dt,direct='out'):
  """
  Returns vector of the number
  of passengers travelled from or to
  airport on given date.

  @arg dt --- date
  """

  # Find maximum number of passengers
  q = "START n = node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       RETURN MAX(r.num_pax)"
  results = gdb.query(q)
  max_npax = results[0][0]

  res = []
  for code in code_list:
    # Query the data
    if direct == 'out':
      q = "START n = node(*)\
           MATCH (n)-[r:FROM_TO_DAILY]->(m)\
           WHERE r.dt = '" + dt.strftime('%Y-%m-%d') + "' AND\
                 n.code? = '" + code + "'\
           RETURN SUM(r.num_pax)"
    else:
      q = "START n = node(*)\
           MATCH (n)-[r:FROM_TO_DAILY]->(m)\
           WHERE r.dt = '" + dt.strftime('%Y-%m-%d') + "' AND\
                 m.code? = '" + code + "'\
           RETURN SUM(r.num_pax)"
    result = gdb.query(q)
    npax = result[0][0]
    res.append(float(npax)/max_npax)
  return res

def rev_day(dt,direct='out'):
  """
  Returns vector of revenues
  flown from airports on given date.

  @arg dt --- date
  """

  # Find maximum flown revenue during day
  q = "START n = node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       RETURN MAX(r.rev)"
  results = gdb.query(q)
  max_rev = results[0][0]

  res = []
  for code in code_list:
    # Query the data
    if direct == 'out':
      q = "START n = node(*)\
           MATCH (n)-[r:FROM_TO_DAILY]->(m)\
           WHERE r.dt = '" + dt.strftime('%Y-%m-%d') + "' AND\
                 n.code? = '" + code + "'\
           RETURN SUM(r.rev)"
    else:
      q = "START n = node(*)\
           MATCH (n)-[r:FROM_TO_DAILY]->(m)\
           WHERE r.dt = '" + dt.strftime('%Y-%m-%d') + "' AND\
                 n.code? = '" + code + "'\
           RETURN SUM(r.rev)"
    result = gdb.query(q)
    rev = result[0][0]
    res.append(float(rev)/max_rev)
  return res

def rw_matrix_day(dt):
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
      pass #print e

  # Add 1 to all elements in order to
  # avoid zeroes in matrix.
  # FIXME: describe what it is needed for.
  # (some properties of graphs...) 
  # Laplace smoothing with one.
  m = m + np.ones( m.shape )

  # Do stochastic
  m = do_matrix_stochastic(m)
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

def sd_npax_rev_vec_day(dt):
  """
  Return feature vector consisting of
  of stationarity distribution, number
  of passengers travelled from and
  revenue flown from.
  """
  sd = stat_distr(rw_matrix_day(dt))
  npax = vec_npax_day(dt)
  rev = vec_rev_day(dt)

  return np.concatenate( (sd,npax,rev), axis=0 )

def min_date():
  gdb = GraphDatabase('http://localhost:7474/db/data/')
  q = "START n=node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       RETURN MIN(r.dt)"
  result = gdb.query(q)
  res = result[0][0]
  ress = res.split('-')
  return date(int(ress[0]),int(ress[1]),int(ress[2]))

def max_date():
  gdb = GraphDatabase('http://localhost:7474/db/data/')
  q = "START n=node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       RETURN MAX(r.dt)"
  result = gdb.query(q)
  res = result[0][0]
  ress = res.split('-')
  return date(int(ress[0]),int(ress[1]),int(ress[2]))

if __name__ == '__main__':

  fill_code_list_npax(70)

  min_dt = min_date()
  max_dt = max_date()

  dts = []
  dt = min_dt

  m = None

  while dt <= max_dt:
    dts.append(dt.strftime('%Y-%m-%d'))

    npax_out = npax_day(dt,direct='out')
    npax_in = npax_day(dt,direct='in')
    rev_out = rev_day(dt,direct='out')
    rev_in = rev_day(dt,direct='in')
    sd = stat_distr(rw_matrix_day(dt))

    npax_out = np.matrix(npax_out).transpose()
    npax_in = np.matrix(npax_in).transpose()
    rev_out = np.matrix(rev_out).transpose()
    rev_in = np.matrix(rev_in).transpose()

    v = np.concatenate( (npax_out,npax_in,rev_out,rev_in,sd), axis = 0)
    v += np.matrix(np.random.uniform(0.001,0.002,v.size)).transpose() # Add noise

    print dt

    if dt == min_dt:
      m = v
    else:
      m = np.concatenate( (m,v), axis=1)

    dt = dt + timedelta(days=1)

  pickle.dump([dts,code_list,m],open('features.pkl','w'))
 

