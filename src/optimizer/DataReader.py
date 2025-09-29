import csv
import numpy as np
from MFileParser import *

class DataReader:


  def __init__(self, matrixFName, capFName = None, fareFName = None, demandFName = None):
    self.matrixFName = matrixFName
    self.capFName = capFName
    self.fareFName = fareFName
    self.demandFName = demandFName


  def setCapacityFile(self, capFName):
    self.capFName = capFName

  
  def setFareFile(self, fareFName):
    self.fareFName = fareFName


  def setDemandFile(self, demandFName):
    self.demandFName = demandFName


  def getMatrix(self):
    mparser = MFileParser(self.matrixFName)
    mparser.parse()
    return mparser.getMatrix()


  def getCapacities(self):
    with open(self.capFName) as csvfile:
      reader = csv.reader(csvfile)
      caps = []
      for row in reader:
        if len(row) == 0:
          continue
        caps.append(int(row[0]))
      capVector = [0.0] * len(caps) 
      i = 0
      for c in caps:
        capVector[i] = c
        i += 1
    return capVector


  def getFares(self):
    with open(self.fareFName) as csvfile:
      reader = csv.reader(csvfile)
      fares = []
      for row in reader:
        if len(row) == 0:
          continue
        fares.append(float(row[0]))
      fareVector = [0.0] * len(fares)
      i = 0
      for f in fares:
        fareVector[i] = f
        i += 1
    return fareVector


  def getDemand(self):
    with open(self.demandFName) as csvfile:
      reader = csv.reader(csvfile)
      demands = []
      for row in reader:
        if len(row) == 0:
          continue
        demands.append(float(row[0]))
      demandVector = [0.0] * len(demands) 
      i = 0
      for d in demands:
        demandVector[i] = d
        i += 1
    return demandVector 


  def getDemandStds(self):
    with open(self.demandFName) as csvfile:
      reader = csv.reader(csvfile)
      stds = []
      for row in reader:
        if len(row) == 0:
          continue
        stds.append(float(row[1]))
      stdVector = np.zeros(len(stds), dtype=np.float)
      i = 0
      for std in stds:
        stdVector[i] = std
        i += 1
    return stdVector


if __name__ == "__main__":
  dr = DataReader("../data/simplest/aij_a.m",\
                  "../data/simplest/ci_a.csv",\
                  "../data/simplest/fj_a.csv",\
                  "../data/simplest/udj_a.csv")

  m = dr.getMatrix()
  print "matrix dimension: ", m.shape
 
  c = dr.getCapacities()
  print "capacity dimension: ", c.shape

  f = dr.getFares()
  print "fare dimension: ", f.shape

  d = dr.getDemand()
  print "demand dimension: ", d.shape
  print "d = ", d
  
  stds = dr.getDemandStds()
  print "std dimension: ", d.shape
  print "stds = ", stds


