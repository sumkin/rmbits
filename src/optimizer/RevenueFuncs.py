from math import pi, sqrt, exp
import scipy.integrate as integrate
from scipy.special import erf, erfc
import numpy as np
import time
import matplotlib.pyplot as plt

from EMSROptimizer import *
from PiecewiseLinearApproximator import *


def getRevenueClassFunc(f, m, std, b1, b2):
  assert m > EPSILON
  assert std > -EPSILON

  stdfsqrt2 = (std * f) / sqrt(2)
  stdfsqrt2pi = (std * f) / sqrt(2*pi)

  if abs(std) <= EPSILON:
    K = f * m
  else:
    mstd2 = m / (sqrt(2)*std)
    K = stdfsqrt2pi * exp(-mstd2 * mstd2) + ((m * f) / 2) * (1 + erf(mstd2))

  b2b1 = b2 - b1
  mf = m * f
  sqrt2std = sqrt(2) * std
  sqrtpi = sqrt(pi)

  if abs(std) <= EPSILON:
    b2b1f = b2b1 * f
    def resFunc(y):
      if y <= b2:
        x = y - b1
      else:
        x = b2b1
      if x >= m:
        return mf
      else:
        return x * f
    return resFunc
  else:
    zb2b1 = (b2b1 - m) / sqrt2std
    val = stdfsqrt2 * (zb2b1 * erfc(zb2b1) - exp(-zb2b1*zb2b1)/sqrtpi) + K
    def resFunc(y):
      if y <= b2:
        x = y - b1
      else:
        return val
      z = (x - m) / sqrt2std
      return stdfsqrt2 * (z * erfc(z) - exp(-z*z)/sqrtpi) + K  
    return resFunc


def getRevenueFuncAndProts(fs, ms, stds, cap):
  if len(fs) > 1:
    assert all(fs[i] >= fs[i+1] for i in range(len(fs)-1))
  assert len(fs) == len(ms)
  assert len(ms) == len(stds)

  optimizer = EMSROptimizer(fs, ms, stds)

  prots = optimizer.getCapacityProtectionsB(cap)
  limits = []
  prevProt = 0.0
  for prot in prots:
    limits.append([prevProt, prot])
    prevProt = prot

  assert len(limits) == len(fs)

  revs = []
  for i in range(len(fs)):
    rev = getRevenueClassFunc(fs[i], ms[i], stds[i], limits[i][0], limits[i][1])
    revs.append(rev)


  def resFunc(y):
    return sum([max(0.0, e(y)) for e in revs])


  return resFunc, prots


if __name__ == "__main__":
  fs = [300.0, 200.0, 100.0]
  ms = [50.0, 15.0, 250.0]
  stds = [10.0, 10.0, 10.0]
  cap = 100.0

  revFunc = getRevenueFunc(fs, ms, stds, cap)
  approximator = PiecewiseLinearApproximator(revFunc, 0, cap, 0.1)
  approximator.approximate()
  PLinearFunc = approximator.getPLinearFunc()

  x = 0.0
  maxv = 0.0
  while x <= cap:
    maxv = max(maxv, abs(revFunc(x) - PLinearFunc(x)))
    x += 0.01
  print "maxv = ", maxv

