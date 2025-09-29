from lpmodelloader import *
from glpsolver import *
from cls import *

class ConstrFrcst:

    def __init__(self, fcstdate, depdate):
        self.fcstdate = fcstdate
        self.depdate = depdate
        loader = LPModelLoader(self.fcstdate, self.depdate)
        self.model = loader.get(mode="remaining")
        Adata = self.model["Adata"]
        Ai = self.model["Ai"]
        Aj = self.model["Aj"]
        cap = self.model["cap"]
        d = self.model["d"]
        f = self.model["f"]
        A = coo_matrix((Adata, (Ai, Aj)), shape=(len(cap), len(d)))
        self.lps = GLPSolver(A, cap, d, f,
                             [0] * len(f),
                             [0] * len(f),
                             self.model["prdt_names"],
                             self.model["rsrc_names"])

    def solve_max(self):
        if len(self.model["d"]) == 0:
            return 0, []
        else:
            maxval, maxsol = self.lps.solve("maxrev")
            return maxval, maxsol

    def solve_min(self, npax):
        minval, minsol = self.lps.solve("minrev", npax)
        return minval, minsol

    def rows(self, maxsol, minsol):
        d = self.model["d"]
        mp = self.model["f"]

        for idx in range(len(maxsol)):
            if self.model["f"][idx] > 0.0:
                yield self.model["initrow"][idx].split(',') + [mp[idx], d[idx], maxsol[idx]]

    def slack_rows(self):
        c = self.model["fcap"]
        s = self.lps.get_rsrc_slack()
        rsrc_names = self.model["rsrc_names"]
        assert len(s) == len(rsrc_names)
        return rsrc_names, c, s 

    def sp_rsrc_rows(self):
        sp = self.lps.get_rsrc_sp()
        slow = self.lps.get_rsrc_sens_low()
        shigh = self.lps.get_rsrc_sens_high()
        rsrc_names = self.model["rsrc_names"]

        assert len(sp) == len(rsrc_names)
        assert len(slow) == len(rsrc_names)
        assert len(shigh) == len(rsrc_names)
        return rsrc_names, sp, slow, shigh        

    def sp_prdt_rows(self, maxsol):
        sp = self.lps.get_prdt_sp()
        slow = self.lps.get_prdt_sens_low()
        shigh = self.lps.get_prdt_sens_high()
        
        assert len(maxsol) == len(sp)
        assert len(maxsol) == len(slow)
        assert len(maxsol) == len(shigh)

        for idx in range(len(maxsol)):
            flow = self.model["initrow"][idx].split(",")
            cabin = get_cmpt(flow[len(flow) - 2])
            yield flow + [cabin] + [sp[idx], slow[idx], shigh[idx]]

if __name__ == "__main__":
    cf = ConstrFrcst("20240520", "20241028")
    maxval, maxsol = cf.solve_max()
    rows = cf.rows(maxsol, [0] * len(maxsol))
    slack_rows = cf.slack_rows()
    sp_rsrc_rows = cf.sp_rsrc_rows()
    sp_prdt_rows = cf.sp_prdt_rows(maxsol)



