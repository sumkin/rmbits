##########################################
#
# This is command line script to show
# histogram of stay lengths for OD.
# That is done for Fare Branding project.
#
# Fedor Nikitin 2012
#
###########################################

import sys
from od import *
import rpy2.robjects as robjects

r = robjects.r

if __name__ == '__main__':
    if len(sys.argv) == 4:
        hop1 = sys.argv[1]
        hop2 = sys.argv[2]
        cls = sys.argv[3]

        od = OD([hop1,hop2])
        res = od.get_ap_cls_stats(cls)
        res_r = robjects.IntVector(res)
        hist_title = hop1 + '-' + hop2 + ' ap class ' + cls
        r.hist(res_r,xlab='',ylab='',breaks=25,main=hist_title)
    elif len(sys.argv) == 5:
        hop1 = sys.argv[1]
        hop2 = sys.argv[2]
        hop3 = sys.argv[3]
        cls = sys.argv[4]

        od = OD([hop1,hop2,hop3])
        res = od.get_ap_cls_stats(cls)
        res_r = robjects.IntVector(res)
        hist_title = hop1 + '-' + hop2 + '-' + hop3 + ' ap class ' + cls
        r.hist(res_r,xlab='',ylab='',breaks=25,main=hist_title)
      
