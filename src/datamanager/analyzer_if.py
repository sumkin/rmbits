import sys
from datetime import date
from math import sqrt

from db_connector import dbConnector

#####################################################
#
#                 PUBLIC INTERFACE 
#
#####################################################

def get_avail_orgns(dfrom,dto,term=''):

    cursor = dbConnector.get_prosuser_curs()

    q = "SELECT DISTINCT orgn FROM active_legs"
    if term != '':
        q = q + " WHERE orgn LIKE '"+term+"%'"
    cursor.execute(q)
    row_l = cursor.fetchall()

    ret = [e[0].strip() for e in row_l]
    return ret

def get_all_orgn_dstn_fltnum():

    cursor = dbConnector.get_prosuser_curs()

    q = "SELECT DISTINCT orgn,dstn,fltnum FROM leg"
    cursor.execute(q)

    rows = cursor.fetchall()
    ret = []
    for row in rows:
        ret.append([row[0].strip(),row[1].strip(),row[2].strip()])
    return ret

def get_avail_dstns_for_orgn(dfrom,dto,orgn,term):

    cursor = dbConnector.get_prosuser_curs()

    q = "SELECT DISTINCT dstn FROM active_legs\
         WHERE orgn = '"+orgn+"'"
    if term != '':
        q = q + " AND dstn LIKE '"+term+"%'"
    cursor.execute(q)
    row_l = cursor.fetchall()
   
    ret = [e[0].strip() for e in row_l]
    return ret

def get_avail_dayspriors(dfrom,dto):

    cursor = dbConnector.get_prosuser_curs()

    q = "SELECT DISTINCT daysprior FROM hleg\
         WHERE dptdt >= DATE('"+dfrom.strftime('%Y-%m-%d')+"') AND\
               dptdt <= DATE('"+dto.strftime('%Y-%m-%d')+"')"
    cursor.execute(q)
    row_l = cursor.fetchall()

    ret = [e[0] for e in row_l]
    return ret

def get_avail_fltnum_for_leg(orgn,dstn,dfrom,dto):

    cursor = dbConnector.get_prosuser_curs()

    q = "SELECT DISTINCT fltnum FROM active_legs\
         WHERE orgn='"+orgn+"' AND dstn='"+dstn+"'"
    cursor.execute(q)
    row_l = cursor.fetchall()

    ret = [e[0] for e in row_l]
    return ret

def get_avail_cls_for_fltnum_leg(orgn,dstn,fltnum):

    cursor = dbConnector.get_prosuser_curs()

    q = "SELECT DISTINCT clssym FROM leg_class\
         WHERE orgn='"+orgn+"' AND dstn='"+dstn+"' AND fltnum='"+fltnum+"'"
    cursor.execute(q)
    row_l = cursor.fetchall()

    ret = [e[0].strip() for e in row_l]
    return ret

def get_avail_cmp_for_fltnum_leg(orgn,dstn,fltnum,dfrom,dto):

    cursor = dbConnector.get_prosuser_curs()

    q = "SELECT DISTINCT cmpsym FROM hleg_compartment\
         WHERE orgn='"+orgn+"' AND dstn='"+dstn+"' AND fltnum='"+fltnum+"' AND\
               dptdt >= DATE('"+dfrom.strftime('%Y-%m-%d')+"') AND\
               dptdt <= DATE('"+dto.strftime('%Y-%m-%d')+"')"
    cursor.execute(q)
    row_l = cursor.fetchall()

    ret = [e[0] for e in row_l]
    return ret

def get_avail_cmpt():

    cursor = dbConnector.get_prosuser_curs()

    q = "SELECT DISTINCT cmpsym FROM leg_compartment"
    cursor.execute(q)
    row_l = cursor.fetchall()

    ret = [e[0] for e in row_l]
    return ret

def get_avail_cls(cmpt):

    cursor = dbConnector.get_prosuser_curs()

    q = "SELECT DISTINCT clssym FROM leg_class\
         WHERE cmpsym = '" + cmpt + "'"
    cursor.execute(q)
    row_l = cursor.fetchall()

    ret = [e[0] for e in row_l]
    return ret 

def get_avail_daysprior_for_fltnum_leg(orgn,dstn,fltnum,dfrom,dto):

    cursor = dbConnector.get_prosuser_curs()

    q = "SELECT DISTINCT daysprior FROM hleg_compartment\
         WHERE orgn='"+orgn+"' AND dstn='"+dstn+"' AND fltnum='"+fltnum+"' AND\
               dptdt >= DATE('"+dfrom.strftime('%Y-%m-%d')+"') AND\
               dptdt <= DATE('"+dto.strftime('%Y-%m-%d')+"') AND daysprior != -1 ORDER BY daysprior DESC"
    cursor.execute(q)
    row_l = cursor.fetchall()

    ret = [e[0] for e in row_l]
    return ret

