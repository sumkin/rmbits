import numpy as np
from datetime import datetime
from gurobipy import *
from scipy.sparse import coo_matrix

from lpreaderfdc import *
from lpmodelloader import LPModelLoader

class GLPSolver:

    def __init__(self, A,
                 c, d, f, b, y,
                 prdt_names,
                 rsrc_names,
                 eqs=[],
                 semiconts=[],
                 semicont_lbs=[],
                 semiints=[],
                 semiint_lbs=[]):
        assert len(semiconts) == len(semicont_lbs), "len(semiconts) = {}, len(semicont_lbs) = {}".format(len(semiconts), len(semicont_lbs))
        assert len(semiints) == len(semiint_lbs), "len(semiints) = {}, len(semiint_lbs) = {}".format(len(semiints), len(semiint_lbs))

        self.m = A
        self.c = c
        self.d = d
        self.f = f
        self.b = b
        self.y = y
        self.prdt_names = prdt_names
        self.rsrc_names = rsrc_names
        self.eqs = eqs
        self.semiconts = semiconts
        self.semicont_lbs = semicont_lbs
        self.semiints = semiints 
        self.semiint_lbs = semiint_lbs

    def solve(self, lpname, silent = False):
        self.nrows = len(self.c)
        self.ncols = len(self.d)

        env = Env(empty = True)
        env.setParam('OutputFlag', 0)
        env.start()
        
        # Create a new model.
        self.model = Model("lp", env = env)

        # Create varialbes.
        self.x = []
        for i in range(self.ncols):
            if i in self.eqs:
                self.x.append(self.model.addVar(self.d[i], self.d[i], self.f[i], vtype = GRB.CONTINUOUS, name = "x" + str(i + 1)))
            else:
                if i in self.semiconts:
                    idx = self.semiconts.index(i)
                    self.x.append(self.model.addVar(self.semicont_lbs[idx], self.d[i], self.f[i], vtype = GRB.SEMICONT, name = "x" + str(i + 1)))
                elif i in self.semiints:
                    idx = self.semiints.index(i)
                    self.x.append(self.model.addVar(self.semiint_lbs[idx], self.d[i], self.f[i], vtype = GRB.SEMIINT, name = "x" + str(i + 1)))
                else:
                    self.x.append(self.model.addVar(0.0, np.inf, self.f[i], vtype = GRB.CONTINUOUS, name = "x" + str(i + 1)))

        # Set objective.
        self.obj = LinExpr()
        for i in range(self.ncols):
            self.obj += self.f[i] * self.x[i]
        self.model.setObjective(self.obj, GRB.MAXIMIZE)

        # Add row constraints.
        for i in range(self.nrows):
            nonzeros = list(self.m.getrow(i).nonzero()[1])
            if len(nonzeros) > 0:
                self.constr = self.x[nonzeros[0]]
                for j in nonzeros[1:]:  
                    self.constr += self.x[j]
                if self.c[i] == 0.0:
                    self.model.addConstr(self.constr == self.c[i], "c" + str(i + 1))
                else:
                    self.model.addConstr(self.constr <= self.c[i], "c" + str(i + 1))

        # Add variables upper constraints.
        for i in range(self.ncols):
            if i not in self.eqs:
                self.constr = self.x[i]
                self.model.addConstr(self.constr <= self.d[i], "d" + str(i + 1))

        self.model.Params.Presolve = 1
        self.model.Params.Method = 1
        self.model.optimize()

        self.val = self.model.objVal

        self.sol = []
        for i in range(self.ncols):
            varname = "x" + str(i + 1)
            varval = self.model.getVarByName(varname).X
            self.sol.append(varval)

        return self.val, self.sol 

    def get_rom_actual(self):
        self.ncols = len(self.d)

        bkgsum, bkgrevsum = 0, 0
        self.ff, self.ffbkg, self.ffrev = [], [], []
        assert self.ncols == len(self.prdt_names)
        prev_prdt_name = None
        prev_geo_od,prev_pos,prev_ff,prev_tp,prev_bc = None,None,None,None,None
        for i in range(self.ncols):
            prdt_name = self.prdt_names[i]
            bkg = self.b[i]
            bkgrev = self.b[i] * self.y[i]

            try:
                if prev_prdt_name is not None:
                    prev_geo_od,prev_pos,prev_ff,prev_tp,prev_bc = prev_prdt_name.split('-')
                geo_od,pos,ff,tp,bc = prdt_name.split('-')
            except Exception as e:
                raise e

            if prev_geo_od != geo_od or\
               prev_pos != pos or\
               prev_ff != ff or ff == '':
                # New fare family.
                if prev_ff == '':
                    prev_ff = prev_bc

                if prev_geo_od is not None:
                    self.ff.append([prev_geo_od,prev_pos,prev_ff])
                    self.ffbkg.append(bkgsum)
                    self.ffrev.append(bkgrevsum)

                bkgsum = bkg
                bkgrevsum = bkgrev
            else:
                # Fare family continues.
                bkgsum += bkg
                bkgrevsum += bkgrev

            prev_prdt_name = prdt_name

        return self.ff, self.ffbkg, self.ffrev

    def solve_rom_load(self):
        self.nrows = len(self.c)
        self.ncols = len(self.d)

        # Create model.
        self.model = Model("rom_load")

        # Get objective coefficients.
        ones = np.ones(self.nrows)
        objcoeffs = np.dot(ones, self.m.toarray())
  
        # Create variables.
        self.x = []
        for i in range(self.ncols):
            self.x.append(self.model.addVar(0.0,
                                            self.d[i],
                                            objcoeffs[i],
                                            vtype=GRB.CONTINUOUS,
                                            name="x" + str(i + 1)))

        # Set objective.
        self.obj = LinExpr()
        for i in range(self.ncols):
            self.obj += objcoeffs[i] * self.x[i]
        self.model.setObjective(self.obj, GRB.MAXIMIZE) 

        # Add row constraints.
        for i in range(self.nrows):
            nonzeros = list(self.m.getrow(i).nonzero()[1])
            if len(nonzeros) == 0:
                continue
            if len(nonzeros) > 0:
                self.constr = self.x[nonzeros[0]]
            for j in nonzeros[1:]:
                try:
                    self.constr += self.x[j]
                except:
                    self.constr = self.x[j]
            if self.c[i] == 0.0:
                self.model.addConstr(self.constr == self.c[i], "c" + str(i + 1))
            else:
                self.model.addConstr(self.constr <= self.c[i], "c" + str(i + 1))

        self.model.Params.Presolve = 1
        self.model.Params.Method = 1
        self.model.optimize()

        self.val = self.model.objVal

        varvalsum = 0
        dsum = 0
        self.sol = []
        self.ff, self.bcs, self.ffsol, self.ffd = [], [], [], []
        assert self.ncols == len(self.prdt_names)
        prev_prdt_name = None
        prev_geo_od,prev_pos,prev_ff,prev_tp,prev_bc = None,None,None,None,None
        for i in range(self.ncols):
            varname = "x" + str(i + 1)
            varval = self.model.getVarByName(varname).X
            prdt_name = self.prdt_names[i]
            self.sol.append(varval)

            try:
                if prev_prdt_name is not None:
                    prev_geo_od,prev_pos,prev_ff,prev_tp,prev_bc = prev_prdt_name.split('-')
                geo_od,pos,ff,tp,bc = prdt_name.split('-')
            except Exception as e:
                raise e

            if prev_geo_od != geo_od or\
               prev_pos != pos or\
               prev_ff != ff or ff == '' or\
               prev_tp != tp:
                # New fare family.
                if prev_ff == '':
                    assert len(self.bcs) == 1
                    prev_ff = prev_bc
                if varvalsum > 0.0:
                    self.ff.append([prev_geo_od,prev_pos,prev_ff,prev_tp])
                    self.bcs.append(prev_bc)
                    self.ffsol.append(varvalsum)
                    self.ffd.append(dsum)
                self.bcs = [bc]
                varvalsum = varval
                dsum = self.d[i]
            else:
                # Fare family continues.
                self.bcs.append(bc)  
                varvalsum += varval
                dsum += self.d[i]

            prev_prdt_name = prdt_name

        load_val = self.val

        return load_val, self.ff, self.ffd, self.ffsol

    def solve_rom_max(self, max_load):
        self.nrows = len(self.c)
        self.ncols = len(self.d)

        # Create model.
        self.model = Model("rom_max")

        # Create variables.
        self.x = []
        for i in range(self.ncols):
            self.x.append(self.model.addVar(0.0,
                                            self.d[i],
                                            self.f[i],
                                            vtype=GRB.CONTINUOUS,
                                            name="x" + str(i + 1)))

        # Set objective.
        self.obj = LinExpr()
        for i in range(self.ncols):
            self.obj += self.f[i] * self.x[i]
        self.model.setObjective(self.obj, GRB.MAXIMIZE)

        # Add row constraints.
        for i in range(self.nrows):
            nonzeros = list(self.m.getrow(i).nonzero()[1])
            if len(nonzeros) > 0:
                self.constr = self.x[nonzeros[0]]
                for j in nonzeros[1:]:
                    self.constr += self.x[j]
                if self.c[i] == 0.0:
                    self.model.addConstr(self.constr == self.c[i], "c" + str(i + 1))
                else:
                    self.model.addConstr(self.constr <= self.c[i], "c" + str(i + 1))

        # Add variables upper constraints.
        for i in range(self.ncols):
            self.constr = self.x[i]
            self.model.addConstr(self.constr <= self.d[i], "d" + str(i + 1))

        # Get maxload coefficients..
        ones = np.ones(self.nrows)
        maxloadcoeffs = np.dot(ones, self.m.toarray())
        maxloadcoeffs = maxloadcoeffs.astype(int)       
 
        # Add max load constraint.
        nonzeros = maxloadcoeffs.nonzero()[0]
        self.constr = self.x[nonzeros[0]]
        for i in nonzeros[1:]:
            self.constr += maxloadcoeffs[i] * self.x[i]
        self.model.addConstr(self.constr == int(max_load), "maxload")

        self.model.Params.Presolve = 1
        self.model.Params.Method = 1
        self.model.optimize()

        self.val = self.model.objVal

        dsum, varvalsum, varrevsum = 0, 0, 0
        self.sol = []
        self.ff, self.bcs, self.ffd, self.ffsol, self.ffrev = [], [], [], [], []
        assert self.ncols == len(self.prdt_names)
        prev_prdt_name = None
        prev_geo_od,prev_pos,prev_ff,prev_tp,prev_bc = None,None,None,None,None
        for i in range(self.ncols):
            varname = "x" + str(i + 1)
            varval = self.model.getVarByName(varname).X
            prdt_name = self.prdt_names[i]
            self.sol.append(varval)

            if prev_prdt_name is not None:
                prev_geo_od,prev_pos,prev_ff,prev_tp,prev_bc = prev_prdt_name.split('-')
            geo_od,pos,ff,tp,bc = prdt_name.split('-')

            if prev_geo_od != geo_od or\
               prev_pos != pos or\
               prev_ff != ff or ff == '' or\
               prev_tp != tp:
                # New fare family.
                if prev_ff == '':
                    assert len(self.bcs) == 1
                    prev_ff = prev_bc
                if varvalsum > 0.0:
                    self.ff.append([prev_geo_od,prev_pos,prev_ff,prev_tp])
                    self.bcs.append(prev_bc)
                    self.ffd.append(dsum)
                    self.ffsol.append(varvalsum)
                    self.ffrev.append(varrevsum)
                self.bcs = [bc]
                dsum = self.d[i]
                varvalsum = varval
                varrevsum = self.f[i] * varval
            else:
                # Fare family continues.
                self.bcs.append(bc)
                dsum += self.d[i]
                varvalsum += varval
                varrevsum += self.f[i] * varval

            prev_prdt_name = prdt_name

        return self.ff, self.ffd, self.ffsol, self.ffrev

    def solve_rom_min(self, max_load):
        self.nrows = len(self.c)
        self.ncols = len(self.d)

        # Create model.
        self.model = Model("rom_min")

        self.x = [] # x contains new variables (one per ff), p contains coefficients for objective
        self.objparams = []
        self.maxd = [] # variable demand upper constraints. 

        def process_ff(fs,ds,i):
            if len(fs) == 0:
                assert False
                return False
            elif sum(fs) <= 0.000001:
                assert len(fs) == len(ds)
                self.maxd.append(sum(ds))
                self.x.append(self.model.addVar(0.0,
                                                sum(ds),
                                                sum(fs),
                                                vtype=GRB.CONTINUOUS,
                                                name="x" + str(i + 1)))
                self.objparams.append([sum(fs)])
                return True
            else:
                assert len(fs) == len(ds)

                d,r = 0,0
                dsums,rsums = [0],[0] # demand and revenue sums
                for j in range(len(fs)):
                    d += ds[j]
                    r += fs[j] * ds[j]
                    if len(dsums) > 0:
                        if abs(dsums[len(dsums)-1] - d) <= 0.000001:
                            d += ds[j]   
                            continue
                    dsums.append(d)
                    rsums.append(r)
            
                if len(dsums) > 1: 
                    self.maxd.append(dsums[len(dsums)-1])
                    self.x.append(self.model.addVar(0, dsums[len(dsums)-1], name = "x" + str(i + 1)))
                    self.objparams.append([dsums,rsums]) 
                    return True
                else:
                    try:
                        self.maxd.append(dsums[1])
                        self.x.append(self.model.addVar(0, dsums[1], name = "x" + str(i + 1)))
                        self.objparams.append(self.fs[0])
                        return True
                    except:
                        return False

        # Create variables.
        mtilde_indices = []
        self.ff = []
        fs, ds, clss = [], [], []
        prev_geo_od_ts_key, prev_pos, prev_ff, prev_tp, prev_bc = None, None, None, None, None
        for i in range(self.ncols):
            prdt_name = self.prdt_names[i]
            geo_od_ts_key, pos, ff, tp, bc = prdt_name.split('-')

            if prev_geo_od_ts_key == geo_od_ts_key and\
               prev_pos == pos and\
               prev_ff == ff and\
               ff != '' and\
               prev_tp == tp:
                # Fare-family continues.
                fs.append(self.f[i])
                ds.append(self.d[i])   
                clss.append(bc) 
            else:

                if prev_geo_od_ts_key is not None:
                    # New fare-family.
                    if process_ff(fs,ds,i-1):
                        if prev_ff == '':
                            assert len(clss) == 1
                            prev_ff = clss[0]
                        self.ff.append([prev_geo_od_ts_key,prev_pos,prev_ff,prev_tp])
                        mtilde_indices.append(i-1)

                fs = [self.f[i]]
                ds = [self.d[i]]
                clss = [bc]
                        
            prev_geo_od_ts_key, prev_pos, prev_ff, prev_tp, prev_bc =\
                geo_od_ts_key, pos, ff, tp, bc

        if process_ff(fs,ds,i):
            if prev_ff == '':
                assert len(clss) == 1
                prev_ff = clss[0]
            self.ff.append([prev_geo_od_ts_key,prev_pos,prev_ff,prev_tp])
            mtilde_indices.append(i)

        mtilde = self.m.toarray()[:,mtilde_indices]

        # Add objective.
        for i in range(len(self.x)):
            if len(self.objparams[i]) == 1:
                if abs(self.maxd[i]) > 0.00001:
                    self.model.setPWLObj(self.x[i], [0,self.maxd[i]], [0,self.objparams[i][0] * self.maxd[i]])
        for i in range(len(self.x)):
            if len(self.objparams[i]) == 2:
                self.model.setPWLObj(self.x[i], self.objparams[i][0], self.objparams[i][1])

        # Get maxload coefficients.
        ones = np.ones(self.nrows)
        maxloadcoeffs = np.dot(ones, mtilde)

        # Add max load constraint.
        nonzeros = maxloadcoeffs.nonzero()[0]
        self.constr = self.x[nonzeros[0]]
        for i in nonzeros[1:]:
            self.constr += maxloadcoeffs[i] * self.x[i]
        self.model.addConstr(self.constr >= max(0, max_load - 1), "maxload")

        self.model.optimize()

        n = 0
        resnames, resds, ressols, resrevs = [], [], [], []
        for i in mtilde_indices:
            varname = "x" + str(i + 1)
            var = self.model.getVarByName(varname)
            varval = var.X
            pp = self.model.getPWLObj(var)
            if len(pp) != 0:
                resnames.append(self.ff[n])
                resds.append(self.maxd[n])
                ressols.append(varval)
                found = False
                for j in range(1,len(pp)):
                    if varval <= pp[j][0]:
                        found = True
                        v1, v2 = pp[j-1][0], pp[j][0]
                        r1, r2 = pp[j-1][1], pp[j][1]
                        r = r1 + ((r2 - r1) / (v2 - v1)) * (varval - v1)
                        resrevs.append(r)
                        break
                if not found:
                    assert varval <= pp[len(pp)-1][0] + 0.1
                    v1, v2 = pp[len(pp)-2][0], pp[len(pp)-1][0]
                    r1, r2 = pp[len(pp)-2][1], pp[len(pp)-1][1]
                    r = r1 + ((r2 - r1) / (v2 - v1)) * (varval - v1)
                    resrevs.append(r)
            n += 1

        return resnames, resds, ressols, resrevs

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

    def get_rsrc_sp(self):
        res = []
        for i in range(self.nrows):
            nonzeros = self.m.getrow(i).nonzero()[1]
            if len(nonzeros) > 0:
                cname = "c" + str(i + 1)
                res.append(self.model.getConstrByName(cname).Pi)
            else:
                res.append(np.nan)
        return res 

    def get_rsrc_sens_low(self):
        res = []
        for i in range(self.nrows):
            nonzeros = self.m.getrow(i).nonzero()[1]
            if len(nonzeros) > 0:
                cname = "c" + str(i + 1)
                res.append(self.model.getConstrByName(cname).SARHSLow)
            else:
                res.append(np.nan)
        return res

    def get_rsrc_sens_high(self):
        res = []
        for i in range(self.nrows):
            nonzeros = self.m.getrow(i).nonzero()[1]
            if len(nonzeros) > 0:
                cname = "c" + str(i + 1)
                res.append(self.model.getConstrByName(cname).SARHSUp)
            else:
                res.append(np.nan)
        return res

    def get_prdt_sp(self): 
        res = []
        for i in range(self.ncols):
            if i not in self.eqs:
                dname = "d" + str(i + 1)
                res.append(self.model.getConstrByName(dname).Pi)
            else:
                res.append(np.nan)
        return res

    def get_prdt_sens_low(self):
        res = []
        for i in range(self.ncols):
            if i not in self.eqs:
                dname = "d" + str(i + 1)
                res.append(self.model.getConstrByName(dname).SARHSLow)
            else:
                res.append(np.nan)
        return res

    def get_prdt_sens_high(self):
        res = []
        for i in range(self.ncols):
            if i not in self.eqs:
                dname = "d" + str(i + 1)
                res.append(self.model.getConstrByName(dname).SARHSUp)
            else:
                res.append(np.nan)
        return res

    def adjust_demand(self, idx, d):
        self.d[idx] = d 

    def get_col_val(self, i):
        return self.sol[i]

    def get_num_rows(self):
        return self.nrows

    def get_num_cols(self):
        return self.ncols

