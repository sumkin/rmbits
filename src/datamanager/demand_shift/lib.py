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
sys.path.append(config.get('PATHS','datamanager'))
sys.path.append(config.get('PATHS','webgui'))

# Needed to access django models outside of application
os.environ['PYTHONPATH'] = config.get('PATHS','webgui')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from db_connector import dbConnector
from oandd import *
from cls import *
from airport import *
from demand_shift.models import ClassUsage

# DSM is Demand Shfit Matrix
def is_cls_missed_in_dsm(cls,demand_shift_matrix):
    res = True
    for cls2 in get_clss_():
        if float(demand_shift_matrix[cls][cls2]) != 0.0:
            res = False
            break
    return res

def cu_cmp(cls,cu1,cu2):
    res = 0
    if is_exact_match(cls,cu1,cu2):
       [cls1,dist1] = get_closest(cls,cu1.cls)
       [cls2,dist2] = get_closest(cls,cu2.cls)
       if dist1 < dist2:
           res = -1
       elif dist1 < dist2:
           res = 1
    else:
        # FIXME: function assumes that cu1 and cu2
        # matches (not in exact sense).
        if cu1.chng_cwf == True and cu2.chng_cwof == True:
            res = -1
        elif cu2.chng_cwf == True and cu1.chng_cwof == True:
            res = 1
        else:
            [cls1,dist1] = get_closest(cls,cu1.cls)
            [cls2,dist2] = get_closest(cls,cu2.cls)
            if dist1 < dist2:
                res = -1
            elif dist1 < dist2:
                res = 1
    return res
        
def is_tc_match(cu1,cu2):
    # compare traffic category
    if cu1.type_p2p == cu2.type_p2p == True or\
       cu1.type_lh == cu2.type_lh  == True or\
       cu1.type_ie == cu2.type_ie == True:
        return True
    return False

def is_ch_exact_match(cu1,cu2):
    # compare changes rules
    if (cu1.chng_cwof == cu2.chng_cwof == True or\
        cu1.chng_cwf == cu2.chng_cwf == True or\
        cu1.chng_nc == cu2.chng_nc == True):
        return True
    return False

def is_rf_exact_match(cu1,cu2):
    # compare refund rules
    if (cu1.refund_fr == cu2.refund_fr == True or\
        cu1.refund_pr == cu2.refund_pr == True or\
        cu1.refund_nr == cu2.refund_nr == True):
        return True
    return False

def is_cls_match(cls,cu1,cu2):
    # in rules should be classes
    # from the same cabin
    cls1 = cu1.cls
    cls2 = cu2.cls
    for c1 in cls1:
        for c2 in cls2:
            if get_cmpt(c1) == get_cmpt(c2) == get_cmpt(cls):
                return True
    return False

def is_ch_match(cu1,cu2):
    # compare changes rules
    if is_ch_exact_match(cu1,cu2):
        return True
    else:
        # consider partial match in changes
        if (cu1.chng_cwf == True and cu2.chng_cwof == True) or\
           (cu2.chng_cwf == True and cu1.chng_cwof == True):
            return True
    return False

def is_rf_match(cu1,cu2):
    # compare refund rules
    if is_rf_exact_match(cu1,cu2):
        return True
    else:
        # consider partial match in refund
        if (cu1.refund_pr == True and cu2.refund_fr == True) or\
           (cu1.refund_pr == True and cu2.refund_fr == True):
            return True
    return False

def is_exact_match(cls,cu1,cu2):
    # Function checks whether demand
    # could shift between cu1 and cu2.
    # It returns True if classes are similar
    # in some sense and False otherwise.
    #
    # FIXME: logic could be revised and eloborated.
    # That is just draft version...
    #print '\t',cu1.cls,cu2.cls
    #print '\tis_cls_match:',is_cls_match(cu1,cu2)
    #print '\tis_tc_match:',is_tc_match(cu1,cu2)
    #print '\tis_rf_match:',is_rf_match(cu1,cu2)
    #print '\tis_ch_exact_match:',is_ch_exact_match(cu1,cu2)
    return is_cls_match(cls,cu1,cu2) and is_tc_match(cu1,cu2) and\
           is_rf_exact_match(cu1,cu2) and is_ch_exact_match(cu1,cu2)

