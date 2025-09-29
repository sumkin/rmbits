import sys
import os
import ConfigParser

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))
sys.path.append(config.get('PATHS','analyzer'))

CURR_PATH = config.get('PATHS','analyzer')

from analyzer_if import get_fcsterr_by_dptdt_dflc_lvl

from datetime import date
from rpy2 import robjects
from rpy2.robjects import r


r_source_path = CURR_PATH + '/fcst_analyzer.R'
r_source_path = os.path.normpath(r_source_path)
r.source(r_source_path)

# Shapiro-Wilk test for normality
def shapiro_wilk_p_value(l):
   
    #l = list(Set(l)) 
    r_l = robjects.FloatVector(l)
    r_p_value = r.get_shapiro_wilk_p_value(r_l)
    p_value = robjects.default_ri2py(r_p_value)[0]

    return p_value

# Kolmogorov-Smirnov test
def ks_p_value(l):
    
    r_l = robjects.IntVector(l)
    r_p_value = r.get_ks_p_value(r_l)
    p_value = robjects.default_ri2py(r_p_value)[0]

    return p_value

def cramer_von_mises_p_value(l):
   
    r_l = robjects.IntVector(l)
    r_p_value = r.get_cr_von_mis_p_value(r_l)
    p_value = robjects.default_ri2py(r_p_value)[0]
 
    return p_value

# Ljung-Box test for independence 
def get_ljung_box_pval(type,orgn,dstn,fltnum,dfrom,dto,daysprior,cls):

    [fcst,obs,diff,dptdt_l] = get_fcsterr_by_dptdt_dflc_lvl(type,orgn,dstn,fltnum,dfrom,dto,daysprior,cls)
    if len(diff) != 0:
        r_diff = robjects.FloatVector(diff)
        r_pval = r.get_ljung_box_pval(r_diff)
        pval = robjects.default_ri2py(r_pval)[0]
    else:
        pval = 0
    return pval

def get_fcsterr_mse(type,orgn,dstn,fltnum,dfrom,dto,daysprior,cls):

    [fcst,obs,diff,dptdt_l] = get_fcsterr_by_dptdt_dflc_lvl(type,orgn,dstn,fltnum,dfrom,dto,daysprior,cls)
    r_diff = robjects.FloatVector(diff)
    r_mse = r.get_mse(r_diff)
    mse = robjects.default_ri2py(r_mse)[0]

    return mse 


def get_fcsterr_trend_pol2(type,orgn,dstn,fltnum,dfrom,dto,daysprior,cls):

    [fcst,obs,diff,dptdt_l] = get_fcsterr_by_dptdt_dflc_lvl(type,orgn,dstn,fltnum,dfrom,dto,daysprior,cls)
    r_diff = robjects.FloatVector(diff)
    res = r.get_trend_pol2(r_diff)
    return res

