from math import sqrt
import numpy as np
from scipy.stats import norm


from constants import *


class EMSROptimizer:


  def __init__(self, fares, mus, stds):
    """
    @param fares - list of fares
    @param mus - list of means of demand
    @param stds - list of standart deviations
    """
    assert len(fares) == len(mus) == len(stds)

    self.n = len(fares)

    self.fares = fares
    self.mus = mus
    self.stds = stds

    # Make floats
    self.fares = [float(e) for e in self.fares]
    self.mus = [float(e) for e in self.mus]
    self.stds = [float(e) for e in self.stds]
  

  def getProtectionsA(self):
    """
    Calculates nested protection levels based
    on EMSR-a heuristic.
    """

    prots = []
    for j in range(1,self.n):
      y_sum = 0
      for k in range(j):
        fare_ratio = self.fares[j]/self.fares[k]
        y_sum += self.mus[k] + self.stds[k] * norm.ppf(1 - fare_ratio)
      prots.append(y_sum)
    return prots


  def getCapacityProtectionsA(self, cap):
    """
    Calculates nested protections levels with
    given capacity based on EMSR-a heurisitc.
    """

    prots = self.getProtectionsA()
    
    return_prots = []
    for p in prots:
      real_p = min(cap, p)
      return_prots.append(max(0.0, real_p))
    return_prots.append(cap)   
 
    return return_prots


  def getProtectionsB(self):
    """
    Calculates nested protection levels based
    on EMSR-b heuristic.
    """

    # Calculate variance
    vs = [e*e for e in self.stds]
    stds_sum = [sqrt(sum(vs[:i+1])) for i in range(len(vs))]
    
    # Aggregate demand
    mus_sum = [sum(self.mus[:i+1]) for i in range(len(self.mus))]

    # Calculate weighted-average price
    fmus = [e[0]*e[1] for e in zip(self.fares, self.mus)]
    fmus_sum = [sum(fmus[:i+1]) for i in range(len(fmus))]
    wap = [e[0]/e[1] for e in zip(fmus_sum, mus_sum)]

    # Calculate EMSR ratios
    ratios = [self.fares[i+1]/wap[i] for i in range(len(wap) - 1)]

    # Calculate nested protections
    prots = []
    for k in range(len(ratios)):
      if abs(stds_sum[k]) < EPSILON:
        prots.append(mus_sum[k])
      else:
        prot = norm.ppf(1-ratios[k])
        prots.append(max(0.0, mus_sum[k] + stds_sum[k] * prot))    

    return prots


  def getCapacityProtectionsB(self, cap):
    """
    Calculates nested protection levels with
    given capacity based on EMSR-b heurisitic.
    """

    prots = self.getProtectionsB();

    return_prots = []
    for p in prots:
      real_p = min(cap, p)
      return_prots.append(round(max(0.0, real_p), 1))
    return_prots.append(round(cap, 1))

    return return_prots 

#----------------------------------
#----------- Unit tests -----------
#----------------------------------

import unittest
import math

class TestEMSROptimizer(unittest.TestCase):

  def setUp(self):
    pass

  def testEMSRa1(self):
    
    fares = [1050.0, 567.0, 534.0, 520.0]
    mus = [17.3, 45.1, 39.6, 34.0]
    stds = [5.8, 15.0, 13.2, 11.3]

    optimizer = EMSROptimizer(fares, mus, stds)
    prots = optimizer.getProtectionsA()

    self.assertTrue(abs(prots[0] - 16.7) < 0.1)
    self.assertTrue(abs(prots[1] - 38.7) < 0.1)
    self.assertTrue(abs(prots[2] - 55.6) < 0.1)

  def testEMSRa2(self):

    fares = [1050.0, 950.0, 699.0, 520.0]
    mus = [17.3, 45.1, 39.6, 34.0]
    stds = [5.8, 15.0, 13.2, 11.3]

    optimizer = EMSROptimizer(fares, mus, stds)
    prots = optimizer.getProtectionsA()

    self.assertTrue(abs(prots[0] - 9.8) < 0.1)
    self.assertTrue(abs(prots[1] - 50.4) < 0.1)
    self.assertTrue(abs(prots[2] - 91.6) < 0.1)

  def testEMSRb1(self):

    fares = [1050.0, 567.0, 534.0, 520.0]
    mus = [17.3, 45.1, 39.6, 34.0]
    stds = [5.8, 15.0, 13.2, 11.3]

    optimizer = EMSROptimizer(fares, mus, stds)
    prots = optimizer.getProtectionsB()

    self.assertTrue(abs(prots[0] - 16.7) < 0.1)
    self.assertTrue(abs(prots[1] - 50.9) < 0.1)
    self.assertTrue(abs(prots[2] - 83.1) < 0.1)

  def testEMSRb2(self):

    fares = [1050.0, 950.0, 699.0, 520.0]
    mus = [17.3, 45.1, 39.6, 34.0]
    stds = [5.8, 15.0, 13.2, 11.3]

    optimizer = EMSROptimizer(fares, mus, stds)
    prots = optimizer.getProtectionsB()

    self.assertTrue(abs(prots[0] - 9.8) < 0.1)
    self.assertTrue(abs(prots[1] - 53.2) < 0.1)
    self.assertTrue(abs(prots[2] - 96.8) < 0.1)

if __name__ == "__main__":
  unittest.main()




