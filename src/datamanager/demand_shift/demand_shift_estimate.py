import os
import sys
import csv
import ConfigParser
from datetime import date

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)
#print config.get('PATHS','datamanager')
sys.path.append(config.get('PATHS','datamanager'))
sys.path.append(config.get('PATHS','webgui'))

# Needed to access django models outside of application
os.environ['PYTHONPATH'] += config.get('PATHS','webgui') + ';'
os.environ['PYTHONPATH'] += config.get('PATHS','datamanager') + ';'
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from db_connector import dbConnector
from lib import *
from cls import *
from oandd import OandD
from airport import *
from demand_shift.models import ClassUsage


# dictionary containing coefficients
# how demand is going to be shifted
demand_shift_matrix = {}
def reset_dsm():
    for cls_up in get_clss_():
        demand_shift_matrix[cls_up] = {}
        for cls_bottom in get_clss_():
            demand_shift_matrix[cls_up][cls_bottom] = '0.00'

def print_demand_shift_matrix(demand_shift_matrix):
    # print first line
    print ' ',
    for cls in classes:
        print ' ',cls,'',
    print
    for cls_up in classes:
        print cls_up,
        for cls_bottom in classes:
            val = demand_shift_matrix[cls_up][cls_bottom]
            if float(val) == 0.0:
                print ' -- ',
            else:
                print ("%.2f" % float(demand_shift_matrix[cls_up][cls_bottom])),
        print
    
def class_usage_repr(cu):
    # x_1 --- type of traffic (000-111) p2p,lh,ie
    # x_2 --- min stay (e.g. 15)
    # x_3 --- max stay (e.g. 45)
    # x_4 --- ap (e.g. 20)
    # x_5 --- refund (000-111) nr,pr,fr
    # x_6 --- changes (000-111) nr,pr,fr
    x_1 = ''
    if cu.type_p2p:
        x_1 += '1'
    else:
        x_1 += '0'
    if cu.type_lh:
        x_1 += '1'
    else:
        x_1 += '0'
    if cu.type_ie:
        x_1 += '1'
    else:
        x_1 += '0'
        
    x_2 = cu.min_stay
    x_3 = cu.max_stay
    x_4 = cu.ap
    if x_4 == 0:
        x_4 = None

    x_5 = ''
    if cu.refund_nr:
        x_5 += '1'
    else:
        x_5 += '0'
    if cu.refund_pr:
        x_5 += '1'
    else:
        x_5 += '0'
    if cu.refund_fr:
        x_5 += '1'
    else:
        x_5 += '0'

    x_6 = ''
    if cu.chng_nc:
        x_6 += '1'
    else:
        x_6 += '0'
    if cu.chng_cwf:
        x_6 += '1'
    else:
        x_6 += '0'
    if cu.chng_cwof:
        x_6 += '1'
    else:
        x_6 += '0'

    return [x_1,x_2,x_3,x_4,x_5,x_6]

def get_coeff_stay_and_ap(od,cls,cu_old,cu_new):
    sl_and_ap = od.get_stay_length_and_ap_stats(cls)
    tot_num = len(sl_and_ap)
    
    new_min_stay = cu_new.min_stay
    new_max_stay = cu_new.max_stay
    new_ap = cu_new.ap

    # FIXME: None values should
    # be fixed in DB. 
    if new_min_stay is None:
        new_min_stay = 0
    if new_max_stay is None:
        new_max_stay = 365
    if new_ap is None:
        new_ap = 0     

    sl_and_ap_filtered = filter(lambda x: x[0] >= new_min_stay, sl_and_ap)
    sl_and_ap_filtered = filter(lambda x: x[0] <= new_max_stay, sl_and_ap_filtered)
    if new_ap is not None:
        sl_and_ap_filtered = filter(lambda x: x[1] >= new_ap, sl_and_ap_filtered)
    filtered_num = len(sl_and_ap_filtered)
    if tot_num == 0:
        return ' n '
    else:
        return str(round(float(filtered_num)/tot_num,2))

def filter_obs_cls1(obs,cls,cu):
    # filters out observations
    # which satisfies new rules
    new_min_stay = cu.min_stay
    new_max_stay = cu.max_stay
    new_ap = cu.ap
    if new_ap is None:
        new_ap = 0
    
    obs_filtered = filter(lambda x: x[0] < new_min_stay or\
                                    x[0] > new_max_stay or\
                                    x[1] < new_ap, obs)
    return obs_filtered

def filter_obs_cls2(obs,cls,cu):
    # filters out observations
    # which does not satisfied
    # with new rules
    new_min_stay = cu.min_stay
    new_max_stay = cu.max_stay
    new_ap = cu.ap
    if new_ap is None:
        new_ap = 0

    obs_filtered = filter(lambda x: x[0] >= new_min_stay and\
                                    x[0] <= new_max_stay and\
                                    x[1] >= new_ap, obs)
    return obs_filtered

def define_coeffs_cls(od,cls,cu_old,cu_news):
    # cu   --- old class from which demand
    #          is redistributed.
    # cu_l --- the list of classes to which
    #          demand will be redistributed.

    # Handle special classes here
    if is_special_cls(cls):
        demand_shift_matrix[cls][cls] = ' 1. '
        print '\t',cls,'->',cls,'1.00'
        return

    obs = od.get_stay_length_and_ap_stats(cls)
    # Filter observations based on old rules
    obs = filter_obs_cls2(obs,cls,cu_old)
    print '\tInit obs:',len(obs)
    tot_num = len(obs)
    print '\tTot num:',tot_num
    if tot_num == 0:
        demand_shift_matrix[cls][cls] = ' 1. '
        return

    num_filtered = 0
    for cu_new in cu_news:
        # Here filter all observations
        c,dist = get_closest(cls,cu_new.cls)
        len_before = len(obs)
        obs = filter_obs_cls1(obs,cls,cu_new)
        len_after = len(obs)
        num_filtered = len_before - len_after
        print '\tAfter fillter',c,':',len(obs)

        if tot_num != 0:
            demand_shift_matrix[cls][c] = str(round(float(num_filtered)/tot_num,2))
            print '\t[',cls,'],[',c,'] - ',demand_shift_matrix[cls][c]

