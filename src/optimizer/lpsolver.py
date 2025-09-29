import numpy as np
from swiglpk import *
from copy import deepcopy
from datetime import datetime
import time

from defs import *
from rmlpctps import *
from lpreaderfdc import *
from smplxsolver import *

try:
    libc = CDLL("librmlp.so")
except Exception as e:
    print e


class LPSolver:


    def __init__(self, m, c, d, f, prdt_names, rsrc_names, eqs = []):
        self.m = m
        self.c = c
        self.d = d
        self.f = f
        self.prdt_names = prdt_names
        self.rsrc_names = rsrc_names
        self.eqs = eqs


    def solve(self, lpname, method = 'simplex'):
        nrows = len(self.c)
        ncols = len(self.d)

        # Initialization.
        ia = intArray(nrows * ncols); ja = intArray(nrows * ncols)
        ar = doubleArray(nrows * ncols)
        self.lp = glp_create_prob();
        glp_set_prob_name(self.lp, lpname)
        glp_set_obj_dir(self.lp, GLP_MAX)

        # Add rows.
        glp_add_rows(self.lp, nrows)
        for i in range(nrows):
            rowname = self.rsrc_names[i]
            glp_set_row_name(self.lp, i + 1, rowname)
            assert self.c[i] < np.inf
            assert 0.0 <= self.c[i]
            if self.c[i] == 0.0:
                glp_set_row_bnds(self.lp, i + 1, GLP_FX, 0.0, 0.0)
            else: 
                glp_set_row_bnds(self.lp, i + 1, GLP_UP, 0.0, self.c[i]) 

        # Add columns.
        glp_add_cols(self.lp, ncols)
        for i in range(ncols):
            colname = self.prdt_names[i]
            glp_set_col_name(self.lp, i + 1, colname)
            if i in self.eqs:
                glp_set_col_bnds(self.lp, i + 1, GLP_FX, self.d[i], self.d[i])
            else:
                glp_set_col_bnds(self.lp, i + 1, GLP_DB, 0.0, self.d[i])
            assert self.f[i] >= -EPS
            glp_set_obj_coef(self.lp, i + 1, self.f[i])

        # Fill matrix.
        num = 0
        rownum = 1
        for rowIndex in range(nrows):
            for colIndex in self.m[rowIndex].nonzero()[0]:
                num += 1
                ia[num] = rownum
                ja[num] = colIndex + 1
                ar[num] = self.m[rowIndex,colIndex]
                if colIndex in self.eqs:
                    self.d[colIndex] = min(self.d[colIndex], self.c[rowIndex])
            rownum += 1

        glp_load_matrix(self.lp, num, ia, ja, ar)

        self.sol = []
        if method == 'simplex':
            parm = glp_smcp()
            glp_init_smcp(parm)
            parm.meth = GLP_PRIMAL
            parm.presolve = GLP_ON
            glp_adv_basis(self.lp, 0)
            glp_simplex(self.lp, parm)
            for i in range(ncols):
                s = glp_get_col_prim(self.lp, i + 1)
                self.sol.append(s)
            self.val = glp_get_obj_val(self.lp)
        else:
            glp_interior(self.lp, None)
            for i in range(ncols):
                s = glp_ipt_col_prim(self.lp, i + 1)
                self.sol.append(s)
            self.val = glp_ipt_obj_val(self.lp)
            
        return self.val, self.sol


    def free(self):
        glp_delete_prob(self.lp)


    def solve_rmlp(self):
        m,n = self.m.shape

        # Set simplex tableu.
        self.ss = SimplexSolver(m + n, m + 2 * n)
        for i in range(m):
            for j in self.m[i].nonzero()[0]:
                self.ss.set_m(i, j, self.m[i,j])
            self.ss.set_m(i, n + i, 1)
            self.ss.set_rhs(i, self.c[i]) 
        for i in range(n):
            self.ss.set_m(m + i, i, 1)
            self.ss.set_m(m + i, m + n + i, 1)
            self.ss.set_rhs(m + i, self.d[i])
        for i in range(n):
            self.ss.set_lr(i, self.f[i])

        # Initialize basis.
        self.ss.set_init_slack_basis()

        # Solve.
        self.ss.solve()

        self.sol = []
        for i in range(n):
            self.sol.append(self.get_col_val_rmlp(i))
        self.val = self.ss.get_value()

        return self.val, self.sol


    def adjust_demand(self, idx, d):
        self.d[idx] = d 


    def get_col_val_swiglpk(self, i):
        return glp_get_col_prim(self.lp, i + 1)


    def get_col_val_rmlp(self, i):
        return self.ss.get_sol(i)


    def get_num_rows(self):
        return glp_get_num_rows(self.lp)


    def get_num_cols(self):
        return glp_get_num_cols(self.lp)


    def get_value(self):
        return self.value


    def get_sol(self):
        return self.sol


    def get_rsrc_slack(self):
        m = self.m
        s = np.array(self.get_sol())
        b = m.dot(s)
        slack = self.c - b
        return slack


    def get_min_rsrc_slack(self, idx):
        slack = self.get_rsrc_slack()
        mval = np.inf
        for i in self.m[:,idx].nonzero()[0]:
            mval = min(mval, slack[i])
        return int(mval)


    def get_rsrc_slacks(self, idx):
        slack = self.get_rsrc_slack()
        ress = []
        for i in self.m[:,idx].nonzero()[0]:
            ress.append(str(int(slack[i])))
        return ', '.join(ress)


    def print_sens_analysis(self, fname):
        glp_factorize(self.lp)
        glp_print_ranges(self.lp, 0, None, 0, fname)


    def write_cplex_file(self, fname):
        nrows = len(self.c)
        ncols = len(self.d)
        with open(fname, 'w') as fout:
            fout.write('Maximize\n')
            fout.write(' objective: ')
            for i in range(nrows):
                sgn = ''
                if self.f[i] >= 0.0:
                    if i != 0:
                        sgn = ' + '     
                    else:
                        sgn = ' '
                else:
                    sgn = ' - '
                fout.write(sgn + str(abs(self.f[i])) + ' ' + 'x'+str(i+1))
            fout.write('\n')
            fout.write('\n')
              
            fout.write('Subject To\n')
            for i in range(nrows):
                variables = []
                for j in self.m[i].nonzero()[0]:
                    variables.append('x'+str(j+1))
                fout.write('Con'+str(i+1)+': ' + ' + '.join(variables) + ' <= ' + str(self.c[i]))
                fout.write('\n')
            fout.write('\n')

            fout.write('Bounds\n')
            for j in range(ncols):
                fout.write('0 <= x' + str(j+1) + ' <= ' + str(self.d[i]) + '\n')    
            fout.write('\n')
            fout.write('end')


    def write_free_mps(self, fname):
        glp_write_mps(self.lp, GLP_MPS_FILE, None, fname)