if __name__ == "__main__":
    fcst_date, dep_date = '20230814', '20230814'

    print('Reading data from s3...')
    loader = LPModelLoader(fcst_date, dep_date)
    model = loader.get()

    Ai, Aj, Adata = model['Ai'], model['Aj'], model['Adata']
    cap = model['cap']
    d = model['d']
    f = model['f']
    b = model['b']
    y = model['y']
    prdt_names = model['prdt_names']
    rsrc_names = model['rsrc_names']

    A = coo_matrix((Adata, (Ai, Aj)), shape=(len(cap), len(d)))
    lps = GLPSolver(A, cap, d, f, b, y, prdt_names, rsrc_names)
    lps.solve("")
    lps.model.write("/home/ay49514/rmbits/data/model.lp")
    prdt_dual = lps.get_prdt_sp()
    print("prdt_dual = {}".format(prdt_dual))
    print("prdt_dual(> 0) = {}".format([e for e in prdt_dual if e > 0]))

    """
    actual_names, actual_bkgs, actual_revs = lps.get_rom_actual()
    print("ROM actual")
    print("len(actual_names) = ", len(actual_names))
    print("len(actual_bkgs) = ", len(actual_bkgs))
    print("len(actual_revs) = ", len(actual_revs))
    print("act_npax = ", sum(actual_bkgs))
    print("act_rev = ", sum(actual_revs))

    load_val, load_names, load_ds, load_sols = lps.solve_rom_load()
    print("ROM load")
    print("load_val = ", load_val)
    print("len(load_names) = ", len(load_names))
    print("len(load_sols) = ", len(load_sols))
    print("load_npax = ", sum(load_sols))

    max_names, max_ds, max_sols, max_revs = lps.solve_rom_max(load_val)
    print("ROM max")
    print("len(max_names) = ", len(max_names))
    print("len(max_sols) = ", len(max_sols))
    print("max_npax = ", sum(max_sols))
    print("max_rev = ", sum(max_revs))

    min_names, min_ds, min_sols, min_revs = lps.solve_rom_min(load_val)
    print("ROM min")
    print("len(min_names) = ", len(min_names))
    print("len(min_sols) = ", len(min_sols))
    print("min_pax = ", sum(min_sols))
    print("min_rev = ", sum(min_revs))
    """




