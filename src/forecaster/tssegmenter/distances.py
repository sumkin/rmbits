import unittest
import numpy as np

def dist_inner(s):
  # Input is matrix. Row index - features, column index - time.
  s = np.matrix(s)
  nrows,ncols = s.shape 
  
  dist = np.linalg.norm(s[:,0]-s[:,1])
  for i in range(ncols):
    for j in range(ncols):
      d = np.linalg.norm(s[:,i]-s[:,j])
      if d > dist:
        dist = d
  return dist

def dist_outer(s1,s2):
  # Input is two matrices. Row index - features, column index - time.
  s1 = np.matrix(s1)
  s2 = np.matrix(s2)

  assert s1.shape == s2.shape

  nrows,ncols = s1.shape

###############
#
# Unit testing
#
###############

class DistInnerTests(unittest.TestCase):

  def testFoo(self):
    self.failUnless(False)

  def testOne(self):
    pass

  def testTwo(self):
    pass

def main():
  unittest.main()

if __name__ == '__main__':
  main()



