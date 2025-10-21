import os
import dill
import numpy as np
from gurobipy import *

if __name__ == "__main__":
    fcstdate = "20251006"
    month = "february2026"
    dill_fwoc_fname = "../cache/fwoc_{}_{}.dill".format(month, fcstdate)
    mps_fname = "../cache/model_{}_{}.mps".format(month, fcstdate)
    assert os.path.exists(dill_fwoc_fname) and os.path.exists(mps_fname)

    with open(dill_fwoc_fname, "rb") as f:
        fwoc = dill.load(f)
    fwoc.model = read(mps_fname)
    vars = fwoc.model.getVars()

    y_vars = [var for var in vars if "y" in var.VarName]
    fwoc.y_vars = {}
    for y_var in y_vars:
        var_name = y_var.VarName
        d, k = var_name.split(",")
        d, k = int(d.lstrip("y[")), int(k.rstrip("]"))
        fwoc.y_vars[(d, k)] = y_var

    z_vars = [var for var in vars if "z" in var.VarName]
    fwoc.z_vars = {}
    for z_var in z_vars:
        var_name = z_var.VarName
        j = int(var_name.strip("z[").strip("]"))
        fwoc.z_vars[j] = z_var

    s_vars = [var for var in vars if "s" in var.VarName]
    fwoc.s_vars = {}
    for s_var in s_vars:
        var_name = s_var.VarName
        d, k = var_name.split(',')
        d, k = int(d.lstrip("s[")), int(k.rstrip("]"))
        fwoc.s_vars[(d, k)] = s_var
    fwoc.obj = fwoc.model.getObjective()

    print("num_duties = {}".format(len(fwoc.dr.duties)))
    for c in fwoc.model.getConstrs():
        if c.constrName == "max_num_changes":
            #for num_changes in range(len(fwoc.dr.duties), 0, -1):
            for num_changes in range(len(fwoc.dr.duties)):
                if num_changes % 100 != 0:
                    continue
                c.RHS = num_changes
                fwoc.model.setParam("OutputFlag", 0)
                fwoc.model.setParam("Presolve", 2)
                fwoc.model.setParam("MIPGap", 0.01)
                fwoc.model.setParam("MIPFocus", 2)
                fwoc.model.setParam("Heuristics", 0.95)
                fwoc.model.optimize()
                sol = fwoc.get_solution()
                rev, booked_rev, costs = sol["rev"], sol["booked_rev"], sol["costs"]
                profit = rev + booked_rev - costs
                print("num_changes, profit = {}, {}".format(num_changes, profit))


