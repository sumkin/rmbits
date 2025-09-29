import numpy as np
from swiglpk import *
from copy import deepcopy
from datetime import datetime
import time

from lpreaderfdc import *


class FMinLPSolver:
    

    def __init__(self, m, c, d, f, prdt_names, rsrc_names):
        '''
        m --- Product to resource matrix. 
              Each element is cumulative demand 
              from highest class.
        c --- Capacity vector.
        d --- Cumulative demand from highest class.
        f --- Cumulative revenue for each class.
        '''
        self.m = deepcopy(m)
        self.c = deepcopy(c)
        self.d = deepcopy(d)
        self.f = deepcopy(f)
        self.prdt_names = prdt_names
        self.rsrc_names = rsrc_names


    def solve_swiglpk(self, lpname, npax):
        n = len(self.d)
        m = len(self.c)

        nrows = m + n + 3
        ncols = 2 * n - 1

        print "nrows, ncols = ", nrows, ncols       

        nonzeronum = 8 * n 
        ia = intArray(nonzeronum); ja = intArray(nonzeronum)
        ar = doubleArray(nonzeronum)

        print "nonzeronum = ", nonzeronum
 
        self.lp = glp_create_prob()
        glp_set_obj_dir(self.lp, GLP_MIN)

        ####################################
        #
        #  Add rows.
        #
        ####################################
        glp_add_rows(self.lp, nrows)
        
        # First row is passengers constraint.
        glp_set_row_name(self.lp, 1, 'npax')
        glp_set_row_bnds(self.lp, 1, GLP_FX, npax, npax)

        # Next m rows are capacity constraints.
        for i in range(2, m + 2):
            assert self.c[i-2] > 0.0

            rowname = self.rsrc_names[i-2]
            glp_set_row_name(self.lp, i, rowname)
            glp_set_row_bnds(self.lp, i, GLP_UP, 0.0, self.c[i-2])

        # Next n rows are adjacency constraints.
        for i in range(m + 2, m + n + 1):
            rowname = 'adjcnstr' + str(i)
            glp_set_row_name(self.lp, i, rowname)
            glp_set_row_bnds(self.lp, i, GLP_UP, 0.0, 0.0)

        # Convexity constraints on lambda.
        glp_set_row_name(self.lp, m + n + 2, 'lmbdcnvx')
        glp_set_row_bnds(self.lp, m + n + 2, GLP_UP, 0.0, 1.0)

        # Exclusion constraints on z.
        glp_set_row_name(self.lp, m + n + 3, 'zexcl')
        glp_set_row_bnds(self.lp, m + n + 3, GLP_UP, 0.0, 1.0)

        ####################################
        #
        #  Add columns.
        #
        ####################################
        glp_add_cols(self.lp, ncols)

        # Lambda variables.
        for i in range(1, n + 1):
            colname = 'lambda' + str(i)
            glp_set_col_name(self.lp, i, colname)
            glp_set_col_bnds(self.lp, i, GLP_DB, 0.0, 1.0)
            glp_set_obj_coef(self.lp, i, self.f[i-1])

        # z variables.
        for i in range(1, n):
            colname = 'z' + str(i)
            glp_set_col_name(self.lp, n + i, colname)
            glp_set_col_kind(self.lp, n + i, GLP_BV)

        ####################################
        #
        #  Fill matrix.
        #
        ####################################

        # First row is pax constraints.
        num = 0
        for i in range(1, n + 1):
            num += 1
            ia[num] = 1
            ja[num] = i
            ar[num] = self.d[i - 1]

        # Next m rows are network matrix.
        for rowIndex in range(0, m):
            # First n columns is network matrix.
            for colIndex in self.m[rowIndex].nonzero()[0]:
                num += 1
                ia[num] = rowIndex + 2
                ja[num] = colIndex + 1
                ar[num] = self.m[rowIndex, colIndex]

        # Next n rows are adjacency constraints.
        for rowIndex in range(m + 2, m + n + 2):
            # First n columns is identity matrix.
            num += 1
            ia[num] = rowIndex
            ja[num] = rowIndex - m - 1
            ar[num] = 1
            # Second n - 1 columns is adjacency constraints.
            coln = rowIndex - m - 1 + n
            if coln <= 2 * n - 1:
                num += 1
                ia[num] = rowIndex
                ja[num] = coln
                ar[num] = -1

            coln = rowIndex - m - 1 + n - 1
            if coln >= n + 1:
                num += 1
                ia[num] = rowIndex
                ja[num] = coln
                ar[num] = -1

        # Lambda convexity constraints (m + n + 2)..
        # First n columns are ones. Rest is zero.
        for colIndex in range(1, n + 1):
            num += 1
            ia[num] = m + n + 2
            ja[num] = colIndex
            ar[num] = 1

        # z exclusion constraints.
        # First n columns are zeros.
        # Second n - 1 columns are ones.
        for colIndex in range(n + 1, 2 * n):
            num += 1
            ia[num] = m + n + 3
            ja[num] = colIndex
            ar[num] = 1

        print 'num = ', num
        glp_load_matrix(self.lp, num, ia, ja, ar)  
        print 'Matrix loaded.'

        parm = glp_iptcp()
        glp_init_iptcp(parm)
        glp_interior(self.lp, parm)

        parm = glp_iocp()
        glp_init_iocp(parm)
        #parm.presolve = GLP_ON
        glp_intopt(self.lp, parm)

        sol = []
        for i in range(ncols):
            sol.append(glp_mip_col_val(self.lp, i + 1))
        val = glp_mip_obj_val(self.lp)

        return val, sol


if __name__ == "__main__":
    fcst_date = '20180918'
    dep_date = '20181006'
    lpr = LPReaderFDC(fcst_date, dep_date)
    print 'Reading data from s3 and converting...'
    dt1 = datetime.now()
    lpr.read_min()
    dt2 = datetime.now()
    print 'Reading done in ', (dt2 - dt1).seconds, 'seconds'
    print 'Creating LPSolver...'

    A = lpr.get_A()            
    cap = lpr.get_cap()
    d = lpr.get_d()
    print 'sum(d) = ', sum(d)
    f = lpr.get_f()
    prdt_names = lpr.get_prdt_names()
    rsrc_names = lpr.get_rsrc_names()
    print 'A.shape = ', A.shape
    print 'cap.shape = ', cap.shape
    print 'f.shape = ', f.shape

    print 'len(prdt_names) = ', len(prdt_names)
    print 'len(rsrc_names) = ', len(rsrc_names)
    lps = FMinLPSolver(A, cap, d, f, prdt_names, rsrc_names) 
    dt3 = datetime.now()
    val,sol = lps.solve_swiglpk(fcst_date+'-'+dep_date, 10000)
    print "val (with npax) = ", val 


