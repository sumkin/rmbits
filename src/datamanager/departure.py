import sys
import os
import ConfigParser
from datetime import date,datetime,timedelta

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','forecaster'))
sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector
from aircraft import *
from cls import *
from crm_case import *

# FIXME: rename class name to satisfy PEP8

class Departure:
  def __init__(self,orgn,dstn,fltnum,dptdt):
    self.orgn = orgn
    self.dstn = dstn
    self.fltnum = fltnum
    self.dptdt = dptdt
    self.dmdtocome_cache = {}
    self.cls_fare_cache = {}
    self.now = datetime.now()  # that is needed to update caches if needed

  def is_departed(self):
    pros_curs = dbConnector.get_prosuser_curs()
    q = "SELECT * FROM hleg_compartment\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "' AND\
               daysprior = '-1' AND\
               dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd')"
    pros_curs.execute(q)
    row = pros_curs.fetchone()
    return (row is not None)    

  def get_aircraft(self):
    pros_curs = dbConnector.get_prosuser_curs()
    q = "SELECT fltaircrafttype AS code, fltaircraftcfgidcurrent AS cfg\
         FROM leg\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "' AND\
               dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd')"
    pros_curs.execute(q)
    row = pros_curs.fetchone()
    code = row[0]
    #or_curs = dbConnector.get_or_curs()
    #q = "SELECT cfg_code FROM aircraft_cfg WHERE cfg_key = '" + row[1] + "'"
    #or_curs.execute(q)
    #row2 = or_curs.fetchone()
    return Aircraft(row[0],row2[0])

  @property
  def aircraft_code(self):
    aircraft = self.get_aircraft()
    return aircraft.code

  @property
  def aircraft_cfg_code(self):
    aircraft = self.get_aircraft()
    return aircraft.cfg_code

  @property
  def cap_j(self):
    aircraft = self.get_aircraft()
    return aircraft.get_cap()[0]

  @property
  def cap_y(self):
    aircraft = self.get_aircraft()
    return aircraft.get_cap()[1] 

  @property
  def adjcap_j(self):
    return self.get_adjcap('J')

  @property
  def adjcap_y(self):
    return self.get_adjcap('Y')

  @property
  def booked_j(self):
    return self.get_pros_future_booked('J')

  @property
  def booked_y(self):
    return self.get_pros_future_booked('Y')

  @property
  def achdmd_j(self):
    return self.get_pros_ach_demand('J')

  @property
  def achdmd_y(self):
    return self.get_pros_ach_demand('Y')

  @property
  def excdmd_j(self):
    return self.achdmd_j - self.adjcap_j

  @property
  def excdmd_y(self):
    return self.achdmd_y - self.adjcap_y

  def get_adjcap(self,cmpt,daysprior='-1'):
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT adjcap FROM hleg_compartment\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "' AND\
               daysprior = '" + daysprior + "' AND\
               dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
               cmpsym = '" + cmpt + "'"
    curs.execute(q)
    row = curs.fetchone()
    # Sometimes it failes. May be cancelled flights?
    try:
      return row[0]
    except:
      return -1

  def get_pros_future_booked(self,cmpt):
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT booked FROM leg_compartment\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "' AND\
               dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
               cmpsym = '" + cmpt + "'"
    curs.execute(q)
    row = curs.fetchone()
    return row[0]

  def get_pros_ach_demand(self,cmpt):
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT achfnldmd FROM leg_compartment\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "' AND\
               dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
               cmpsym = '" + cmpt + "'"
    curs.execute(q)
    row = curs.fetchone()
    return row[0]

  def get_num_booked(self,cmpt):
    # FIXME: circular and multi-leg flights
    # are problematic here, because select
    # is done based on flight number!
    ads_curs = dbConnector.get_ads_curs()
    q = "SELECT COUNT(DISTINCT bkg_id)\
         FROM ads_bkg, ads_flight\
         WHERE ads_bkg.opr_flt_id = ads_flight.flt_id AND\
               ads_flight.flight_nbr = '" + self.fltnum.lstrip('0') + "' AND\
               ads_flight.flt_date = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
               cabin_cd = '" + cmpt + "'"
    ads_curs.execute(q)
    res = ads_curs.fetchone()
    if res is None:
      return 0
    else:
      return res[0]

  def get_num_conf_booked(self,cmpt):
    # FIXME: circular and multi-leg flights
    # are problematic here, because select
    # is done based on flight number!
    ads_curs = dbConnector.get_ads_curs()
    ads_curs.execute("SELECT COUNT(DISTINCT bkg_id)\
                      FROM ads_bkg, ads_flight\
                      WHERE ads_bkg.opr_flt_id = ads_flight.flt_id AND\
                            ads_flight.flight_nbr = '" + self.fltnum.lstrip('0') + "' AND\
                            ads_flight.flt_date = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                            ads_bkg.confirm_ind = 'Y' AND\
                            cabin_cd = '" + cmpt + "'")
    res = ads_curs.fetchone()
    if res is None:
      return 0
    else:
      return res[0]

  def get_num_conf_surv_booked(self,cmpt):
    # FIXME: circular and multi-leg flights
    # are problematic here, because select
    # is done based on flight number!
    ads_curs = dbConnector.get_ads_curs()
    ads_curs.execute("SELECT COUNT(DISTINCT bkg_id)\
                      FROM ads_bkg, ads_flight\
                      WHERE ads_bkg.opr_flt_id = ads_flight.flt_id AND\
                            ads_flight.flight_nbr = '" + self.fltnum.lstrip('0') + "' AND\
                            ads_flight.flt_date = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                            ads_bkg.confirm_ind = 'Y' AND\
                            ads_bkg.dead_ind = 'N' AND ads_bkg.bkg_cancel_dt_tm IS NULL AND\
                            cabin_cd = '" + cmpt + "'")
    res = ads_curs.fetchone()
    if res is None:
      return 0
    else:
      return res[0]

  def get_num_conf_surv_checkin_booked(self,cmpt):
    # FIXME: circular and multi-leg flights
    # are problematic here, because select
    # is done based on flight number!
    ads_curs = dbConnector.get_ads_curs()
    ads_curs.execute("SELECT COUNT(DISTINCT ads_checkin.bkg_id)\
                      FROM ads_bkg, ads_flight, ads_checkin\
                      WHERE ads_bkg.opr_flt_id = ads_flight.flt_id AND\
                            ads_bkg.bkg_id = ads_checkin.bkg_id AND\
                            ads_flight.flight_nbr = '" + self.fltnum.lstrip('0') + "' AND\
                            ads_flight.flt_date = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                            ads_bkg.cabin_cd = '" + cmpt + "' AND\
                            ads_bkg.confirm_ind = 'Y' AND\
                            ads_bkg.dead_ind = 'N' AND\
                            ads_bkg.bkg_cancel_dt_tm IS NULL AND\
                            ads_checkin.bk_pdi_infantindicator = 'N'")
    res = ads_curs.fetchone()
    if res is None:
      return 0
    else:
      return res[0]

  def get_num_conf_surv_checkin_brd_booked(self,cmpt):
    # FIXME: circular and multi-leg flights
    # are problematic here, because select
    # is done based on flight number!
    ads_curs = dbConnector.get_ads_curs()
    ads_curs.execute("SELECT COUNT(DISTINCT ads_checkin.bkg_id)\
                      FROM ads_bkg, ads_flight, ads_checkin\
                      WHERE ads_bkg.opr_flt_id = ads_flight.flt_id AND\
                            ads_bkg.bkg_id = ads_checkin.bkg_id AND\
                            ads_flight.flight_nbr = '" + self.fltnum.lstrip('0') + "' AND\
                            ads_flight.flt_date = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                            ads_bkg.cabin_cd = '" + cmpt + "' AND\
                            ads_bkg.confirm_ind = 'Y' AND\
                            ads_bkg.dead_ind = 'N' AND\
                            ads_bkg.bkg_cancel_dt_tm IS NULL AND\
                            ads_checkin.bk_pdi_infantindicator = 'N' AND\
                            ads_checkin.boarding_status = 'BDD'")
    res = ads_curs.fetchone()
    if res is None:
      return 0
    else:
      return res[0]

  def get_num_unconf_booked(self,cmpt):
    # FIXME: circular and multi-leg flights
    # are problematic here, because select
    # is done based on flight number!
    ads_curs = dbConnector.get_ads_curs()
    ads_curs.execute("SELECT COUNT(DISTINCT bkg_id)\
                      FROM ads_bkg, ads_flight\
                      WHERE ads_bkg.opr_flt_id = ads_flight.flt_id AND\
                            ads_flight.flight_nbr = '" + self.fltnum.lstrip('0') + "' AND\
                            ads_flight.flt_date = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                            ads_bkg.confirm_ind = 'N' AND\
                            cabin_cd = '" + cmpt + "'")
    res = ads_curs.fetchone()
    if res is None:
      return 0
    else:
      return res[0]

  def get_num_unconf_surv_booked(self,cmpt):
    # FIXME: circular and multi-leg flights
    # are problematic here, because select
    # is done based on flight number!
    ads_curs = dbConnector.get_ads_curs()
    ads_curs.execute("SELECT COUNT(DISTINCT bkg_id)\
                      FROM ads_bkg, ads_flight\
                      WHERE ads_bkg.opr_flt_id = ads_flight.flt_id AND\
                            ads_flight.flight_nbr = '" + self.fltnum.lstrip('0') + "' AND\
                            ads_flight.flt_date = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                            ads_bkg.confirm_ind = 'N' AND\
                            ads_bkg.dead_ind = 'N' AND ads_bkg.bkg_cancel_dt_tm IS NULL AND\
                            cabin_cd = '" + cmpt + "'")
    res = ads_curs.fetchone()
    if res is None:
      return 0
    else:
      return res[0]

  def get_num_unconf_surv_checkin_booked(self,cmpt):
    # FIXME: circular and multi-leg flights
    # are problematic here, because select
    # is done based on flight number!
    ads_curs = dbConnector.get_ads_curs()
    ads_curs.execute("SELECT COUNT(DISTINCT ads_checkin.bkg_id)\
                      FROM ads_bkg, ads_flight, ads_checkin\
                      WHERE ads_bkg.opr_flt_id = ads_flight.flt_id AND\
                            ads_bkg.bkg_id = ads_checkin.bkg_id AND\
                            ads_flight.flight_nbr = '" + self.fltnum.lstrip('0') + "' AND\
                            ads_flight.flt_date = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                            ads_bkg.cabin_cd = '" + cmpt + "' AND\
                            ads_bkg.confirm_ind = 'N' AND\
                            ads_bkg.dead_ind = 'N' AND\
                            ads_bkg.bkg_cancel_dt_tm IS NULL AND\
                            ads_checkin.bk_pdi_infantindicator = 'N'")
    res = ads_curs.fetchone()
    if res is None:
      return 0
    else:
      return res[0]

  def get_num_unconf_surv_checkin_brd_booked(self,cmpt):
    # FIXME: circular and multi-leg flights
    # are problematic here, because select
    # is done based on flight number!
    ads_curs = dbConnector.get_ads_curs()
    ads_curs.execute("SELECT COUNT(DISTINCT ads_checkin.bkg_id)\
                      FROM ads_bkg, ads_flight, ads_checkin\
                      WHERE ads_bkg.opr_flt_id = ads_flight.flt_id AND\
                            ads_bkg.bkg_id = ads_checkin.bkg_id AND\
                            ads_flight.flight_nbr = '" + self.fltnum.lstrip('0') + "' AND\
                            ads_flight.flt_date = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                            ads_bkg.cabin_cd = '" + cmpt + "' AND\
                            ads_bkg.confirm_ind = 'N' AND\
                            ads_bkg.dead_ind = 'N' AND\
                            ads_bkg.bkg_cancel_dt_tm IS NULL AND\
                            ads_checkin.bk_pdi_infantindicator = 'N' AND\
                            ads_checkin.boarding_status = 'BDD'")
    res = ads_curs.fetchone()
    if res is None:
      return 0
    else:
      return res[0]

  def get_pros_booked(self,cmpt,daysprior='-1'):
    pros_curs = dbConnector.get_prosuser_curs()
    pros_curs.execute("SELECT booked\
                       FROM hleg_compartment\
                       WHERE orgn = '" + self.orgn + "' AND\
                             dstn = '" + self.dstn + "' AND\
                             fltnum = '" + self.fltnum + "' AND\
                             dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                             daysprior = '" + daysprior + "' AND\
                             cmpsym = '" + cmpt + "'")
    res = pros_curs.fetchone()
    if res is None:
      return 0
    else:
      return res[0]

  def get_pros_au(self,cmpt,daysprior='-1'):
    pros_curs = dbConnector.get_prosuser_curs()
    pros_curs.execute("SELECT au\
                       FROM hleg_compartment\
                       WHERE orgn = '" + self.orgn + "' AND\
                             dstn = '" + self.dstn + "' AND\
                             fltnum = '" + self.fltnum + "' AND\
                             dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                             daysprior = '" + daysprior + "' AND\
                             cmpsym = '" + cmpt + "'")
    res = pros_curs.fetchone()
    if res is None:
      return 0
    else:
      return res[0]

  def get_pros_out(self,cmpt,daysprior='-1'):
    pros_curs = dbConnector.get_prosuser_curs()
    pros_curs.execute("SELECT consoutdmd\
                       FROM hleg_compartment\
                       WHERE orgn = '" + self.orgn + "' AND\
                             dstn = '" + self.dstn + "' AND\
                             fltnum = '" + self.fltnum + "' AND\
                             dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                             daysprior = '" + daysprior + "' AND\
                             cmpsym = '" + cmpt + "'")
    res = pros_curs.fetchone()
    if res is None:
      return 0
    else:
      return res[0]

  def get_pros_noshow(self,cmpt):
    pros_curs = dbConnector.get_prosuser_curs()
    pros_curs.execute("SELECT noshow\
                       FROM hleg_compartment\
                       WHERE orgn = '" + self.orgn + "' AND\
                             dstn = '" + self.dstn + "' AND\
                             fltnum = '" + self.fltnum + "' AND\
                             dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                             daysprior = '-1' AND\
                             cmpsym = '" + cmpt + "'")
    res = pros_curs.fetchone()
    if res is None:
      return 0
    else:
      return res[0]

  def get_pros_upgrade(self,cmpt):
    pros_curs = dbConnector.get_prosuser_curs()
    if cmpt == 'J':
      pros_curs.execute("SELECT upgrin\
                         FROM hleg_compartment\
                         WHERE orgn = '" + self.orgn + "' AND\
                               dstn = '" + self.dstn + "' AND\
                               fltnum = '" + self.fltnum + "' AND\
                               dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                               daysprior = '-1' AND\
                               cmpsym = '" + cmpt + "'")
    elif cmpt == 'Y':
      pros_curs.execute("SELECT upgrout\
                         FROM hleg_compartment\
                         WHERE orgn = '" + self.orgn + "' AND\
                               dstn = '" + self.dstn + "' AND\
                               fltnum = '" + self.fltnum + "' AND\
                               dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                               daysprior = '-1' AND\
                               cmpsym = '" + cmpt + "'")
    else:
      pass

    res = pros_curs.fetchone()
    if res is None:
      return 0
    else:
      return res[0]

  def get_weighted_avg_fare(self,cmpt):
    pros_curs = dbConnector.get_prosuser_curs()
    pros_curs.execute("SELECT clssym,booked,fare\
                       FROM hleg_class\
                       WHERE orgn = '" + self.orgn + "' AND\
                             dstn = '" + self.dstn + "' AND\
                             fltnum = '" + self.fltnum + "' AND\
                             dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                             daysprior = '-1' AND\
                             cmpsym = '" + cmpt + "'")
    rows = pros_curs.fetchall()
    wfares_sum = 0
    booked_sum = 0
    for row in rows:
      cls    = row[0]
      booked = row[1]
      fare   = row[2]
      wfares_sum += fare * booked
      booked_sum += booked
    return float(wfares_sum)/booked_sum

  def get_aircraft_chng_est(self):
    # This code is written for SVX route.
    # That's why we consider only E90 and A319.
    # FIXME: code should be flexible and suit
    # all markets. 

    # FIXME: THIS FUNCTION IS MESS! RE-WRITE! 
        
    # We need to calculate both possible revenue
    # and costs

    # current aircraft for this departure
    cur_ac = self.get_aircraft()
    max_extra_rev = 0
    best_ac = cur_ac

    # loop over all possible configurations
    for ac in aircraft.get_all_aircrafts('SVX'):  # That is done for SVX ONLY !!!!!!!!
      print ac
      if cur_ac.code == ac.code and cur_ac.cfg_code == ac.cfg_code:
        # skip, this is current 
        continue

      if ac.code[:2] == '90':
        new_costs = 17485.0
      elif ac.code[:2] == '19':
        new_costs = 21784.0
      else:
        print 'Strange aircraft code!'
        assert 0
        
      if cur_ac.code[:2] == '90':
        cur_costs = 17485.0
      elif cur_ac.code[:2] == '19':
        cur_costs = 21784.0
      else:
        print 'Strange aircraft code!'
        assert 0        
            
      to_extra_rev = self.__get_extra_greedy_revenue(ac)
      print 'To revenue', to_extra_rev
      # estimate return revenue
      ret_dep = self.get_return_dep()
      # FIXME: configuration could be different for return flight!!!
      from_extra_rev = ret_dep.__get_extra_greedy_revenue(ac)
      print 'From revenue', from_extra_rev

      if to_extra_rev is not None and from_extra_rev is not None:
        extra_rev = to_extra_rev + from_extra_rev
      else:
        extra_rev = None

      # FIXME: aircraft should know about
      # its costs
      if extra_rev is not None:
        if best_ac.code[:2] != cur_ac.code[:2]:
          if best_ac.code[:2] == '90' and cur_ac.code[:2] == '19':
            extra_rev += 4299
          else:
            extra_rev -= 4299

          if extra_rev is not None and extra_rev < 0:     
            continue
      
          if extra_rev is not None:
            if max_extra_rev < extra_rev:
              max_extra_rev = extra_rev
              best_ac = ac
      
    return [best_ac,max_extra_rev]
             
  def __get_extra_greedy_revenue(self,ac):
    # calculates extra revenue if configuration to ac
    # aircraft will change. The greedy fashion means
    # that we iterate over classes and try to put
    # extra demand in lowest possible class.
    achdmd_j = self.achdmd_j
    achdmd_y = self.achdmd_y  
    cur_cap_j = self.get_adjcap('J')
    cur_cap_y = self.get_adjcap('Y')
    [new_cap_j,new_cap_y] = ac.get_cap()
    #new_cap_j = self.get_adjcap('J')
    #new_cap_y = self.get_adjcap('Y')
    excdmd_j = achdmd_j - cur_cap_j 
    excdmd_y = achdmd_y - cur_cap_y

    if new_cap_j < self.booked_j or new_cap_y < self.booked_y:
      # RULE: we don't kick-off already booked passengers
      # that is merely rule. It could be revised.
      # Even more this configuration is not accepted 
      # for consideration. 
      return None

    if excdmd_j > 0:
      ex_rev_j = self.__greedy_acc_extra_cap('J',new_cap_j - cur_cap_j,excdmd_j)
    else:
      ex_rev_j = 0

    if excdmd_y > 0:
      ex_rev_y = self.__greedy_acc_extra_cap('Y',new_cap_y - cur_cap_y,excdmd_y)
    else:
      # no extra revenue 
      ex_rev_y = 0  
    return ex_rev_j + ex_rev_y 

  def __greedy_acc_extra_cap(self,cmpt,extra_cap,excdmd):
    clss = get_cmpt_clss(cmpt,'ASC')
    ret = 0

    # calculate average fare
    w_fare= 0
    w_sum = 0
    print 'Weights: ',
    for cls in clss:
      fare = self.get_cls_fare(cls)
      weight = self.__get_achdmd_weight(cmpt,cls)
      w_sum += weight
      print weight,
      w_fare += fare * weight
    print 'Sum of weights: ', w_sum

    print '\tCompartment: ', cmpt
    print '\tWeighted fare: ', w_fare
    print '\tExtra capacity: ', extra_cap
    print '\tExtra demand: ', excdmd

    ret = min(excdmd,extra_cap) * w_fare
    print 'Extra revenue: ', ret
    return ret

  def __get_achdmd_weight(self,cmpt,cls):
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT achfnldmd - booked FROM hleg_compartment\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "' AND\
               dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
               cmpsym = '" + cmpt + "' ORDER BY daysprior DESC"
    curs.execute(q)
    row = curs.fetchone()
    dmdtocome_cmpt = float(row[0])

    q = "SELECT achfnldmd - booked FROM hleg_class\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "' AND\
               dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
               clssym = '" + cls + "' ORDER BY daysprior DESC"
    curs.execute(q)
    row = curs.fetchone()
    dmdtocome_cls = float(row[0])

    if dmdtocome_cmpt == 0:
      return 0
    else:
      return dmdtocome_cls/dmdtocome_cmpt 

  def get_au_curve(self,cmpt=''):
    res = []
    if cmpt == '':
      res_j = self.get_au_curve('J')
      res_y = self.get_au_curve('Y')
      for e in zip(res_j,res_y):
        assert e[0][0] == e[1][0]
        res.append([e[0][0],e[0][1]+e[1][1]])
    else:
      curs = dbConnector.get_prosuser_curs()
      q = "SELECT daysprior,au FROM hleg_compartment\
           WHERE orgn = '" + self.orgn + "' AND\
                 dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND\
                 dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                 cmpsym = '" + cmpt + "'\
           ORDER BY daysprior"
      curs.execute(q)
      rows = curs.fetchall()
      for row in rows:
        res.append([row[0],row[1]])
    return res

  def get_booked_curve(self,cmpt=''):
    res = []
    if cmpt == '':
      res_j = self.get_booked_curve('J')
      res_y = self.get_booked_curve('Y')
      for e in zip(res_j,res_y):
        assert e[0][0] == e[1][0]
        res.append([e[0][0],e[0][1]+e[1][1]])
    else:
      curs = dbConnector.get_prosuser_curs()
      q = "SELECT daysprior,booked FROM hleg_compartment\
           WHERE orgn = '" + self.orgn + "' AND\
                 dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND\
                 dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                 cmpsym = '" + cmpt + "'\
           ORDER BY daysprior"
      curs.execute(q)
      rows = curs.fetchall()
      for row in rows:
        res.append([row[0],row[1]])
    return res

  def get_adjcap_curve(self,cmpt=''):
    res = []
    if cmpt == '':
      res_j = self.get_adjcap_curve('J')
      res_y = self.get_adjcap_curve('Y')
      for e in zip(res_j,res_y):
        assert e[0][0] == e[1][0]
        res.append([e[0][0],e[0][1]+e[1][1]])
    else:
      curs = dbConnector.get_prosuser_curs()
      q = "SELECT daysprior,adjcap FROM hleg_compartment\
           WHERE orgn = '" + self.orgn + "' AND\
                 dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND\
                 dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                 cmpsym = '" + cmpt + "'\
           ORDER BY daysprior"
      curs.execute(q)
      rows = curs.fetchall()
      for row in rows:
        res.append([row[0],row[1]])
    return res

  def get_vircap_curve(self,cmpt=''):
    res = []
    if cmpt == '':
      res_j = self.get_vircap_curve('J')
      res_y = self.get_vircap_curve('Y')
      for e in zip(res_j,res_y):
        assert e[0][0] == e[1][0]
        res.append([e[0][0],e[0][1]+e[1][1]])
    else:
      curs = dbConnector.get_prosuser_curs()
      q = "SELECT daysprior,vircap FROM hleg_compartment\
           WHERE orgn = '" + self.orgn + "' AND\
                 dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND\
                 dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                 cmpsym = '" + cmpt + "'\
           ORDER BY daysprior"
      curs.execute(q)
      rows = curs.fetchall()
      for row in rows:
        res.append([row[0],row[1]])
    return res

  def get_phycap_curve(self,cmpt=''):
    res = []
    if cmpt == '':
      res_j = self.get_phycap_curve('J')
      res_y = self.get_phycap_curve('Y')
      for e in zip(res_j,res_y):
        assert e[0][0] == e[1][0]
        res.append([e[0][0],e[0][1]+e[1][1]])
    else:
      curs = dbConnector.get_prosuser_curs()
      q = "SELECT daysprior,phycap FROM hleg_compartment\
           WHERE orgn = '" + self.orgn + "' AND\
                 dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND\
                 dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                 cmpsym = '" + cmpt + "'\
           ORDER BY daysprior"
      curs.execute(q)
      rows = curs.fetchall()
      for row in rows:
        res.append([row[0],row[1]])
    return res

  def get_dmdtocome_in_cls(self,cmpt,cls):
    if cls in self.dmdtocome_cache:
      return self.dmdtocome_cache[cls]
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT achfnldmd - booked FROM leg_class\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "' AND\
               dptdt = DATE('" + self.dptdt.strftime('%Y-%m-%d') + "') AND\
               cmpsym = '" + cmpt + "' AND\
               clssym = '" + cls + "'"
    curs.execute(q)
    row = curs.fetchone()
    self.dmdtocome_cache[cls] = row[0]
    return row[0] 

  def get_cls_fare(self,cls):   
    if cls in self.cls_fare_cache:
      return self.cls_fare_cache[cls] 
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT fare FROM leg_class\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "' AND\
               dptdt = DATE('" + self.dptdt.strftime('%Y-%m-%d') + "') AND\
               clssym = '" + cls + "'"
    curs.execute(q)   
    row = curs.fetchone()
    self.cls_fare_cache[cls] = row[0]
    return row[0] 

  def get_return_dep(self):
    # Method provides return departure object.
    # Rule is pretty simple. Swap origin and 
    # destination and increase flight number by 1.
    # Departure date should be greater or equal 
    # original one. 
    #
    # Return should be outbound. There is no return
    # for inbound.
    if int(self.fltnum) % 2 == 0:
      return None
    orgn = self.dstn
    dstn = self.orgn
    fltnum = str(int(self.fltnum) + 1).zfill(5)
    curs = dbConnector.get_prosuser_curs()
    curs.execute("SELECT dptdt\
                  FROM leg\
                  WHERE orgn = '" + orgn + "' AND\
                        dstn = '" + dstn + "' AND\
                        fltnum = '" + fltnum + "' AND\
                        dptdt > TO_DATE('" + self.dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd')")
    row = curs.fetchone()
    dptdt = row[0]
    return Departure(orgn,dstn,fltnum,dptdt)

  def get_db_paid_amount(self):
    return crmCase.get_dep_db_total_compensation(self.orgn,self.dstn,self.fltnum,self.dptdt)
   
  def get_db_num_pax(self):
    return crmCase.get_dep_db_total_num_pax(self.orgn,self.dstn,self.fltnum,self.dptdt)

  def get_fares_means_stds(self):
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT fare,uncdmd,uncstddev\
         FROM hleg_class\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "' AND\
               dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d')+"','yyyy-mm-dd') AND\
               daysprior = 1"
    curs.execute(q)
    fs = []
    mus = []
    stds = []
    rows = curs.fetchall()
    for row in rows:
      fs.append(row[0])
      mus.append(row[1])
      stds.append(row[2])
    return fs,mus,stds

  def get_booked_daysprior(self,cls,daysprior):
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT booked\
         FROM hleg_class\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "' AND\
               clssym = '" + cls + "' AND\
               dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d')+"','yyyy-mm-dd') AND\
               daysprior = 0"
    curs.execute(q)
    row = curs.fetchone()
    booked = row[0]
    return booked

  def get_fare_mean_std_booked_cls(self,cls):
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT fare,booked,uncdmd,uncstddev\
         FROM hleg_class\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "' AND\
               clssym = '" + cls + "' AND\
               dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d')+"','yyyy-mm-dd') AND\
               daysprior = 1"
    curs.execute(q)
    row = curs.fetchone()
    fare = row[0]
    booked = row[1]
    uncdmd = row[2]
    uncstddev = row[3]

    return fare,booked,uncdmd,uncstddev
 
  def get_revenue(self):
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT SUM(fare*booked)\
         FROM hleg_class\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "' AND\
               dptdt = TO_DATE('" + self.dptdt.strftime('%Y-%m-%d')+"','yyyy-mm-dd') AND\
               daysprior = 0"
    curs.execute(q)
    row = curs.fetchone()
    return row[0]

if __name__ == '__main__':
  orgn = 'HEL'
  dstn = 'JFK'
  fltnum = '00005'
  dptdt = date(2014,5,1)
  dep = Departure(orgn,dstn,fltnum,dptdt)
  print dep.is_departed()

    