def is_match(cls,cu1,cu2):
    return is_cls_match(cls,cu1,cu2) and is_tc_match(cu1,cu2) and\
           is_rf_match(cu1,cu2) and is_ch_match(cu1,cu2)

def __old__find_old_rules_for_cls(cls,cu_olds):
    for cu_old in cu_olds:
        if cls in cu_old.cls:
            return cu_old
    return None

def find_old_rules_for_cls(cls,orgn,dstn):
    levels = ['airport','city','country','region','continent']
    orgn_ap = airport(orgn)
    dstn_ap = airport(dstn)
    for orgn_level in levels:
        for dstn_level in levels:
            
            if orgn_level == 'airport':
                orgn_code = orgn
            elif orgn_level == 'city':
                orgn_code = orgn_ap.get_city()
            elif orgn_level == 'country':
                orgn_code = orgn_ap.get_country()
            elif orgn_level == 'region':
                orgn_code = orgn_ap.get_region()
                if orgn_code == 'SEASI':
                    orgn_code = 'ASIA'
            elif orgn_level == 'continent':
                orgn_code = orgn_ap.get_continent()
            else:
                assert 0

            if dstn_level == 'airport':
                dstn_code = dstn
            elif dstn_level == 'city':
                dstn_code = dstn_ap.get_city()
            elif dstn_level == 'country':
                dstn_code = dstn_ap.get_country()
            elif dstn_level == 'region':
                dstn_code = dstn_ap.get_region()
                if dstn_code == 'SEASI':
                    dstn_code = 'ASIA'
            elif dstn_level == 'continent':
                dstn_code = dstn_ap.get_continent()
            else:
                assert 0

            class_usages_old = ClassUsage.objects.filter(fromm=orgn_code,to=dstn_code,old_new='OLD',cls__contains=cls)
            if len(class_usages_old) != 0:
               return class_usages_old[0]
    return None


def find_new_rules_for_cls(cls,cu_old,od):
    levels = ['airport','city','country','region','continent']
    orgn = od.get_orgn()
    dstn = od.get_dstn()
    orgn_ap = airport(orgn)
    dstn_ap = airport(dstn)
    res = []
    found = False
    class_usages_new = []
    for orgn_level in levels:
        for dstn_level in levels:
            
            if orgn_level == 'airport':
                orgn_code = orgn
            elif orgn_level == 'city':
                orgn_code = orgn_ap.get_city()
            elif orgn_level == 'country':
                orgn_code = orgn_ap.get_country()
            elif orgn_level == 'region':
                orgn_code = orgn_ap.get_region()
                if orgn_code == 'SEASI':
                    orgn_code = 'ASIA'
            elif orgn_level == 'continent':
                orgn_code = orgn_ap.get_continent()
            else:
                assert 0

            if dstn_level == 'airport':
                dstn_code = dstn
            elif dstn_level == 'city':
                dstn_code = dstn_ap.get_city()
            elif dstn_level == 'country':
                dstn_code = dstn_ap.get_country()
            elif dstn_level == 'region':
                dstn_code = dstn_ap.get_region()
                if dstn_code == 'SEASI':
                    dstn_code = 'ASIA'
            elif dstn_level == 'continent':
                dstn_code = dstn_ap.get_continent()
            else:
                assert 0

            # FIXME: what for we needed cls__contains???
            #class_usages_new = ClassUsage.objects.filter(fromm=orgn_code,to=dstn_code,old_new='NEW',cls__contains=cls)
            tmp = ClassUsage.objects.filter(fromm=orgn_code,to=dstn_code,old_new='NEW')
            if len(tmp) != 0:
                class_usages_new += tmp

    '''
    FI-SE_LVSNQ_NEW ['101', 0L, 365L, None, '110', '110']
    EUROP-EUROP_LV_NEW ['100', 1L, 365L, None, '110', '110']

    In the example above L class will be checked to times and
    re-write demand shift matrix.
    What we do to avoid is the following.
    Remove found classes 
    '''

    for cu_new in class_usages_new:
        if is_match(cls,cu_old,cu_new):
            if od.get_type()   == TC_P2P:
                if cu_new.type_p2p == False:
                    continue
            elif od.get_type() == TC_LH:
                if cu_new.type_lh == False:
                    continue
            elif od.get_type() == TC_IE:
                if cu_new.type_ie == False:
                    continue
            res.append(cu_new)
            
    res = sorted(res,cmp=lambda x1,x2: cu_cmp(cls,x1,x2))

    res_modif = []
    found_cls = []
    for cu in res:
        for cls in found_cls:
            cu.cls = cu.cls.replace(cls,'')
        for e in cu.cls:
            found_cls.append(e)
        if cu.cls is not None and cu.cls != '':
            res_modif.append(cu)       
    return res_modif

