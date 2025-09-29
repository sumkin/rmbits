import os
import sys
import ConfigParser

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(__file__,'../../../rw.cfg')
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))
sys.path.append(config.get('PATHS','analyzer'))

from datetime import date, datetime
from pylab import *
from numpy import mean
from math import ceil,floor
import csv

from analyzer_if import get_fcsterr_by_dptdt_dflc_lvl
from analyzer_if import get_booked_by_dptdt_dflc_lvl
from analyzer_if import get_all_orgn_dstn_fltnum
from analyzer_if import get_noshows_by_flc_lvl

from rpy2 import robjects
from pylab import *

r = robjects.r
r.source('outl_det.R')

clss = ['C','D','F','I','J',\
        'U','A','B','E','G',\
        'H','K','M','L','O',\
        'N','Q','P','S','R',\
        'T','W','V','Y','X','Z']

dayspriors = [320,286,252,213,196,\
              180,154,120,95,76,60,\
              47,42,37,29,26,23,21,\
              18,16,14,13,12,11,10,\
              9,8,7,6,5,4,3,2,1,0]

def get_sd_ratios(what,orgn,dstn,fltnum,dfrom,dto,daysprior,cls):

    curr_dt = datetime.now()
    curr_date = date(curr_dt.year, curr_dt.month, curr_dt.day)

    if what == 'pb':
        [vals,obs,diff,dptdts] = \
          get_fcsterr_by_dptdt_dflc_lvl('uncons',orgn,dstn,\
                                        fltnum,dfrom,curr_date,\
                                        daysprior,cls)
    elif what == 'fb':
        print "fp parameter what isn't implemented"
        assert 0
    elif what == 'ns':
        vals = get_noshows_by_flc_lvl(orgn,dstn,fltnum,dfrom,dto,cls)
    else:
        print 'Unknown parameter what in get_sd_ratios'
        assert 0

    print vals

    try:

        vals_r = robjects.FloatVector(vals)
        res_r = r.find_var_prop(vals_r) 
        res = robjects.default_ri2py(res_r)   

    except:

        res = [0,0]

    return res

if __name__ == '__main__':

    if len(sys.argv) == 4:

        what = sys.argv[1]
        [dfrom_y,dfrom_m,dfrom_d] = sys.argv[2].split('-')
        [dto_y,dto_m,dto_d] = sys.argv[3].split('-')
        orgn_dstn_fltnums = get_all_orgn_dstn_fltnum()

    else:

        orgn = sys.argv[1]
        dstn = sys.argv[2]
        fltnum = sys.argv[3]
        what = sys.argv[4]
        [dfrom_y,dfrom_m,dfrom_d] = sys.argv[5].split('-')
        [dto_y,dto_m,dto_d] = sys.argv[6].split('-')
        orgn_dstn_fltnums = [[orgn,dstn,fltnum]]

    # what:
    #   'pb' - past bookings outliers
    #   'fb' - future bookings outliers
    #   'ns' - noshows outliers

    orgn_dstn_fltnums = get_all_orgn_dstn_fltnum()

    for orgn_dstn_fltnum in orgn_dstn_fltnums: 

        orgn = orgn_dstn_fltnum[0]
        dstn = orgn_dstn_fltnum[1]
        fltnum = orgn_dstn_fltnum[2]
        dfrom = date(int(dfrom_y),int(dfrom_m),int(dfrom_d))
        dto = date(int(dto_y),int(dto_m),int(dto_d))

        l_props = []
        u_props = []

        cls_coeffs = {}

        csv_file_name = './'+what+'_files_lv/' + orgn + '_' + dstn + '_' + fltnum + '.csv'
        if (os.path.exists(csv_file_name)):
            continue
        csv_writer = csv.writer(open(csv_file_name,'w'))

        for cls in clss:

            for daysprior in dayspriors:
   
                [l_prop,u_prop] = get_sd_ratios(what,orgn,dstn,fltnum,dfrom,dto,daysprior,cls)
                if l_prop != 0:
                    l_props.append(l_prop)
                if u_prop != 0:
                    u_props.append(u_prop)

            num_outl_rmv_l = int(ceil(len(l_props))*0.05)
            num_outl_rmv_u = int(ceil(len(u_props))*0.05)

            for i in range(0,num_outl_rmv_l):

                if i % 2 == 0:
                    l_props.pop(l_props.index(max(l_props)))
                    u_props.pop(u_props.index(max(u_props)))
                else:
                    l_props.pop(l_props.index(min(l_props)))
                    u_props.pop(u_props.index(min(u_props)))

            lower_coeff = mean(l_props)
            upper_coeff = mean(u_props)

            print 'Class ' + cls
            print [lower_coeff, upper_coeff]
            cls_coeffs[cls] = [lower_coeff,upper_coeff]

            csv_str = [cls,lower_coeff,upper_coeff]
            csv_writer.writerow(csv_str)

        print cls_coeffs




