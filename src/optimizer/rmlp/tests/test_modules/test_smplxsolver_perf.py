#------------------------------------------------------------------------------
#
#  Tests to check simplex solver.
#
#-------------------------------------------------------------------------------

import unittest
import os
import sys
import numpy as np
import random
from datetime import datetime

sys.path.append('../../src')
sys.path.append('../../..')

from defs import *
from smplxsolver import *
from lpsolver import *


class TestSmplxSolverPerf(unittest.TestCase):


    def setUp(self):
        pass


    def test_1(self):
        nrows, ncols = 200, 2000
        # Generate matrix.
        A = np.zeros((nrows,ncols))
        m,n = A.shape
        for j in range(n):
            i1 = random.randint(0,m-1)
            i2 = random.randint(0,m-1)
            A[i1,j] = 1
            A[i2,j] = 1    
        # Capacity.
        c = np.zeros(m)
        for i in range(m):
            c[i] = random.randint(50,300)
        # Fare.
        f = np.zeros(n)
        for j in range(n):
            f[j] = random.randint(100, 1000)
        # Demand.
        d = np.zeros(n)
        for j in range(n):
            d[j] = random.randint(1, 500)   
 
        # Solve.
        lps = LPSolver(A,c,d,f,[''] * n,[''] * n)

        dt1 = datetime.now()
        val_glpk, sol_glpk = lps.solve_swiglpk('')
        dt2 = datetime.now()
        print "glpk: val,time = ", val_glpk, ",", (dt2 - dt1)

        dt1 = datetime.now()        
        val_rmlp, sol_rmlp = lps.solve_rmlp()
        dt2 = datetime.now()
        print "rmlp: val,time = ", val_rmlp, ",", (dt2 - dt1)

        self.assertTrue(abs(val_glpk - val_rmlp) <= EPS)


if __name__ == "__main__":
    unittest.main()


