import numpy as np
from gurobipy import *

model = Model("ex1")

nrows = 2
c = [200,500]

ncols = 3
f = [3,2,2]
d = [300,200,404]

m = np.array([[1,1,0],[1,0,1]])

x = []
for i in range(ncols):
    x.append(model.addVar(0.0, GRB.INFINITY, f[i], vtype = GRB.CONTINUOUS, name = "x" + str(i+1)))

obj = LinExpr()
for i in range(ncols):
    obj += f[i] * x[i]
model.setObjective(obj, GRB.MAXIMIZE)

# Row constraints.
for i in range(nrows):
    print 'i = ', i
    nonzeros = m[i].nonzero()[0]
    print 'nonzeros = ', nonzeros
    if len(nonzeros) > 0:
        constr = x[nonzeros[0]]
        for j in nonzeros[1:]:
            constr += x[j]
        model.addConstr(constr, GRB.LESS_EQUAL, c[i], "c" + str(i + 1))

# Demand constraints.
for i in range(ncols):
    constr = x[i]
    model.addConstr(constr, GRB.LESS_EQUAL, d[i], "d" + str(i + 1))

model.Params.Presolve = 0
model.Params.Method = 1

model.optimize()

sol = []
for i in range(ncols):
    varname = "x" + str(i + 1)
    varval = model.getVarByName(varname).X
    sol.append(varval)

print 'sol = ', sol

for i in range(nrows):
    cname = "c" + str(i + 1)
    c = model.getConstrByName(cname)
    print cname, c.Pi, c.SARHSLow, c.SARHSUp

for i in range(ncols):
    varname = "x" + str(i + 1)
    var = model.getVarByName(varname)
    dname = "d" + str(i + 1)
    dmd = model.getConstrByName(dname)
    print dname, var.X, dmd.Pi, dmd.SARHSLow, dmd.SARHSUp



   


