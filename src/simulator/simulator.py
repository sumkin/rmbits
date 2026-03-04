import csv
from datetime import datetime
from joblib import Parallel, delayed
from scipy.sparse import coo_matrix

from lpreaderfdc import *
from constrfrcst import *
from s3utils import *
from demand_influences import *
from capacity_influences import *
from yield_influences import *

class Simulator:

    def __init__(self, fcstdate, prefix, mode, dmd_infl, cap_infl, yld_infl):
        # fcstdate - date when forecast was done.
        # prefix - prefix for file names.
        # mode - remaining or not.
        # dmd_infl - demand influence function.
        # cap_infl - capacity influence function.
        self.fcstdate = fcstdate
        self.prefix = prefix
        self.mode = mode
        self.dmd_infl = dmd_infl
        self.cap_infl = cap_infl
        self.yld_infl = yld_infl

    def process(self, fname, fcstdate):
        depdate = fname.split('/')[5].split('.')[0].split('_')[2]
        csv2check = 'ay-rmp-home/nrm/' + self.prefix + 'cf/' + fcstdate[:4] +\
                                                        '/' + fcstdate[4:6] +\
                                                        '/' + fcstdate[6:8] +\
                                                        '/' + self.prefix + 'cf_' + fcstdate + '_' + depdate + '.csv.gz'
        if s3fileexists(csv2check):
            print("{} exists.".format(csv2check))
            return 0

        self.lpr = LPReaderFDC(fcstdate, depdate, mode=self.mode)
        self.lpr.read(dmd_infl=self.dmd_infl, cap_infl=self.cap_infl, yld_infl=self.yld_infl)
        Ai, Aj, Adata = self.lpr.get_A()
        c = self.lpr.get_cap()
        d = self.lpr.get_d()
        f = self.lpr.get_f()
        b = [0] * len(d)
        y = [0] * len(f)
        prdt_names = self.lpr.get_prdt_names()
        rsrc_names = self.lpr.get_rsrc_names()
        A = coo_matrix((Adata, (Ai, Aj)), shape=(len(c), len(d)))
        self.lps = GLPSolver(A, c, d, f, b, y, prdt_names, rsrc_names)
        maxval, maxsol = self.lps.solve("")
        minval, minsol = 0, [0] * len(maxsol)
        assert len(f) == len(maxsol)

        fname_out = '/home/ay49514/tmp/' + self.prefix + 'cf_' + fcstdate + '_' + depdate + '.csv'
        with open(fname_out, 'w') as fout:
            csvwriter = csv.writer(fout)
            csvwriter.writerow(['GEO_OD_TS_KEY', 'BASE_OD_ORGN', 'BASE_OD_DSTN', 'BASE_OD_VIA',
                                'BASE_OD_ORGN_COUNTRY', 'BASE_OD_ORGN_REGION',
                                'BASE_OD_DSTN_COUNTRY', 'BASE_OD_DSTN_REGION',
                                'BASE_OPR_CC', 'BASE_OPR_FLTNUM',
                                'BASE_MKT_CC', 'BASE_MKT_FLTNUM',
                                'BASE_OD_DEPT_DATE', 'BASE_SEG_DEP_DATE', 'BASE_SEG_ARR_DATE',
                                'GEO_ORGN', 'GEO_DSTN',
                                'PREV_VIA', 'PREV_OPR_CC', 'PREV_OPR_FLTNUM', 'PREV_MKT_CC', 'PREV_MKT_FLTNUM', 'PREV_SEG_DEP_DATE', 'PREV_SEG_ARR_DATE',
                                'NEXT_VIA', 'NEXT_OPR_CC', 'NEXT_OPR_FLTNUM', 'NEXT_MKT_CC', 'NEXT_MKT_FLTNUM', 'NEXT_SEG_DEP_DATE', 'NEXT_SEG_ARR_DATE',
                                'POS', 'FF', 'BC', 'TP', 'MP', 'F',
                                'SRD','ARD', 'SFD', 'AFD',
                                'GCC_ARMD', 'GCC_SRMD', 'GCC_AFMD', 'GCC_SFMD', 'ADC', 'SDC', 'AMDC', 'SMDC', 'D',
                                'LPC_D', 'LPC_D_MIN', 'CREV', 'SRC_DATE'])
            srd = [0] * len(d) #self.lpr.get_srd()
            ard = [0] * len(d) #self.lpr.get_ard()
            sfd = [0] * len(d) #self.lpr.get_sfd()
            afd = [0] * len(d) #self.lpr.get_afd()
            gcc_armd = [0] * len(d) #self.lpr.get_gcc_armd()
            gcc_srmd = [0] * len(d) #self.lpr.get_gcc_srmd()
            gcc_afmd = [0] * len(d) #self.lpr.get_gcc_afmd()
            gcc_sfmd = [0] * len(d) #self.lpr.get_gcc_sfmd()
            adc = [0] * len(d) #self.lpr.get_adc()
            sdc = [0] * len(d) #self.lpr.get_sdc()
            amdc = [0] * len(d) #self.lpr.get_amdc()
            smdc = [0] * len(d) #self.lpr.get_smdc()

            mp = self.lpr.get_f()
            f = [0] * len(mp) #self.lpr.get_p()

            for idx in range(len(maxsol)):
                r = self.lpr.get_initrow(idx).split(',') + [mp[idx], f[idx],
                    srd[idx], ard[idx], sfd[idx], afd[idx],
                    gcc_armd[idx], gcc_srmd[idx], gcc_afmd[idx], gcc_sfmd[idx], adc[idx], sdc[idx], amdc[idx], smdc[idx], d[idx],
                    maxsol[idx], minsol[idx], float(mp[idx]) * float(maxsol[idx])]
                csvwriter.writerow(r + [fcstdate])
         
        print("Zipping file...")
        subprocess.check_output(['gzip', fname_out])

        print("Copying file to s3...")
        subprocess.check_output(['aws', 's3', 'cp', fname_out+'.gz', 's3://'+csv2check])

        print("Cleaning-up...")
        subprocess.check_output(['rm', fname_out + '.gz'])

        return 1  

    def process_parallel(self, fnames, fcstdate):
        num_cores = 8 # because of Gurobi.
        results = Parallel(n_jobs=num_cores)(delayed(self.process)(fname, fcstdate) for fname in fnames)
        return sum(results)

    def process_non_parallel(self, fnames, fcstdate):
        res = 0
        for fname in fnames:
            res += self.process(fname, fcstdate)
        return res    

    def simulate(self):
        fcsty = self.fcstdate[:4]
        fcstm = self.fcstdate[4:6]
        fcstd = self.fcstdate[6:8]

        fnames = gets3files('ay-rmp-home/nrm/fdc/'+fcsty+'/'+fcstm+'/'+fcstd)

        dt_s = datetime.now()
        num = 0
        if len(fnames) != 0:
            num = self.process_parallel(fnames, self.fcstdate)
        dt_e = datetime.now()

if __name__ == "__main__":
    sim = Simulator('20190519', 'XIA_CKG_C_', 'final', xiy_ckg_dmd, xiy_ckg_cap, xiy_ckg_yld)
    sim.simulate()


 