def get_new_rules(od,cls):
    levels = ['airport','city','country','region','continent']
    orgn = od.get_orgn()
    dstn = od.get_dstn()
    orgn_ap = airport(orgn)
    dstn_ap = airport(dstn)
    res = []
    found = False
    class_usages_new = []
    for orgn_level in levels:
        for dstn_level in levels:
            
            if orgn_level == 'airport':
                orgn_code = orgn
            elif orgn_level == 'city':
                orgn_code = orgn_ap.get_city()
            elif orgn_level == 'country':
                orgn_code = orgn_ap.get_country()
            elif orgn_level == 'region':
                orgn_code = orgn_ap.get_region()
                if orgn_code == 'SEASI':
                    orgn_code = 'ASIA'
            elif orgn_level == 'continent':
                orgn_code = orgn_ap.get_continent()
            else:
                assert 0

            if dstn_level == 'airport':
                dstn_code = dstn
            elif dstn_level == 'city':
                dstn_code = dstn_ap.get_city()
            elif dstn_level == 'country':
                dstn_code = dstn_ap.get_country()
            elif dstn_level == 'region':
                dstn_code = dstn_ap.get_region()
                if dstn_code == 'SEASI':
                    dstn_code = 'ASIA'
            elif dstn_level == 'continent':
                dstn_code = dstn_ap.get_continent()
            else:
                assert 0

            # FIXME: what for we needed cls__contains???
            #class_usages_new = ClassUsage.objects.filter(fromm=orgn_code,to=dstn_code,old_new='NEW',cls__contains=cls)
            tmp = ClassUsage.objects.filter(fromm=orgn_code,to=dstn_code,old_new='NEW')
            if len(tmp) != 0:
                class_usages_new += tmp
                
    for cu_new in class_usages_new:
        res.append(cu_new)
            
    res = sorted(res,cmp=lambda x1,x2: cu_cmp(cls,x1,x2))
    return res

def whether_match_for_smoothing(od,cls1,cls2):            
    cu_news1 = get_new_rules(od,cls1)
    cu_news2 = get_new_rules(od,cls2)

    # take first rules (they should be sorted correctly already)
    cu_new1 = cu_news1[0]
    cu_new2 = cu_news2[0]

    if cu_new1.min_stay is None:
        cu_new1.min_stay = 0
    if cu_new2.min_stay is None:
        cu_new2.min_stay = 0
    if cu_new1.max_stay is None:
        cu_new1.max_stay = 0
    if cu_new2.max_stay is None:
        cu_new2.max_stay = 0

    # Check minimum, maximum stay and ap
    if cu_new1.min_stay == cu_new2.min_stay and\
       cu_new1.min_stay == cu_new2.max_stay and\
       cu_new1.ap == cu_new2.ap:
        return True
    return False

    




    