def run(od):
    reset_dsm()
    if len(od.airports) == 2:
        orgn = od.airports[0]
        dstn = od.airports[1]
    else:
        orgn = od.airports[0]
        dstn = od.airports[2]

    or_curs = dbConnector.get_or_curs()
    ads_curs = dbConnector.get_ads_curs()

    #
    # First pass through demand shift matrix
    # to redistribute old demand through new classes.
    # 

    for cls in get_clss_():
        cu_old = find_old_rules_for_cls(cls,orgn,dstn)
        print '\n'
        print cls, ': ',
        if cu_old is not None:
            cu_new_match_l = find_new_rules_for_cls(cls,cu_old,od)
        else:
            if is_special_cls(cls):
                demand_shift_matrix[cls][cls] = ' 1. '
            print 'OLD RULES ARE NOT FOUND!'

        if cu_old:
            print cu_old,class_usage_repr(cu_old)
            if len(cu_new_match_l) != 0:
                for cu_new in cu_new_match_l:
                    print '\t', cu_new, class_usage_repr(cu_new)
                define_coeffs_cls(od,cls,cu_old,cu_new_match_l)
            else:
                print '\tNEW RULES ARE NOT FOUND'

    #
    # Re-distribute new demand among new classes.
    # Interpolation of demand for the clases which weren't used
    # before.
    #

    print_demand_shift_matrix(demand_shift_matrix)
    print 'Re-distribution of demand in new classes'

    for cls in get_clss_():
        if is_cls_missed_in_dsm(cls,demand_shift_matrix):
            continue

        if is_special_cls(cls):
            continue

        fares = {}
        fares[cls] = od.get_avg_tot_fare_cls_robust(cls)
        missed = []
        # Go left until not missed
        lower_cls = get_lower_cls(cls)
        while lower_cls is not None and is_cls_missed_in_dsm(lower_cls,demand_shift_matrix):
            if lower_cls != 'W':
                missed.append(lower_cls)
                fares[lower_cls] = od.get_avg_tot_fare_cls_robust(lower_cls)
            lower_cls = get_lower_cls(lower_cls)
        
        # Go right until not missed
        upper_cls = get_upper_cls(cls)
        while upper_cls is not None and is_cls_missed_in_dsm(upper_cls,demand_shift_matrix):
            if upper_cls != 'W':
                missed.append(upper_cls)
                fares[upper_cls] = od.get_avg_tot_fare_cls_robust(upper_cls)
            upper_cls = get_upper_cls(upper_cls)
            
        if None in fares.values():
            fares_sum = 0.0
        else:
            fares_sum = sum(fares.values())

        if fares_sum == 0.0:
            continue

        if len(missed) == 0:
            continue

        # Smooth
        for sub_cls in get_clss_():
            if is_special_cls(cls):
                continue
            dmd = float(demand_shift_matrix[sub_cls][cls])
            if float(dmd) == 0:
                # nothing to re-distribute
                continue
            #print 'Sub class:',sub_cls,', cls:',cls,', dmd:',str(dmd)
            rm_dmd = 0
            for sub_sub_cls in missed:
                # shift of demand from sub_cls to sub_sub_cls
                if whether_match_for_smoothing(od,sub_sub_cls,sub_cls):
                    val = float(demand_shift_matrix[sub_cls][sub_sub_cls])
                    val_to_add = float(fares[sub_sub_cls])/fares_sum * dmd
                    rm_dmd += val_to_add
                    val += round(val_to_add,2)
                    demand_shift_matrix[sub_cls][sub_sub_cls] = str(val)
                else:
                    # How many will be shifted from class
                    obs = od.get_stay_length_and_ap_stats(sub_cls)
                    val = float(demand_shift_matrix[sub_cls][sub_sub_cls])
                    cu_new = get_new_rules(od,sub_sub_cls)[0]
                    sh_obs = filter_obs_cls2(obs,sub_sub_cls,cu_new)
                    if len(obs) != 0:
                        val_to_add = float(len(sh_obs))/float(len(obs)) * dmd
                        val_to_add *= float(fares[sub_sub_cls])/fares_sum
                        rm_dmd += val_to_add
                    else:
                        val_to_add = 0
                        rm_dmd = 0
                    val += round(val_to_add,2)
                    demand_shift_matrix[sub_cls][sub_sub_cls] = str(val)
                
                    
            if len(missed) != 0:
                val = float(demand_shift_matrix[sub_cls][cls])
                demand_shift_matrix[sub_cls][cls] = str(val - rm_dmd)

    print_demand_shift_matrix(demand_shift_matrix)
    return demand_shift_matrix

if __name__ == '__main__':
    if len(sys.argv) == 4:
        od = OandD([sys.argv[1],sys.argv[2],sys.argv[3]])
        orgn = sys.argv[1]
        dstn = sys.argv[3]
    elif len(sys.argv) == 3:
        od = OandD([sys.argv[1],sys.argv[2]])
        orgn = sys.argv[1]
        dstn = sys.argv[2]
    else:
        print 'WRONG NUMBER OF ARGUMENTS...'
        exit
    run(od)
    


    
    

        




