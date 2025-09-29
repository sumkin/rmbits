import sys
import json
import pandas as pd
import csv
from cls import *
from datetime import datetime


if __name__ == "__main__":
    if len(sys.argv) == 3:
        fn = sys.argv[1]
        fnout = sys.argv[2]
        with open(fn, 'r') as f:
            with open(fnout, 'w') as fout:
                csvwriter = csv.writer(fout)
                csvwriter.writerow(['ORIG','DSTN','VIA','DPTDT','OD_DEPT_DATE','CC','POS','FLTNUM',\
                                    'LOCJ_WOSC','LOCY_WOSC','LOCJ_WOSC_IND','LOCY_WOSC_IND'])
                for line in f:
                    d = json.loads(line)
                    dptdt = datetime.strptime(d['OD_DEPT_DATE'],'%Y%m%d').strftime('%d.%m.%Y')
                    csvwriter.writerow([d['ORIG'],d['DSTN'],d['VIA'],dptdt,\
                                        d['OD_DEPT_DATE'],d['CC'],d['POS'],d['FLTNUM'],\
                                        d['LOCJ_WOSC'], d['LOCY_WOSC'],\
                                        get_cls_ind_j_wosc(d['LOCJ_WOSC']),\
                                        get_cls_ind_y_wosc(d['LOCY_WOSC'])])      