def get_avail_cls_for_fltnum_leg_cmp(orgn,dstn,fltnum,cmp):

    cursor = dbConnector.get_prosuser_curs()

    q = "SELECT DISTINCT clssym FROM hleg_class\
         WHERE orgn='"+orgn+"' AND dstn='"+dstn+"' AND fltnum='"+fltnum+"' AND cmpsym='"+cmp+"'"
    cursor.execute(q)
    row_l = cursor.fetchall()

    ret = [e[0].strip() for e in row_l]
    return ret
#
# FIXME: remove function below it is obsolete
#
def get_fcst_and_obs_for_daysprior_fltnum_leg_cls(orgn_in,dstn_in,fltnum_in,cls_in,daysprior_in,dfrom,dto):

    cursor = dbConnector.get_prosuser_curs()

    fcst = []
    obs = []
    diff = []

    q = "SELECT dptdt,daysprior,consfnldmd FROM hleg_class\
         WHERE crr='AY' AND fltnum='"+fltnum_in+"' AND orgn='"+orgn_in+"' AND\
               dstn='"+dstn_in+"' AND clssym='"+cls_in+"' AND\
               (daysprior='"+str(daysprior_in)+"' OR daysprior='-1') AND\
               dptdt >= DATE('"+dfrom.strftime('%Y-%m-%d')+"') AND\
               dptdt <= DATE('"+dto.strftime('%Y-%m-%d')+"')\
         ORDER BY dptdt,daysprior,consfnldmd"
    cursor.execute(q)

    prev_dptdt = prev_daysprior = prev_cnsfnldmd = None

    row = cursor.fetchone()
    while row is not None:

        dptdt = row[0]
        daysprior = row[1]
        consfnldmd = row[2]
       
        if dptdt == prev_dptdt:
            fcst.append(consfnldmd)
            obs.append(prev_consfnldmd)
            diff.append(consfnldmd - prev_consfnldmd)

        prev_dptdt = dptdt
        prev_daysprior = daysprior
        prev_consfnldmd = consfnldmd

        row = cursor.fetchone()

    return [fcst,obs,diff]

def get_fcst_rel_error_for_dayspriors_fltnum_leg_cls(orgn_in, dstn_in, fltnum_in,cls_in,daysprior_in,dfrom,dto):

    cursor = dbConnector.get_prosuser_curs()

    rel_err = []

    q = "SELECT dptdt,daysprior,consfnldmd FROM hleg_class\
         WHERE crr='AY' AND fltnum='"+fltnum_in+"' AND orgn='"+orgn_in+"' AND\
               dstn='"+dstn_in+"' AND clssym='"+cls_in+"' AND\
               (daysprior='"+str(daysprior_in)+"' OR daysprior='-1') AND\
               dptdt >= DATE('"+dfrom.strftime('%Y-%m-%d')+"')\
         ORDER BY dptdt,daysprior,consfnldmd"
    cursor.execute(q)

    prev_dptdt = prev_daysprior = prev_cnsfnldmd = None

    row = cursor.fetchone()
    while row is not None:
        
        dptdt = row[0]
        daysprior = row[1]
        consfnldmd = row[2]

        if dptdt == prev_dptdt:
            fcst = consfnldmd
            obs = prev_consfnldmd
            if obs != 0:
                rel_err.append(float(fcst-obs)/obs)
            elif fcst != 0:
                rel_err.append(float(fcst-obs)/fcst)
            else:
                rel_err.append(0)      

        prev_dptdt = dptdt
        prev_daysprior = daysprior
        prev_consfnldmd = consfnldmd

        row = cursor.fetchone()

    return rel_err

