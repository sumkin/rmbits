'''
GLPK sensitivity analysis report parser.
'''
import csv

from glpk_sar_parser import *


class SARParser:


    def __init__(self, fname):
        self.fname = fname


    def rows(self):
        vartype = '' # values are 'row' and 'column'
        with open(self.fname, 'r') as f:
            while True:
                line = f.readline()
                if not line:
                    break
                if line.strip() == '':
                    continue
                lines = line.strip().split()
                lines = [e for e in lines if e.strip() != '']
                try:
                    idx = int(lines[0])
                    if vartype == 'row':
                        # Read two lines.
                        res = lines
                        line1 = f.readline()
                        lines1 = line1.strip().split()
                        lines1 = [e for e in lines1 if e.strip() != '']
                        res += lines1

                        line2 = f.readline()
                        lines2 = line2.strip().split()
                        lines2 = [e for e in lines2 if e.strip() != '']
                        res += lines2

                        if len(res) == 15:
                            rownum   = res[0]
                            varname  = res[1]
                            status   = res[2]
                            activity = res[3]
                            slack    = res[4]
                            lowerbnd = res[5]
                            actrngl  = res[6]
                            objcfrl  = res[7]
                            objvall  = res[8]
                            limvall  = res[9]
                            marginal = res[10]
                            upperbnd = res[11]
                            actrngu  = res[12]
                            objcfru  = res[13]
                            objvalu  = res[14]
                            limvalu  = ''
                        elif len(res) == 16:
                            rownum   = res[0]
                            varname  = res[1]
                            status   = res[2]
                            activity = res[3]
                            slack    = res[4]
                            lowerbnd = res[5]
                            actrngl  = res[6]
                            objcfrl  = res[7]
                            objvall  = res[8]
                            limvall  = res[9]
                            marginal = res[10]
                            upperbnd = res[11]
                            actrngu  = res[12]
                            objcfru  = res[13]
                            objvalu  = res[14]
                            limvalu  = res[15]
                        elif len(res) == 14:
                            rownum   = res[0]
                            varname  = res[1]
                            status   = res[2]
                            activity = res[3]  
                            slack    = res[4]
                            lowerbnd = res[5]
                            actrngl  = res[6]
                            objcfrl  = res[7]
                            objvall  = res[8]
                            limvall  = ''
                            marginal = res[10]
                            upperbnd = res[11]
                            actrgnu  = res[12]
                            objcfru  = res[13]
                            objvalu  = res[14]
                            limvalu  = '' 
                        else:
                            assert False
                        yield vartype, rownum, varname, status, activity, slack,\
                              lowerbnd, actrngl, objcfrl, objvall, marginal,\
                              upperbnd, actrngu, objcfru, objvalu, limvall, limvalu
                    elif vartype == 'column':
                        # Read three lines.
                        res = lines
                        line1 = f.readline()
                        lines = line1.strip().split()
                        lines = [e for e in lines if e.strip() != '']
                        res += lines

                        line2 = f.readline()
                        lines = line2.strip().split()
                        lines = [e for e in lines if e.strip() != '']
                        res += lines

                        if len(res) == 16:
                            colnum   = res[0]
                            varname  = res[1]
                            status   = res[2]
                            activity = res[3]
                            objcoef  = res[4]
                            lowerbnd = res[5]
                            actrngl  = res[6]
                            objcfrl  = res[7]
                            objvall  = res[8]
                            limvall  = res[9]
                            marginal = res[10]
                            upperbnd = res[11]
                            actrngu  = res[12]
                            objcfru  = res[13]
                            objvalu  = res[14]
                            limvalu  = res[15]
                        else:
                            assert False
                        yield vartype, colnum, varname, status, activity, objcoef,\
                              lowerbnd, actrngl, objcfrl, objvall, marginal,\
                              upperbnd, actrngu, objcfru, objvalu, limvall, limvalu
                    else:
                        assert False
                except:
                    if lines[0] == 'GLPK':
                        # Ignore.
                        pass
                    elif lines[0] == 'Problem':
                        # Ignore.
                        pass
                    elif lines[0] == 'Objective:':
                        # Ignore.
                        pass
                    elif lines[0] == 'No.':
                        if lines[1] == 'Row':
                            vartype = 'row'
                        elif lines[1] == 'Column':
                            vartype = 'column'
                        else:
                            assert False


    def parse(self, rows_fname, cols_fname):
        with open(rows_fname, 'wb') as fr:
            with open(cols_fname, 'wb') as fc:
                cfr = csv.writer(fr)
                cfc = csv.writer(fc)
                cfr.writerow(['VARTYPE', 'ROWNUM', 'VARNAME', 'STATUS',\
                              'ACTIVITY', 'SLACK', 'LOWERBND', 'ACTRNGL',\
                              'OBJCFRL', 'OBJVALL', 'MARGINAL', 'UPPERBND',\
                              'ACTRNGU', 'OBJCFRU', 'OBJVALU', 'LIMVALL', 'LIMVALU'])
                cfc.writerow(['VARTYPE', 'COLNUM', 'VARNAME', 'STATUS',\
                              'ACTIVITY', 'OBJCOEF', 'LOWERBND', 'ACTRNGL',\
                              'OBJCFRL', 'OBJVALL', 'MARGINAL', 'UPPERBND',\
                              'ACTRNGU', 'OBJCFRU', 'OBJVALU', 'LIMVALL', 'LIMVALU'])
                for r in self.rows():
                    if r[0] == 'row':
                        cfr.writerow(r)
                    elif r[0] == 'column':
                        cfc.writerow(r)
                    else:
                        assert False


if __name__ == "__main__":
    sar = SARParser("/home/ay49514/tmp/br_cf_sar_orig_20190122_20190609.txt")
    for r in sar.rows():
        print(r)
    #sar.parse("r.csv", "c.csv")