if __name__ == "__main__":
    m = np.zeros((2,2))

    m[0,0] = 1
    m[0,1] = 0
    m[1,0] = 1
    m[1,1] = 1
 
    c = np.array([200, 500])

    d = np.array([25,50])

    f = np.array([3,2])

    prdt_names = ['x1','x2']
    rsrc_names = ['s1','s2']       

    lps = LPSolver(m,c,d,f,prdt_names,rsrc_names)
    val,sol = lps.solve('')
    slack = lps.get_rsrc_slack()
    msplg1 = lps.get_min_rsrc_slack(0)
    msplg2 = lps.get_min_rsrc_slack(1)
    print 'val = ', val
    print 'sol = ', sol
    print 'slack = ', slack
    print 'msplg1 = ', msplg1
    print 'msplg2 = ', msplg2

'''
if __name__ == "__main__":
    fcst_date = '20181115'
    dep_date = '20190609'

    lpr = LPReaderFDC(fcst_date, dep_date)
    print 'Reading data from s3 and converting...'
    dt1 = datetime.now()
    lpr.read()
    dt2 = datetime.now()
    print 'Reading done in ', (dt2 - dt1).seconds, 'seconds'
    print 'Creating LPSolver...'

    A = lpr.get_A()
    cap = lpr.get_cap()
    d = lpr.get_d()
    f = lpr.get_f()
    prdt_names = lpr.get_prdt_names()
    rsrc_names = lpr.get_rsrc_names()
    print 'A.shape = ', A.shape
    print 'cap.shape = ', cap.shape
    print 'd.shape = ', d.shape
    print 'f.shape = ', f.shape

    print 'len(prdt_names) = ', len(prdt_names)
    print 'len(rsrc_names) = ', len(rsrc_names)
    lps = LPSolver(A, cap, d, f, prdt_names, rsrc_names)
    dt3 = datetime.now()
    val,sol = lps.solve_swiglpk(fcst_date+'-'+dep_date, method = 'interior')
    npax = sum(sol)
    print "val = ", val
    print "npax = ", sum(sol)
    dt4 = datetime.now()
'''