def get_fcsterr_by_dptdt_dflc_lvl(type,orgn_in,dstn_in,fltnum_in,dfrom,dto,daysprior_in,cls_in):

    cursor = dbConnector.get_prosuser_curs()

    fcst = []
    obs = []
    diff = []
    dptdt_l = []

    if type == 'cons':
        q = "SELECT dptdt,daysprior,consfnldmd FROM hleg_class\
             WHERE crr='AY' AND orgn='"+orgn_in+"' AND dstn='"+dstn_in+"' AND fltnum='"+fltnum_in+"' AND\
                   clssym='"+cls_in+"' AND (daysprior='"+str(daysprior_in)+"' OR daysprior='-1') AND\
                   dptdt >= TO_DATE('"+dfrom.strftime('%Y-%m-%d')+"','yyyy-mm-dd') AND\
                   dptdt <= TO_DATE('"+dto.strftime('%Y-%m-%d')+"','yyyy-mm-dd')\
             ORDER BY dptdt, daysprior"
    else:
        q = "SELECT dptdt,daysprior,uncdmd FROM hleg_class\
             WHERE crr='AY' AND orgn='"+orgn_in+"' AND dstn='"+dstn_in+"' AND fltnum='"+fltnum_in+"' AND\
                   clssym='"+cls_in+"' AND (daysprior='"+str(daysprior_in)+"' OR daysprior='-1') AND\
                   dptdt >= TO_DATE('"+dfrom.strftime('%Y-%m-%d')+"','yyyy-mm-dd') AND\
                   dptdt <= DATE('"+dto.strftime('%Y-%m-%d')+"','yyyy-mm-dd')\
             ORDER BY dptdt, daysprior"
    cursor.execute(q)

    prev_dptdt = prev_daysprior = prev_dmd = None

    row = cursor.fetchone()
    while row is not None:

        dptdt = row[0]
        daysprior = row[1]
        dmd = row[2]

        if dptdt == prev_dptdt:

            fcst.append(dmd)
            obs.append(prev_dmd)
            diff.append(dmd - prev_dmd)
            dptdt_l.append(dptdt) 

        prev_dptdt = dptdt
        prev_daysprior = daysprior
        prev_dmd = dmd

        row = cursor.fetchone()

    return [fcst,obs,diff,dptdt_l]

def get_booked_by_dptdt_dflc_lvl(typ,orgn,dstn,fltnum,dfrom,dto,daysprior,cls):

    cursor = dbConnector.get_prosuser_curs()

    dptdts = []
    bookeds = []
    #
    # NOTICE: some flights might be cancelled.
    # Those should be excluded from figures.
    # That's checked through DCP=-1 is presented in DB.
    #
    if typ == 'cons':
        q = "SELECT dptdt,daysprior,booked FROM hleg_class\
             WHERE crr='AY' AND orgn='"+orgn+"' AND dstn='"+dstn+"' AND fltnum='"+fltnum+"' AND\
                   clssym='"+cls+"' AND (daysprior='"+str(daysprior)+"' OR daysprior='-1') AND\
                   dptdt >= DATE('"+dfrom.strftime('%Y-%m-%d')+"') AND\
                   dptdt <= DATE('"+dto.strftime('%Y-%m-%d')+"')\
             ORDER BY dptdt, daysprior"
    else:
        q = "SELECT dptdt,daysprior,unctotbkd FROM hleg_class\
             WHERE crr='AY' AND orgn='"+orgn+"' AND dstn='"+dstn+"' AND fltnum='"+fltnum+"' AND\
                   clssym='"+cls+"' AND (daysprior='"+str(daysprior)+"' OR daysprior='-1') AND\
                   dptdt >= DATE('"+dfrom.strftime('%Y-%m-%d')+"') AND\
                   dptdt <= DATE('"+dto.strftime('%Y-%m-%d')+"')\
             ORDER BY dptdt, daysprior"    
    cursor.execute(q)

    prev_dptdt = prev_daysprior = prev_booked = None

    row = cursor.fetchone()
    while row is not None:

        dptdt = row[0]
        daysprior = row[1]
        booked = row[2]

        if dptdt == prev_dptdt:
            dptdts.append(dptdt)
            bookeds.append(booked)

        prev_dptdt = dptdt
        prev_daysprior = daysprior
        prev_booked = booked

        row = cursor.fetchone()

    return [bookeds,dptdts]

def get_bias_var_by_daysprior_flc_lvl(type,orgn,dstn,fltnum,dfrom,dto,cls):

    cursor = dbConnector.get_prosuser_curs()

    bias_l = []
    se_l = []
    daysprior_l = []

    daysprior_d = {}

    q = "SELECT dptdt,daysprior,consfnldmd FROM hleg_class\
         WHERE crr='AY' AND orgn='"+orgn+"' AND dstn='"+dstn+"' AND\
               fltnum='"+fltnum+"' AND clssym='"+cls+"' AND\
               dptdt >= DATE('"+dfrom.strftime('%Y-%m-%d')+"') AND\
               dptdt <= DATE('"+dto.strftime('%Y-%m-%d')+"')\
         ORDER BY dptdt, daysprior"
    cursor.execute(q)

    prev_dptdt = prev_daysprior = act_consfnldmd = None

    row = cursor.fetchone()

    while row is not None:

        dptdt = row[0]
        daysprior = row[1]
        consfnldmd = row[2]

        if dptdt != prev_dptdt:

            if daysprior != -1:

                # skip this date
                act_consfnldmd = None

            else:

                act_consfnldmd = consfnldmd

        else:

            if daysprior not in daysprior_d:

                daysprior_d[daysprior] = []

            else:

                if act_consfnldmd is not None:

                    daysprior_d[daysprior].append(consfnldmd - act_consfnldmd)    

        prev_dptdt = dptdt
        prev_daysprior = daysprior
        prev_consfnldmd = consfnldmd

        row = cursor.fetchone() 

    k_l = daysprior_d.keys()
    k_l = [int(e) for e in k_l]
    k_l.sort(reverse=True)

    for k in k_l:

        v = daysprior_d[k]
        if len(v) != 0:
            mn = float(sum(v))/len(v)
        else:
            mn = 0
        tmp = [e - mn for e in v]
        tmp = [e*e for e in tmp]
        if len(tmp) != 0:
            var = float(sum(tmp))/len(tmp) 
        else:
            var = 0

        bias_l.append(mn)
        se_l.append(sqrt(var))
     
    daysprior_l = daysprior_d.keys()

    return [bias_l,se_l,k_l]

