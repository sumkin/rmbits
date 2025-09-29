#!/usr/bin/env python

"""segmentation.py Module finds the change in 
multivariate time series read from pickle file"""

__author__ = 'Fedor Nikitin'
__maintainer__ = 'Fedor Nikitin'
__email__ = 'fedor.nikitin@gmail.com'

#############################
#
# Import third party modules
#
#############################
import sys
import pickle
import numpy as np
from datetime import date, timedelta
from matplotlib import pyplot as plt
import segment

#####################
#
# Import own modules
#
#####################
from pca import get_pca


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

if __name__ == '__main__':
  pca = get_pca('features.pkl',0)
  data = segment.DataContainer(range(len(pca)),pca)

  segmenter = segment.TopDown(segment.QuadraticRegression, 10)
  
  fits = segmenter.segment(data)

  lines = fits.fits

  xticks_i = range(len(pca))
  xticks_i = [e for e in xticks_i if e % 7 == 0]

  xticks_v = []
  dt_st = date(2011,11,1)
  for i in xticks_i:
    dt = dt_st + timedelta(days=i)
    xticks_v.append(dt.strftime('%Y-%m-%d'))

  print 'Error:',fits.error
  fs = fits.fits
  for f in fs:
    start = (dt_st + timedelta(days=int(f.xrange[0]))).strftime('%Y-%m-%d')
    end = (dt_st + timedelta(days=int(f.xrange[1]))).strftime('%Y-%m-%d')
    print start,end

  fits.plot()
  segment.plt.xticks(xticks_i,xticks_v,rotation='vertical')
  segment.plt.show()
  
