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
  num = 0
  q = "START n = node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       RETURN n.code?,SUM(r.num_pax) AS npax\
       ORDER BY npax DESC"
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
       RETURN n.code?,SUM(r.num_pax) AS npax\
       ORDER BY npax DESC"
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

def vec_npax_day(dt):
  """
  Returns vector of the number
  of passengers travelled from
  airports on given date.

  @arg dt --- date
  """

  # Initialize vector with small ones
  v = np.random.uniform(0.001,0.002,len(code_list))
  v = np.matrix(v)
  v = v.transpose()

  # Find minimum number of passengers
  # for normalization
  q = "START n = node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       RETURN MIN(r.num_pax)"
  results = gdb.query(q)
  min_npax = results[0][0]

  # Find maximum number of passengers
  # for normalization
  q = "START n = node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       RETURN MAX(r.num_pax)"
  results = gdb.query(q)
  max_npax = results[0][0]

  # Query the data
  q = "START n = node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       WHERE r.dt = '" + dt.strftime('%Y-%m-%d') + "'\
       RETURN n.code?,SUM(r.num_pax)"
  results = gdb.query(q)
  for result in results:
    orgn = result[0]
    npax = result[1]
    try:
      npos = code_list.index(orgn)
      v[npos,0] = float(npax)/max_npax
      # FIXME: add here noise, not constant
      if v[npos,0] < 0.001:
        v[npos,0] = float(np.random.uniform(0.001,0.002,1))
    except Exception as e:
      print e
  return v 

def vec_rev_day(dt):
  """
  Returns vector of revenues
  flown from airports on given date.

  @arg dt --- date
  """

  # Initialize vector with zeroes
  v = np.random.uniform(0.001,0.002,len(code_list))
  v = np.matrix(v)
  v = v.transpose()

  #v = np.matrix(0.001 * np.ones( (len(code_list),1) ))

  # Find maximum flown revenue during day
  # for normalization.
  q = "START n = node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       RETURN MAX(r.rev)"
  results = gdb.query(q)
  max_rev = results[0][0]

  # Query the data
  q = "START n = node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       WHERE r.dt = '" + dt.strftime('%Y-%m-%d') + "'\
       RETURN n.code?,SUM(r.rev)"
  results = gdb.query(q)
  for result in results:
    orgn = result[0]
    rev = result[1]

    try:
      npos = code_list.index(orgn)
      v[npos,0] = float(rev)/max_rev
      # FIXME: add here noise, not constant
      if v[npos,0] < 0.001:
        v[npos,0] = float(np.random.uniform(0.001,0.002,1))
    except:
      pass

  # Make integer in order to speed-up
  # calculation (possibly). Truncation
  # error assumed to be negligible.
  return v

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

  fill_code_list_npax()

  min_dt = min_date()
  max_dt = max_date()

  dts = []
  dt = min_dt
  vs = sd_npax_rev_vec_day(dt)
  dts.append(dt.strftime('%Y-%m-%d'))
  dt = dt + timedelta(days=1)

  while dt <= max_dt:
    v = sd_npax_rev_vec_day(dt)
    print dt.strftime('%Y-%m-%d')
    dts.append(dt.strftime('%Y-%m-%d'))
    vs = np.concatenate((vs,v),axis=1)
    dt = dt + timedelta(days=1)
  
  pickle.dump([dts,vs],open('features.pkl','w'))
 


