def get_noshows_by_flc_lvl(orgn,dstn,fltnum,dfrom,dto,cls):

    cursor = dbConnector.get_prosuser_curs()

    q = "SELECT noshow,dptdt\
         FROM hleg_class\
         WHERE crr='AY' AND orgn='"+orgn+"' AND dstn='"+dstn+"' AND\
               fltnum='"+fltnum+"' AND clssym='"+cls+"' AND daysprior='-1' AND\
               dptdt >= DATE('"+dfrom.strftime('%Y-%m-%d')+"') AND\
               dptdt <= DATE('"+dto.strftime('%Y-%m-%d')+"')\
         ORDER BY dptdt"
    cursor.execute(q)

    noshows = []

    row = cursor.fetchone()

    while row is not None:

        noshow = row[0]
        dptdt = row[1]
       
        noshows.append(float(noshow))
        row = cursor.fetchone()

    return noshows 

def get_mse(type,orgn_in,dstn_in,fltnum_in,dfrom,dto,daysprior_in,cls_in):

    cursor = dbConnector.get_prosuser_curs()

    q = "SELECT dptdt,daysprior,consfnldmd FROM hleg_class\
         WHERE crr='AY' AND orgn='"+orgn_in+"' AND dstn='"+dstn_in+"' AND fltnum='"+fltnum_in+"' AND\
               clssym='"+cls_in+"' AND (daysprior='"+str(daysprior_in)+"' OR daysprior='-1') AND\
               dptdt >= DATE('"+dfrom.strftime('%Y-%m-%d')+"') AND\
               dptdt <= DATE('"+dto.strftime('%Y-%m-%d')+"')\
         ORDER BY dptdt, daysprior"
    cursor.execute(q)

    prev_dptdt = prev_daysprior = prev_consfnldmd = None

    num = 0
    sum_sq_err = 0
    row = cursor.fetchone()

    while row is not None:

        dptdt = row[0]
        daysprior = row[1]
        consfnldmd = row[2]

        if dptdt == prev_dptdt:

            num = num + 1
            fcst = consfnldmd
            obs = prev_consfnldmd

            if type == 'ae':

                err = float(fcst) - obs        

            elif type == 're':

                if fcst == 0 and obs == 0:

                    err = 0

                else:

                    err = (float(fcst) - obs ) / sqrt( (float(fcst*fcst) + obs*obs)/2)

            else:

                pass

            sum_sq_err = sum_sq_err + err
        
        prev_dptdt = dptdt    
        prev_daysprior = daysprior
        prev_consfnldmd = consfnldmd

        row = cursor.fetchone()

    return round(sum_sq_err/num,2)

################################################
#
#             KINDA UNIT TESTS
#
################################################
 
if __name__ == '__main__':

    dfrom = date(2010,1,1)
    dto = date(2011,1,1)
 
    '''
    print 'All available origins:'
    print get_avail_orgns(dfrom,dto)

    print 'All available destinations:'
    print get_avail_dstns(dfrom,dto)

    print 'All available legs:'
    print get_avail_legs(dfrom,dto)

    print 'All available flight numbers for HEL-BKK:'
    print get_avail_fltnum_for_leg('HEL','BKK',dfrom,dto)

    print 'All available departures for HEL-BKK 00095:'
    print get_avail_dptdt_for_fltnum_leg('HEL','BKK','00095',dfrom,dto)
    '''
    print 'Forecast and observations for HEL-BKK 00095 Y class 3 days prior:'
    [fcst,obs,diff] =  get_fcst_and_obs_for_daysprior_fltnum_leg_cls('HEL','BKK','00095','Y','3',dfrom,dto)
    print 'Forecast: ' + str(fcst)
    print 'Observations: ' + str(obs)
    print 'Difference: ' + str(diff)
    


