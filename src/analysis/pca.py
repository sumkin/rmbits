#!/usr/bin/env python

"""pca.py Module calculates PCA transformation
for time series read from pickle file"""

__author__ = 'Fedor Nikitin'
__maintainer__ = 'Fedor Nikitin'
__email__ = 'fedor.nikitin@finnair.com'

#############################
#
# Import third party modules
#
#############################
import os
import sys
import pickle
import numpy as np
from datetime import date, timedelta
from matplotlib import pyplot as plt, mlab
from rpy2 import robjects
from rpy2.robjects.packages import importr

#####################
#
# Import own modules
#
#####################
from features import get_code_list

################################
#
# Global variables and settings
#
################################

#######
#
# Code
#
#######

def read_first_pc(holidays=[],h_r=0.5,breaks_r=2):
  d = os.path.dirname(os.path.realpath(__file__))
  return get_pca(d+'/features.pkl',0,holidays=holidays,h_r=h_r,breaks_r=breaks_r)

def get_pca(fname,ind,holidays=[],h_r=0.5,breaks_r=2):
  d = os.path.dirname(os.path.realpath(__file__))
  r = robjects.r
  path = d + '/segmentation.R'
  importr('bfast')
  r.source(path)

  code_list = get_code_list(1000)
  dts,code_list,mat = pickle.load(open(fname,'r'))
  m,n = mat.shape

  dfrom_s = dts[0]
  dto_s = dts[len(dts)-1]

  dfroms = dfrom_s.split('-')
  dtos = dto_s.split('-')

  dfrom = date(int(dfroms[0]),int(dfroms[1]),int(dfroms[2]))
  dto = date(int(dtos[0]),int(dtos[1]),int(dtos[2]))

  dfrom = dfrom.isocalendar()[:2]
  dto = dto.isocalendar()[:2]

  dfrom_r = robjects.IntVector(dfrom)
  dto_r = robjects.IntVector(dto)

  # Make PCA
  print mat
  print mat.shape
  #mr = mat[range(n),:]
  results = mlab.PCA(mat.transpose())

  pcs = results.Y
  ws = results.Wt
  pc = pcs[:,ind]
  w = ws[:,ind]
  for e in w:
    print float(e[0]),' ',
  data = np.asarray(pc).reshape(-1)
  data = list(data)

  #holidays = [['2012-04-01','2012-04-10'],['2012-06-20','2012-06-25'],['2012-12-22','2012-12-26']]
  #holidays = []

  if len(holidays) != 0:
    datas = []
    prev_end = 0
    for holiday in holidays:
      print holiday
      start = dts.index(holiday[0])
      end = dts.index(holiday[1])
      datas.append(data[prev_end:start])
      datas.append(data[start:end])
      prev_end = end 
    datas.append(data[prev_end:])
  else:
    datas = [data]

  ress = []
  for data in datas:
    print len(data)
    data_r = robjects.FloatVector(data)
    if len(data) >= 50:
      res_r = r.segment(data_r,dfrom_r,dto_r,h=h_r,breaks=breaks_r)
      res = robjects.default_ri2py(res_r) 
      ress.append(res)
    else:
      ress.append([data,['null']*len(data)])  

  # Combine results
  res = [[],[]]
  for r in ress:
    res[0] += list(r[0])
    res[1] += list(r[1])

  return dts,res

if __name__ == '__main__':
  dts,data = read_first_pc(holidays=[],h_r=0.5,breaks_r=2)
  orig,ltr = data

  print 'orig',len(orig)
  print 'ltr',len(ltr)

  plt.plot(orig)
  plt.show()




