import numpy as np
import gzip
import pickle
import time
import pandas as pd
import multiprocessing as mp 

from pyairport.airport import Airport
from lpmodelloader import LPModelLoader
from s3utils import *

EPS = 0.000001

def get_model(arg):
    fcstdate = arg[0]
    depdate = arg[1]
    lml = LPModelLoader(fcstdate, depdate)
    return lml.get()


class LPModelMultiLoader:

    
    def __init__(self, fcstdate, depdate):
        self.fcstdate = fcstdate
        self.depdates = depdate 


    def get(self, mode = "remaining"):
        # Read models.
        print("Reading models...")
        pool = mp.Pool(mp.cpu_count())
        models = pool.map(get_model, [(self.fcstdate, depdate) for depdate in self.depdates])

        # Combine models.
        print("Combining models...")
        res_nrows = 0
        res_ncols = 0

        res_Ai, res_Aj, res_Adata = [], [], []
        res_cap = []
        res_fcap = []
        res_d = []
        res_f = []
        res_b = []
        res_y = []
        res_prdt_names = []
        res_rsrc_names = []
        res_initrow = []
        res_v_flowsh2idx = {}
        res_v_idx2flowsh = []
        res_rownumd = {}

        num = 0
        for model in models:
            num += 1
            print("\tnum = {}".format(num))
            Ai, Aj, Adata = model["Ai"], model["Aj"], model["Adata"] # matrix of constraints
            cap = model["cap"]                                       # vector of capacities
            fcap = model["fcap"]                                     # vector of full capacities
            d = model["d"]                                           # vector of demand 
            f = model["f"]                                           # vector of fares 
            b = model["b"]                                           # vector of bookings 
            y = model["y"]                                           # vector of yields
            prdt_names = model["prdt_names"]                         # name of products 
            rsrc_names = model["rsrc_names"]                         # name of resources
            initrow = model["initrow"]                               # product used to write results to csv
            v_flowsh2idx = model["v_flowsh2idx"]                     # geo flow to index of variable
            v_idx2flowsh = model["v_idx2flowsh"]                     # index of variable to geo flow
            rownumd = model["rownumd"]                               # resource (flight) to row number 
            assert len(d) == len(f) == len(b) == len(y) == len(prdt_names) == len(initrow)
            assert len(cap) == len(fcap) == len(rsrc_names)

            # Ai is the list containing row indices of non-zero elements.
            # Aj is the list containing column indices of non-zero elements.
            # Adata is the list of non-zero elements.
            assert len(Ai) == len(Aj) == len(Adata)
            res_Ai += [e + res_nrows for e in Ai]
            res_Aj += [e + res_ncols for e in Aj]
            res_Adata += Adata 

            res_cap = np.concatenate((res_cap, cap))
            res_fcap = np.concatenate((res_fcap, fcap))
            res_d = np.concatenate((res_d, d))
            res_f = np.concatenate((res_f, f))
            res_b = np.concatenate((res_b, b))
            res_y = np.concatenate((res_y, y))
            res_prdt_names += prdt_names 
            res_rsrc_names += rsrc_names
            res_initrow += initrow 

            for k in v_flowsh2idx.keys():
                res_v_flowsh2idx[k] = v_flowsh2idx[k] + res_ncols

            res_v_idx2flowsh += v_idx2flowsh

            for k in rownumd.keys():
                res_rownumd[k] = rownumd[k] + res_nrows

            res_nrows = len(res_cap)
            res_ncols = len(res_d)

        res = {}
        res["Ai"] = res_Ai
        res["Aj"] = res_Aj
        res["Adata"] = res_Adata
        res["cap"] = res_cap
        res["fcap"] = res_fcap
        res["d"] = res_d 
        res["f"] = res_f 
        res["b"] = res_b
        res["y"] = res_y 
        res["prdt_names"] = res_prdt_names 
        res["rsrc_names"] = res_rsrc_names 
        res["initrow"] = res_initrow 
        res["fcap"] = res_fcap 
        res["v_flowsh2idx"] = res_v_flowsh2idx
        res["v_idx2flowsh"] = res_v_idx2flowsh
        res["rownumd"] = res_rownumd

        # Build A distance matrix.
        od_dist_cache = {}
        dist_df = pd.read_csv("s3://ay-rmp-home/fleet_assigner/input/od_distances.csv") # File should be specified in odfa.py
        dist_df["ap1"] = dist_df["ap1"].astype("category")
        dist_df["ap2"] = dist_df["ap2"].astype("category")
        assert len(res_Ai) == len(res_Aj) == len(res_Adata)

        res_Adistratio_data = []
        n = len(res_Ai)
        for k in range(n):
            i = res_Ai[k]
            j = res_Aj[k]
            resource = res_rsrc_names[i]
            product = res_prdt_names[j]
            leg_ap1 = resource[2:5]
            leg_ap2 = resource[5:8]
            od_ap1 = product[:3]
            if len(product) > 60: # FIXME: why not equal to some number?
                od_ap2 = product[31:34]
            else:
                od_ap2 = product[3:6]
            if (leg_ap1, leg_ap2) in od_dist_cache:
                leg_dist = od_dist_cache[(leg_ap1, leg_ap2)]
            else:
                try:
                    leg_dist = dist_df[(dist_df["ap1"] == leg_ap1) & (dist_df["ap2"] == leg_ap2)]["dist"].iloc[0]
                except:
                    try:
                        leg_dist = Airport(leg_ap1).distance(Airport(leg_ap2))
                    except:
                        print("leg_ap1, leg_ap2 = {}, {}".format(leg_ap1, leg_ap2))
                        assert False
                od_dist_cache[(leg_ap1, leg_ap2)] = leg_dist
            if (od_ap1, od_ap2) in od_dist_cache:
                od_dist = od_dist_cache[(od_ap1, od_ap2)]
            else:
                try:
                    od_dist = dist_df[(dist_df["ap1"] == od_ap1) & (dist_df["ap2"] == od_ap2)]["dist"].iloc[0]
                except:
                    try:
                        od_dist = Airport(od_ap1).distance(Airport(od_ap2))
                    except:
                        print("od_ap1, od_ap2 = {}, {}".format(od_ap1, od_ap2))
                        assert False
                od_dist_cache[(od_ap1, od_ap2)] = od_dist
            if od_dist < EPS:
                v = 0.0
            else:
                v = leg_dist / od_dist
            res_Adistratio_data.append(v)
        res["res_Adistratiodata"] = res_Adistratio_data
        return res


if __name__ == "__main__":
    depdates = ["20220606","20220607","20220608","20220609","20220610","20220611","20220612"]
    lmml = LPModelMultiLoader("20220506", depdates)
    model = lmml.get()
    print(model.keys())



