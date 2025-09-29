import time
import math
from DataReader import *
from pylab import *
from LPSolver import *

class Sparse01Matrix:


  def __init__(self, m = None):

    if m is None:
      self.rows = []
      self.columns = []
      self.removedRows = set()
      self.removedColumns = set()
      self.nrows = 0
      self.ncols = 0
    else:
      self.rows = []
      self.columns = []
      self.removedRows = set()
      self.removedColumns = set()
      self.clusters = []
      self.clusterSets = []

      # Initiate rows and columns lists
      for i in range(m.shape[0]):
        self.rows.append([])
      for i in range(m.shape[1]):
        self.columns.append([])

      # Fill rows and columns lists
      for rowIndex in range(m.shape[0]):
        columnsIndices = list(np.nonzero(m[rowIndex])[0])        
        self.rows[rowIndex] = columnsIndices
        for columnIndex in columnsIndices:
          self.columns[columnIndex].append(rowIndex)

      self.nrows = len(self.rows)
      self.ncols = len(self.columns)

  
  def origShape(self):
    return self.nrows, self.ncols 

 
  def shape(self):
    ncols = len(self.columns) - len(self.removedColumns)
    return self.nrows, ncols

