import subprocess
import pickle
from lpmodelloader import *
from glpsolver import *
from s3utils import *


class ROMCalculator:


    def __init__(self, fcstdate, depdate):
        self.fcstdate = fcstdate
        self.depdate = depdate
        
        orig = "s3://ay-rmp-home/nrm/lprdrfdcpkl/{}/{}/{}/lprdrfdcpkl_{}_{}_final.pkl.gz".format(self.fcstdate[:4],
                                                                                                self.fcstdate[4:6],
                                                                                                self.fcstdate[6:8],
                                                                                                self.fcstdate,
                                                                                                self.depdate)
        dstn = "~/tmp/lprdrfdcpkl_{}_{}_final.pkl.gz".format(self.fcstdate, self.depdate)
        s3copy(orig, dstn)

        subprocess.check_output(["gunzip", dstn])
        pkl_fname = "~/tmp/lprdrfdcpkl_{}_{}_final.pkl".format(self.fcstdate, self.depdate)
        with open(pkl_fname, "rb") as f:
            self.model = pickle.load(f)

        subprocess.check_output(["rm", "-rf", pkl_fname]) 


        self.lps = GLPSolver(self.model['Ai'], self.model['Aj'], self.model['Adata'],\
                             self.model['cap'],\
                             self.model['d'],\
                             self.model['f'],\
                             self.model['b'],\
                             self.model['y'],\
                             self.model['prdt_names'],\
                             self.model['rsrc_names'])
        prdt_names = self.model['prdt_names']


    def get_actual(self):
        if len(self.model['d']) == 0:
            return 0,[]
        else:
            actual_names, actual_bkgs, actual_bkgrevs = self.lps.get_rom_actual()
            return actual_names, actual_bkgs, actual_bkgrevs


    def solve_load(self):
        if len(self.model['d']) == 0:
            return 0,[]
        else:
            load_val, load_names, load_ds, load_sols = self.lps.solve_rom_load()
            return load_val, load_names, load_ds, load_sols


    def solve_max(self, load_val):
        if len(self.model['d']) == 0:
            return 0,[]
        else:
            max_names, max_ds, max_sols, max_revs = self.lps.solve_rom_max(load_val)
            return max_names, max_ds, max_sols, max_revs


    def solve_min(self, load_val):
        if len(self.model['d']) == 0:
            return 0,[]
        else:
            min_names, min_ds, min_sols, min_revs = self.lps.solve_rom_min(load_val)    
            return min_names, min_ds, min_sols, min_revs


if __name__ == "__main__":
    romcalc = ROMCalculator('20191220','20191220')
    load_val, load_names, load_dmds, load_sols = romcalc.solve_load()
    #print("load_val = ", load_val)
    #print("len(load_names) = ", len(load_names))
    #print("len(load_sols) = ", len(load_sols))

    max_names, max_dmds, max_sols, max_revs = romcalc.solve_max(load_val)
    #print("len(max_names) = ", len(max_names))
    #print("len(max_sols) = ", len(max_sols))
    #print("len(max_revs) = ", len(max_revs))
    #print("max rev = ", sum(max_revs))

    min_names, min_dmds, min_sols, min_revs = romcalc.solve_min(load_val)
    #print("len(min_names) = ", len(min_names))
    #print("len(min_sols) = ", len(min_sols))
    #print("len(min_revs) = ", len(min_revs))
    #print("min rev = ", sum(min_revs))

    act_names, act_bkgs, act_bkgrevs = romcalc.get_actual()
    #print("len(act_names) = ", len(act_names))
    #print("len(act_bkgs) = ", len(act_bkgs))
    #print("len(act_bkgrevs) = ", len(act_bkgrevs))
    #print("act bkgs = ", sum(act_bkgs))
    #print("act rev = ", sum(act_bkgrevs))

    print("minrev = ", sum(min_revs))
    print("maxrev = ", sum(max_revs))
    print("actrev = ", sum(act_bkgrevs))


 
    







