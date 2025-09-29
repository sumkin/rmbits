import sys
sys.path.append('../datamanager')
sys.path.append('../analyzer')
from datetime import date
from numpy import mean
from math import sqrt,ceil
from rpy2 import robjects

from daysprior import *
from cls import *
from split_history import *
from fcst_data_reader import *

DEBUG = False

r = robjects.r

def get_sample_size(sample):

    #
    # Formula: 
    #
    # $n = \frac{4}{ (\sqrt(\theta_0) - \sqrt(\theta_1))^2 }$
    #   

    if len(sample) == 0:
        return

    sample = [max(e,0) for e in sample]

    mn0 = mean(sample)
    mn1 = mn0 + max(mn0*1.15,3)

    mn0_sqrt = sqrt(mn0)
    mn1_sqrt = sqrt(mn1)

    diff_sqrt = mn0_sqrt - mn1_sqrt

    return int(ceil(4/(diff_sqrt * diff_sqrt)))      

def get_esp_params(flights,dows,sh_id,pool_ids,clss):

    sizes = []
    alphas = []

    for flight in flights:

        #if DEBUG:
        print flight

        orgn = flight[0]
        dstn = flight[1]
        fltnum = flight[2]

        sh = splitHistory(sh_id)

        for dow in dows:

            #if DEBUG:
            #print 'DOW:',dow

            for pool_id in pool_ids:

                #if DEBUG:
                #print 'POOL_ID:',pool_id

                for cls in clss:

                    #if DEBUG:
                    #print 'CLS:',cls

                    for daysprior in get_dayspriors(): 

                        #print 'DAYSPRIOR:',daysprior

                        #print orgn,dstn,fltnum,cls,daysprior,dow,sh
                        fdr = fcstDataReader(orgn,dstn,fltnum,\
                                             cls,daysprior,dow,sh)
                        vals = fdr.get_fcst_minus_booked_vals('uncons',pool_id)
                        sample_size = get_sample_size(vals)
                        #print '\tsample_size:',sample_size
                        #print '\tlen(vals):',len(vals)

                        if sample_size is not None and len(vals) >= 5:

                            sizes.append(sample_size)
                            vals_r = robjects.FloatVector(vals)
                            vals_r_ts = r.ts(vals_r,frequency=len(vals))
                            try:
                                hw_res = r.HoltWinters(vals_r,beta=False,gamma=False)
                            except:
                                print 'flight: ' + str(flight)
                                print 'dow: ' + str(dow)
                                print 'pool_id: ' + str(pool_id)
                                print 'cls: ' + str(cls)
                                print 'daysprior: ' + str(daysprior)
                                print 'vals: ' + str(vals)
                                continue
                            alpha = robjects.default_ri2py(hw_res[2])
                            alphas.append(alpha)

    lag = int(ceil(mean(sizes)))
    alpha = float(mean(alphas))

    return [lag, alpha]

