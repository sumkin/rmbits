import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy

from Sparse01Matrix import *
from SparseMatrix import *
from RevenueFuncs import *
from PiecewiseLinearApproximator import *


class StochLPSolver:


  def __init__(self, m, f, c, d, std):
    self.m = deepcopy(m)
    self.f = deepcopy(f)
    self.c = deepcopy(c)
    self.d = deepcopy(d)
    self.std = deepcopy(std)
    self.equalConstraintsIndices = []
    self.integerVariables = []    
    self.yVarsInfo = []


  def processColumnAndDuplicatesLP(self, index, duplicates, nonZeroRows):
    columnIndices = [index] + duplicates
    fares = [self.f[i] for i in columnIndices]
    if len(nonZeroRows) == 0:
      maxc = max(self.c)
    else:
      maxc = max([self.c[i] for i in nonZeroRows])
    demand = [self.d[i] for i in columnIndices]
    std = [self.std[i] for i in columnIndices]

    fdstd = zip(fares, demand, std)
    fdstd = sorted(fdstd, key = lambda x: x[0], reverse=True)

    fares = [e[0] for e in fdstd]
    demand = [e[1] for e in fdstd]
    std = [e[2] for e in fdstd]

    eps = 1.0
    revFunc, prots = getRevenueFuncAndProts(fares, demand, std, maxc)
    approximator = PiecewiseLinearApproximator(revFunc, 0, maxc, eps)
    approximator.approximate()
    #approximator.validate()
    pLinearFunc = approximator.getPLinearFunc()
 
    numBreaks = approximator.getNumBreaks()
    minn, maxx = approximator.getMinMax()

    '''
    x = 0.0
    xs = []
    y1s = []
    y2s = []
    while x <= maxc:
      y1 = revFunc(x)
      y2 = pLinearFunc(x)
      xs.append(x)
      y1s.append(y1)
      y2s.append(y2)
      #assert abs(y1 - y2) <= eps + EPSILON 
      x += 0.1
      #print "x = ", x, ", y1 = ", y1, ", y2 = ", y2
    plt.plot(xs, y1s)
    plt.plot(xs, y2s)
    plt.show()
    '''

    # Add y variable.
    self.f.append(0.0)
    self.d.append(maxc)
    yIndex = self.m.addNewColumn(nonZeroRows, [1.0]*len(nonZeroRows))
    self.yVarsInfo.append([columnIndices, prots])

    # Add z variable.
    newRowIndices = []
    self.f.append(1.0)
    for i in range(numBreaks):
      coeffs = approximator.getLinearCoeffsForBreak(i)
    self.d.append(maxx)
    zIndex = self.m.addNewColumn([], [])
    for i in range(numBreaks):
      coeffs = approximator.getLinearCoeffsForBreak(i)
      newRowIndex = self.m.addNewRow([yIndex, zIndex], [-coeffs[0], 1.0])
      newRowIndices.append(newRowIndex)
      self.c.append(coeffs[1])
    
    return newRowIndices


  def convertToLP(self):
    index = self.m.getNextNotProcessedColumn()
    origNumCols = self.m.origShape()[1]
    while index != -1:
      if index >= origNumCols:
        break
      duplicates, nonZeroRows = self.m.getNotProcessedDuplicatesForColumn(index)
      self.processColumnAndDuplicatesLP(index, duplicates, nonZeroRows)
      self.m.markColumnProcessed(index)
      for duplicate in duplicates:
        self.m.markColumnProcessed(duplicate)
      index = self.m.getNextNotProcessedColumn()
    self.m.markProcessedColumnsAsRemoved()  


  def removeRedundantRows(self):
    for i in range(len(self.m.rows)):
      res = 0.0
      for j in self.m.rows[i]:
        res += self.m.values[(i,j)] * self.d[j]
      if res + EPSILON <= self.c[i]:
        self.m.removedRows.add(i)


  def solveLP(self):
    removedRows = self.m.getRemovedRows()
    removedColumns = self.m.getRemovedColumns()

    f = []
    for i in range(len(self.f)):
      if i in removedColumns:
        continue
      f.append(self.f[i])

    d = []
    for i in range(len(self.d)):
      if i in removedColumns:
        continue
      d.append(self.d[i])

    c = []
    for i in range(len(self.c)):
      if i in removedRows:
        continue
      c.append(self.c[i])

    assert all(e > 0 for e in c)

    lpsolver = LPSolver(self.m, c, d, f)
    val, sol  = lpsolver.solve_swiglpk("stoch-lp")
    return val, sol


  def getOriginalSolution(self, sol):
    i = 0
    xSols = {}
    while i < len(sol):
      index = i / 2
      cap = sol[i]
      yVarInfo = self.yVarsInfo[index]
      for k in range(len(yVarInfo[0])):
        xIndex = yVarInfo[0][k]
        xSol = min(yVarInfo[1][k], max(0.0, cap))
        xSols[xIndex] = xSol
        cap = cap - xSol 
      i += 2
    indices = sorted(xSols.keys(), lambda x,y : x > y)   
    
    res = []
    for index in indices:
      res.append(xSols[index])
    return res


if __name__ == "__main__":

  m = np.array([[1.0],[0.0]])

  sm = SparseMatrix(Sparse01Matrix(m))
  f = [10.0]
  c = [100.0, 100.0]
  d = [50.0]
  std = [1000.0]

  detSolver = LPSolver(m, c, d, f)
  detVal, detSol = detSolver.solve_swiglpk("det-lp")
  print "deterministic = ", detVal, detSol

  stochSolver = StochLPSolver(sm, f, c, d, std)
  stochSolver.convertToLP()
  stochVal, stochSol = stochSolver.solveLP()
  print "stochacstic = ", stochVal, stochSol

  stochSolver.getOriginalSolution(stochSol)


