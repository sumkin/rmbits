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

sys.path.append('../../src')
sys.path.append('../../..')

from defs import *
from smplxsolver import *
from lpsolver import *


class TestSmplxSolver(unittest.TestCase):


    def setUp(self):
        pass


    def test_1(self):
        A = np.array([[1,0,1],[0,1,1]])
        c = np.array([300,100])
        f = np.array([500,550,600])
        d = np.array([200,300,100])
        
        lps = LPSolver(A,c,d,f,['p1','p2','p3'],['r1','r2'])
        val_glpk, sol_glpk = lps.solve_swiglpk('')
        val_rmlp, sol_rmlp = lps.solve_rmlp()
        self.assertTrue(abs(val_glpk - val_rmlp) <= EPS)


    def test_2(self):
        nrows = 3
        ncols = 5

        A = np.zeros((nrows,ncols))
        A[0,0] = 1
        A[0,2] = 1
        A[0,3] = 1
        A[0,4] = 1
        A[1,0] = 1
        A[1,1] = 1 
        A[1,4] = 1
        A[2,1] = 1
        A[2,2] = 1
        A[2,3] = 1

        c = np.array([84, 195, 178])
        d = np.array([469, 358, 79, 53, 423])
        f = np.array([799, 950, 870, 962, 244])

        lps = LPSolver(A,c,d,f,['']*ncols,['']*ncols)
        val_rmlp, sol_rmlp = lps.solve_rmlp()
        self.assertTrue(abs(val_rmlp - 209851.5) <= EPS)


    def test_rand_1(self):
        nruns = 1000
        nrows, ncols = 3, 5
        for nrun in range(nruns):
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
            val_glpk, sol_glpk = lps.solve_swiglpk('')
            val_rmlp, sol_rmlp = lps.solve_rmlp()
            if (abs(val_glpk - val_rmlp) > EPS):
                print "A = ", A
                print "c = ", c
                print "d = ", d
                print "f = ", f
                print "val_glpk, val_rmlp = ", val_glpk, val_rmlp
                print "sol_glpk, sol_rmlp = ", sol_glpk, sol_rmlp
            self.assertTrue(abs(val_glpk - val_rmlp) <= EPS)


    def test_rand_2(self):
        nruns = 100
        nrows, ncols = 20, 500
        for nrun in range(nruns):
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
            val_glpk, sol_glpk = lps.solve_swiglpk('')
            val_rmlp, sol_rmlp = lps.solve_rmlp()
            if (abs(val_glpk - val_rmlp) > EPS):
                print "A = ", A
                print "c = ", c
                print "d = ", d
                print "f = ", f
                print "val_glpk, val_rmlp = ", val_glpk, val_rmlp
                print "sol_glpk, sol_rmlp = ", sol_glpk, sol_rmlp
            self.assertTrue(abs(val_glpk - val_rmlp) <= EPS)


if __name__ == "__main__":
    unittest.main()


