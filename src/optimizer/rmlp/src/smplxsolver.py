from ctypes import *
import sys
import random

from rmlpctps import *

try:
    libc = CDLL("librmlp.so")
except Exception as e:
    print e

_main_class_name = "SimplexSolver"


class SimplexSolver:


    def __init__(self, m, n):
        self.m = m
        self.n = n
        libc.smplxtbl_init.argtypes = [c_uint, c_uint]
        libc.smplxtbl_init.restype = POINTER(c_SmplxTbl)
        self.st = libc.smplxtbl_init(m, n)


    def set_rhs(self, i, v):
        libc.smplxtbl_set_rhs.argtypes = [POINTER(c_SmplxTbl), c_uint, c_double]
        libc.smplxtbl_set_rhs.restype = None
        libc.smplxtbl_set_rhs(self.st, i, c_double(v))


    def set_m(self, i, j, v):
        libc.smplxtbl_set_m.argtypes = [POINTER(c_SmplxTbl), c_uint, c_uint, c_double]
        libc.smplxtbl_set_m.restype = None
        libc.smplxtbl_set_m(self.st, i, j, c_double(v))


    def set_lr(self, i, v):
        libc.smplxtbl_set_lr.argtypes = [POINTER(c_SmplxTbl), c_uint, c_double]
        libc.smplxtbl_set_lr.restype = None
        libc.smplxtbl_set_lr(self.st, i, c_double(v))
 
    
    def set_init_slack_basis(self):
        libc.smplxtbl_init_slack_basis.argtypes = [POINTER(c_SmplxTbl)]
        libc.smplxtbl_init_slack_basis.restype = c_ushort
        libc.smplxtbl_init_slack_basis(self.st)


    def solve(self):
        libc.smplx_solve.argtypes = [POINTER(c_SmplxTbl)]
        libc.smplx_solve.restype = c_ushort
        libc.smplx_solve(self.st) 


    def get_value(self):
        libc.smplxtbl_get_value.argtypes = [POINTER(c_SmplxTbl)]
        libc.smplxtbl_get_value.restype = c_double
        return libc.smplxtbl_get_value(self.st)


    def get_sol(self, i):
        libc.smplxtbl_get_sol.argtypes = [POINTER(c_SmplxTbl), c_uint]
        libc.smplxtbl_get_sol.restype = c_double
        return libc.smplxtbl_get_sol(self.st, i)


    def printt(self):
        libc.smplxtbl_print.argtypes = [POINTER(c_SmplxTbl)]
        libc.smplxtbl_print.restype = None
        libc.smplxtbl_print(self.st)


if __name__ == "__main__":
    m = 3
    n = 5
    ss = SimplexSolver(m + n, m + 2 * n)

    print 'Setting simplex tableu...'
    # Set simplex tableu columns.
    '''
    for i in range(n):
        idx1 = random.randint(0,m)
        idx2 = random.randint(0,m)
        ss.set_m(idx1, i, 1)
        if idx2 != idx1:
            ss.set_m(idx2, i, 1)
        ss.set_m(i + m, i, 1)
        f = random.uniform(20, 1000)
        ss.set_lr(i, f)
    '''
    ss.set_m(0,0,1), ss.set_m(0,2,1), ss.set_m(0,3,1)
    ss.set_m(1,1,1), ss.set_m(1,3,1), ss.set_m(1,4,1)
    ss.set_m(2,0,1), ss.set_m(2,1,1), ss.set_m(2,2,1), ss.set_m(2,4,1)
    for i in range(n, n + m):
        ss.set_m(i - n, i, 1)
    for i in range(n + m, 2 * n + m):
        ss.set_m(i - n, i, 1)
    # Set right-hand side.
    ss.set_rhs(0, 231)
    ss.set_rhs(1, 177)
    ss.set_rhs(2, 142)
    ss.set_rhs(3, 12)
    ss.set_rhs(4, 156)
    ss.set_rhs(5, 104)
    ss.set_rhs(6, 311)
    ss.set_rhs(7, 369)

    ss.set_lr(0, 991)
    ss.set_lr(1, 259)
    ss.set_lr(2, 344)
    ss.set_lr(3, 648)
    ss.set_lr(4, 864)
    '''
    for i in range(m):
        c = random.randint(100, 300)
        ss.set_rhs(i, c)
    for i in range(m, n + m):
        mu = random.uniform(0.1, 20)
        ss.set_rhs(i, mu)
    ''' 

    print 'Initializing slack basis...'
    ss.set_init_slack_basis()

    print 'Solving...'
    ss.solve()

    print "val = ", ss.get_value()
    sol = []
    for i in range(n):
        sol.append(ss.get_sol(i))
    print "sol = ", sol

    '''
    ss = SimplexSolver(4, 6)
    ss.set_m(0,0,1), ss.set_m(0,1,1), ss.set_m(0,2,1), ss.set_rhs(0, 300)
    ss.set_m(1,1,1), ss.set_m(1,3,1), ss.set_rhs(1, 100)
    ss.set_m(2,0,1), ss.set_m(2,4,1), ss.set_rhs(2, 200)
    ss.set_m(3,1,1), ss.set_m(3,5,1), ss.set_rhs(3, 300)
    ss.set_lr(0, 500), ss.set_lr(1, 550)
    ss.set_init_slack_basis()
    ss.solve()
    '''
