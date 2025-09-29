from gurobipy import *

model = read("../output/farm_optimized.lp")
model.setParam("MIPGap", 0.05)
model.setParam("Presolve", 2)
model.setParam("Heuristics", 0.95)
model.setParam("MIPFocus", 3)
model.optimize()
    
