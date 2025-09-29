import sys
import time
from datetime import date, datetime, timedelta

from db_connector import dbConnector
from departure import Departure

PRCS_COSTS = 41.0

class Flight:

  @staticmethod
  def get_city(arprt):
    curs = dbConnector.get_ads_curs()
    q = "SELECT city FROM ads_airport\
         WHERE airport_nm = '" + arprt + "'"
    curs.execute(q)
    try:
      res = curs.fetchone()[0]
    except:
     return None
    return res

  @staticmethod
  def get_region(arprt):
    curs = dbConnector.get_ads_curs()
    q = "SELECT region FROM ads_airport\
         WHERE airport_nm = '" + arprt + "'"
    curs.execute(q)
    res = curs.fetchone()[0]
    return res

  @staticmethod
  def is_eu(arprt):
    if flight.get_region(arprt) == 'EUROP':
      return True
    return False

  @staticmethod
  def get_flights():
    ans = []
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT DISTINCT orgn,dstn,fltnum FROM leg_class ORDER BY fltnum"
    curs.execute(q)
    rows = curs.fetchall()
    for row in rows:
      ans.append([row[0],row[1],row[2]])
    return ans

  @staticmethod
  def get_managed_flights():
    ans = []
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT DISTINCT orgn,dstn,fltnum FROM leg_class\
         WHERE (fltnum > '00000' AND fltnum < '10000') OR\
               (fltnum > '03000' AND fltnum < '03300') OR\
               (fltnum > '03601' AND fltnum < '04000')\
         ORDER BY fltnum"
    curs.execute(q)
    rows = curs.fetchall()
    for row in rows:
      ans.append([row[0],row[1],row[2]])
    return ans

  @staticmethod
  def get_lh_managed_flights():
    ans = []
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT DISTINCT orgn,dstn,fltnum FROM leg_class\
         WHERE (fltnum > '00000' AND fltnum < '00100')\
         ORDER BY fltnum"
    curs.execute(q)
    rows = curs.fetchall()
    for row in rows:
      ans.append([row[0],row[1],row[2]])
    return ans

  @staticmethod
  def get_ob_flights_past(dfrom,dto):
    """Get overbooked flights in past
       Overbooked simple means that
       bookings are more than adjusted
       capacity"""
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT orgn,dstn,fltnum\
         FROM hleg_compartment\
         WHERE booked > adjcap AND\
               daysprior = '0' AND\
               cmpsym = 'Y' AND"

  @staticmethod
  def get_orgn_dstn(fltnum):
    curs = dbConnector.get_prosuser_curs()
    fltnum = str(int(fltnum)).zfill(5)
    q = "SELECT DISTINCT orgn,dstn FROM leg_class\
         WHERE fltnum = '" + fltnum + "'"
    curs.execute(q)
    row = curs.fetchone()
    try:
      return row[0],row[1]
    except:
      return 'XXX','XXX'

  @staticmethod
  def get_ob_flights_future():
    """Get overbooked flights in future.
       Overbooked simpley means that bookings
       more than adjusted capacity"""
    dt_now = datetime.now()   
    dt = dt_now+timedelta(days=60)

    curs = dbConnector.get_prosuser_curs()
    q = "SELECT DISTINCT orgn,dstn,fltnum,dptdt\
         FROM leg_compartment\
         WHERE booked > adjcap + 2 AND cmpsym='Y' AND\
               dptdt >= TO_DATE('"+dt_now.strftime('%Y-%m-%d')+"','yyyy-mm-dd') AND\
               dptdt <= TO_DATE('"+dt.strftime('%Y-%m-%d')+"','yyyy-mm-dd')"
    curs.execute(q)
    rows = curs.fetchall()
    return [[e[0],e[1]] for e in rows]

  def __init__(self,orgn,dstn,fltnum,dfrom=None,dto=None):
    self.orgn = orgn
    self.dstn = dstn
    self.fltnum = fltnum
    self.dfrom = dfrom # data for calculations considered from dfrom
    self.dto = dto     # data for calculations considered to dto

  def get_noshow(self,cmpt):
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT DISTINCT orgn,dstn,fltnum,dptdt,noshow\
         FROM hleg_compartment\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "' AND\
               cmpsym = '" + cmpt + "' AND\
               dptdt >= TO_DATE('" + self.dfrom.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
               dptdt <= TO_DATE('" + self.dto.strftime('%Y-%m-%d') + "','yyyy-mm-dd')\
         ORDER BY orgn,dstn,fltnum,dptdt"
    curs.execute(q)
    rows = curs.fetchall()
    for row in rows:
      orgn = row[0]
      dstn = row[1]
      fltnum = row[2]
      dptdt = row[3]
      noshow = row[4]
      print orgn,dstn,fltnum,dptdt,noshow

  def is_cmpt(self,cmpt):
    curs = dbConnector.get_prosuser_curs()
    if self.dfrom is not None and self.dto is not None:
      q = "SELECT COUNT(*) FROM hleg_class\
           WHERE orgn = '" + self.orgn + "' AND\
                 dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND\
                 cmpsym = '" + cmpt + "' AND\
                 dptdt >= DATE('" + self.dfrom.strftime('%Y-%m-%d') + "') AND\
                 dptdt <= DATE('" + self.dto.strftime('%Y-%m-%d') + "')"
    else:
      q = "SELECT COUNT(*) FROM hleg_class\
           WHERE orgn = '" + self.orgn + "' AND\
                 dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND\
                 cmpsym = '" + cmpt + "'"
    curs.execute(q)
    res = curs.fetchone()[0]
    if res == 0:
      return False
    return True

  def get_avg_yield(self,cmpt):
    curs = dbConnector.get_prosuser_curs()
    if self.dfrom is not None and self.dto is not None:
      q = "SELECT AVG(fare) FROM hleg_class\
           WHERE orgn = '" + self.orgn + "' AND\
                 dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND\
                 cmpsym = '" + cmpt + "' AND\
                 dptdt >= DATE('" + self.dfrom.strftime('%Y-%m-%d') + "') AND\
                 dptdt <= DATE('" + self.dto.strftime('%Y-%m-%d') + "')"
    else:
      q = "SELECT AVG(fare) FROM hleg_class\
           WHERE orgn = '" + self.orgn + "' AND\
                 dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND\
                 cmpsym = '" + cmpt + "'"
    curs.execute(q)
    res = curs.fetchone()[0]
    return res

  def get_avg_prime_yield(self,cmpt):
    curs = dbConnector.get_prosuser_curs()
    if self.dfrom is not None and self.dto is not None:
      q = "SELECT AVG(fare) FROM hleg_class\
           WHERE orgn = '" + self.orgn + "' AND\
                 dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND\
                 cmpsym = '" + cmpt + "' AND\
                 clssym = '" + cmpt + "' AND\
                 dptdt >= DATE('" + self.dfrom.strftime('%Y-%m-%d') + "') AND\
                 dptdt <= DATE('" + self.dto.strftime('%Y-%m-%d') + "')"
    else:
      q = "SELECT AVG(fare) FROM hleg_class\
           WHERE orgn = '" + self.orgn + "' AND\
                 dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND\
                 cmpsym = '" + cmpt + "' AND\
                 clssym = '" + cmpt + "'"
    curs.execute(q)
    res = curs.fetchone()[0]
    if res == None:
      return 0
    return res

  def get_mrgnl_dg_costs(self):
    mrgnl_dg_costs = 600.00 + PRCS_COSTS
    return mrgnl_dg_costs

  def get_mrgnl_db_costs(self,cmpt):
    if int(self.fltnum) < 100:
      is_lh = True
    else:
      is_lh = False
    if self.orgn == 'HEL': 
      is_inbound = False
    else:
      is_inbound = True

    # From Station Manual (Revision 48)
    # ---------------------------------
    # 
    # Trips less than 1500 km Euro 250
    # Trips 1500 - 3500 km and all intra EU in excess of 1500 km Euro 400
    # Trips more than 3500 km (non intra EU) Euro 600
    #

    # DB class  OUT A250   IN A250   OUT B400   IN B400   OUT C600   IN C600
    # ----------------------------------------------------------------------
    # RR cost   8.02       41.98     30.13      38.68     65.46      31.47 

        
    length = self.get_length()
    if length < 1500:
      db_cmpn = 250
    elif length > 3500 and not (flight.is_eu(self.orgn) and flight.is_eu(self.dstn)):
      db_cmpn = 600
    else:
      db_cmpn = 400
        
    if is_lh:
      if  is_inbound:
        return (float(db_cmpn) + 31.47 + PRCS_COSTS) 
      else:
        return (float(db_cmpn) + 65.46 + PRCS_COSTS)
    else:
      if is_inbound:
        return (float(db_cmpn) + 38.68 + PRCS_COSTS)
      else:
        return (float(db_cmpn) + 30.13 + PRCS_COSTS)

  def get_db_cost_factor(self,cmpt):
    db_costs = self.get_mrgnl_db_costs(cmpt)
    prime_fare = self.get_avg_prime_yield(cmpt)
    if prime_fare == 0:
      return -1
    else:
      return float(db_costs)/prime_fare 

  def get_booked_ts(self,dfrom = None,dto = None,cmpt = None,cls = None,dow = None):
    cursor = dbConnector.get_prosuser_curs()
    where_date_clause = ''
    if dfrom is not None:
      where_date_clause = " AND dptdt >= TO_DATE('"+ dfrom.strftime('%Y-%m-%d')+"','yyyy-mm-dd')"
    if dto is not None:
      where_date_clause += " AND dptdt <= TO_DATE('" + dto.strftime('%Y-%m-%d')+"','yyyy-mm-dd')"
        
    if cmpt is not None:
      cmpt = cmpt.strip()
    if cls is not None:
      cls = cls.strip()

    if dow is None:
      where_dow_clause = ''
    else:
      dow = ["TO_CHAR(dptdt,'D') = '"+str(e)+"'" for e in dow]
      where_dow_clause = ' OR '.join(dow)
      where_dow_clause = ' AND (' + where_dow_clause + ')'

    if cmpt is not None and cmpt != '':
      q = "SELECT dptdt,booked\
           FROM hleg_compartment\
           WHERE (orgn,dstn,fltnum,dptdt,cmpsym,daysprior) IN\
             (SELECT orgn,dstn,fltnum,dptdt,cmpsym,MIN(daysprior)\
              FROM hleg_compartment\
              WHERE crr = 'AY' AND\
                    orgn = '" + self.orgn + "' AND\
                    dstn = '" + self.dstn + "' AND\
                    fltnum = '" + self.fltnum + "' AND\
                    cmpsym = '" + cmpt + "'" + where_date_clause + where_dow_clause + "\
              GROUP BY orgn,dstn,fltnum,dptdt,cmpsym) ORDER BY dptdt"
    elif cls is not None and cls != '':
      q = "SELECT dptdt,booked\
           FROM hleg_class\
           WHERE (orgn,dstn,fltnum,dptdt,clssym,daysprior) IN\
             (SELECT orgn,dstn,fltnum,dptdt,clssym,MIN(daysprior)\
              FROM hleg_class\
              WHERE crr = 'AY' AND\
                    orgn = '" + self.orgn + "' AND\
                    dstn = '" + self.dstn + "' AND\
                    fltnum = '" + self.fltnum + "' AND\
                    clssym = '" + cls + "'" + where_date_clause + where_dow_clause + "\
              GROUP BY orgn,dstn,fltnum,dptdt,clssym) ORDER BY dptdt" 
    else:
      q = "SELECT dptdt,booked\
           FROM hleg\
           WHERE (orgn,dstn,fltnum,dptdt,daysprior) IN\
             (SELECT orgn,dstn,fltnum,dptdt,MIN(daysprior)\
              FROM hleg\
              WHERE crr = 'AY' AND\
                    orgn = '" + self.orgn + "' AND\
                    dstn = '" + self.dstn + "' AND\
                    fltnum = '" + self.fltnum + "'" + where_date_clause + where_dow_clause + "\
              GROUP BY orgn,dstn,fltnum,dptdt) ORDER BY dptdt"
    print q
    cursor.execute(q) 
    ret = []
    row = cursor.fetchone()
    while row is not None:
      ret.append([row[0],row[1]])
      row = cursor.fetchone()
    return ret

  def get_booked_yield_ts(self,dfrom=None,dto=None,cmpt=None,cls=None,dow=None):
    bs = self.get_booked_ts(dfrom,dto,cmpt,cls,dow)
    ys = self.get_yield_ts(dfrom,dto,cmpt,dow)
    bd = {}
    for e in bs:
      k = e[0]
      v = e[1]
      bd[k] = v
      yd = {}
    for e in ys:
      k = e[0]
      v = e[1]
      yd[k] = v
    res = []
    for k in bd.keys():
      try:
        res.append([bd[k],yd[k]])
      except:
        pass
    return res

  def get_forecast_booked_ts(self,dfrom=None,dto=None,cmpt=None,cls=None,dow=None):
    cursor = dbConnector.get_prosuser_curs()
    if cmpt is not None:
      cmpt = cmpt.strip()
    if cls is not None:
      cls = cls.strip()

    if dow is None:
      where_dow_clause = ''
    else:
      dow = ["TO_CHAR(dptdt,'D') = '" + str(e) + "'" for e in dow]
      where_dow_clause = ' OR '.join(dow)
      where_dow_clause = ' AND (' + where_dow_clause + ')'

    if cmpt is not None and cmpt != '':
      if dfrom is not None and dto is not None:
        add_where_clause = " AND leg_compartment.dptdt >= TO_DATE('" + dfrom.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                                 leg_compartment.dptdt <= TO_DATE('" + dto.strftime('%Y-%m-%d') + "','yyyy-mm-dd')"
      else:
        add_where_clause = ""
      q = "SELECT dptdt,consfnldmd,achfnldmd,booked\
           FROM leg_compartment\
           WHERE (orgn,dstn,fltnum,dptdt,cmpsym,daysprior) IN\
             (SELECT orgn,dstn,fltnum,dptdt,cmpsym,MIN(daysprior)\
              FROM leg_compartment\
              WHERE crr = 'AY' AND\
                    orgn = '" + self.orgn + "' AND\
                    dstn = '" + self.dstn + "' AND\
                    fltnum = '" + self.fltnum + "' AND\
                    cmpsym = '" + cmpt + "' \
                    " + where_dow_clause + " " + add_where_clause + "\
             GROUP BY orgn,dstn,fltnum,dptdt,cmpsym) ORDER BY dptdt" 
    elif cls is not None and cls != '':
      if dfrom is not None and dto is not None:
        add_where_clause = " AND leg_class.dptdt >= TO_DATE('" + dfrom.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                                 leg_class.dptdt <= TO_DATE('" + dto.strftime('%Y-%m-%d') + "','yyyy-mm-dd')"
      else:
        add_where_clause = ""
      q = "SELECT dptdt,consfnldmd,achfnldmd,booked\
           FROM leg_class\
           WHERE (orgn,dstn,fltnum,dptdt,clssym,daysprior) IN\
            (SELECT  orgn,dstn,fltnum,dptdt,clssym,MIN(daysprior)\
             FROM leg_class\
             WHERE crr = 'AY' AND\
                   orgn = '" + self.orgn + "' AND\
                   dstn = '" + self.dstn + "' AND\
                   fltnum = '" + self.fltnum + "' AND\
                   clssym = '" + cls + "' AND\
                   dptdt >= TO_DATE('" + datetime.now().strftime('%Y-%m-%d') + "','yyyy-mm-dd')" + where_dow_clause + " " + add_where_clause + "\
             GROUP BY orgn,dstn,fltnum,dptdt,clssym) ORDER BY dptdt"
    else:
      if dfrom is not None and dto is not None:
        add_where_clause = " AND leg.dptdt >= TO_DATE('" + dfrom.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                                 leg.dptdt <= TO_DATE('" + dto.strftime('%Y-%m-%d') + "','yyyy-mm-dd')"
      else:
        add_where_clause = ""
      q = "SELECT dptdt,consfnldmd,achfnldmd,booked\
           FROM leg\
           WHERE (orgn,dstn,fltnum,dptdt,daysprior) IN\
           (SELECT orgn,dstn,fltnum,dptdt,MIN(daysprior)\
            FROM leg\
            WHERE crr = 'AY' AND\
                  orgn = '" + self.orgn + "' AND\
                  dstn = '" + self.dstn + "' AND\
                  fltnum = '" + self.fltnum + "' AND\
                  dptdt >= TO_DATE('"+datetime.now().strftime('%Y-%m-%d')+"','yyyy-mm-dd')" + where_dow_clause + " " + add_where_clause + "\
            GROUP BY orgn,dstn,fltnum,dptdt) ORDER BY dptdt"
    cursor.execute(q) 
    ret = []
    row = cursor.fetchone()
    while row is not None:
      ret.append([row[0],row[1],row[2],row[3]])
      row = cursor.fetchone()
    return ret

  def get_booked_cmpt_ts(self,cmpt):
    cursor = dbConnector.get_prosuser_curs()
    q = "SELECT dptdt,adjcap,booked\
         FROM hleg_compartment\
         WHERE (orgn,dstn,fltnum,cmpsym,dptdt,daysprior) IN\
         (SELECT orgn,dstn,fltnum,cmpsym,dptdt,MIN(daysprior)\
          FROM hleg_compartment\
          WHERE crr = 'AY' AND\
                orgn = '" + self.orgn + "' AND\
                dstn = '" + self.dstn + "' AND\
                fltnum = '" + self.fltnum + "' AND\
                cmpsym = '" + cmpt + "'\
          GROUP BY orgn,dstn,fltnum,cmpsym,dptdt) ORDER BY dptdt"  
    cursor.execute(q)
    ret = []
    row = cursor.fetchone()
    while row is not None:
      ret.append([row[0],row[1],row[2]])
      row = cursor.fetchone()
    return ret

  def get_booked_cls_mix_ts(self,dfrom=None,dto=None):
    cursor = dbConnector.get_prosuser_curs()
    if dfrom is not None and dto is not None:
      q = "SELECT dptdt, cmpsym, clssym, booked\
           FROM hleg_class\
           WHERE orgn = '" + self.orgn + "' AND\
                 dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND daysprior = -1 AND\
                 dptdt >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
                 dptdt <= DATE('" + dto.strftime('%Y-%m-%d') + "')\
           ORDER BY dptdt,cmpsym,clssym"
    else:
      q = "SELECT dptdt, cmpsym, clssym, booked\
           FROM hleg_class\
           WHERE orgn = '" + self.orgn + "' AND\
                 dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND daysprior = -1\
           ORDER BY dptdt,cmpsym,clssym"
    cursor.execute(q)
    ret  = []
    rets = []
    summ = 0
    row = cursor.fetchone()
    prev_dptdt = None
    while row is not None:
      dptdt  = row[0]
      cmpt   = row[1]
      cls    = row[2]
      booked = row[3] 
            
      if prev_dptdt == dptdt:
        summ += booked
        ret.append(summ)
      else:
        summ = 0
        rets.append(ret)
        ret = [dptdt]
        row = cursor.fetchone() 
        prev_dptdt = dptdt
    return rets
 
  def get_rev_ts(self,dfrom=None,dto=None):
    if dfrom is not None and dto is not None:
      add_where_clause = " AND hleg.dptdt >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
                               hleg.dptdt <= DATE('" + dto.strftime('%Y-%m-%d') + "')"
    else:
      add_where_clause = ""
    cursor = dbConnector.get_prosuser_curs()

    q = "SELECT hleg_class.dptdt,SUM(hleg_class.booked*hleg_class.fare),hleg.fltaircrafttype\
         FROM hleg_class,hleg\
         WHERE hleg_class.orgn = hleg.orgn AND\
               hleg_class.dstn = hleg.dstn AND\
               hleg_class.fltnum = hleg.fltnum AND\
               hleg_class.dptdt = hleg.dptdt AND\
               hleg_class.daysprior = hleg.daysprior AND\
               ( hleg.orgn,hleg.dstn,hleg.fltnum,hleg.dptdt,hleg.daysprior ) IN\
               ( SELECT hleg.orgn,hleg.dstn,hleg.fltnum,hleg.dptdt,MIN(hleg.daysprior)\
                 FROM hleg\
                 WHERE hleg.orgn = '" + self.orgn + "' AND\
                       hleg.dstn = '" + self.dstn + "' AND\
                       hleg.fltnum = '" + self.fltnum + "'" + add_where_clause + "\
                 GROUP BY hleg.orgn,hleg.dstn,hleg.fltnum,hleg.dptdt)\
         GROUP BY hleg_class.orgn,hleg_class.dstn,hleg_class.fltnum,hleg_class.dptdt,hleg.fltaircrafttype\
         ORDER BY hleg_class.dptdt"
       
    cursor.execute(q)
    ret = []
    row = cursor.fetchone()
    while row is not None:
      actype = row[2][0:2]
      costs = 0
      if actype == '70' or actype == '90':
        costs = '8742' # costs/2 because of round-trip costs
      else:
        costs = '10872' # costs/2 because of round-trip
      ret.append([row[0],row[1],costs])
      row = cursor.fetchone()
    return ret

  def get_yield_ts(self,dfrom=None,dto=None,cmpt=None,dow=None):
    if cmpt is not None:
      if dfrom is not None and dto is not None:
        add_where_clause = " AND hleg_compartment.dptdt >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
                                 hleg_compartment.dptdt <= DATE('" + dto.strftime('%Y-%m-%d') + "')"
      else:
        add_where_clause = ""

      if dow is not None:
        is_first = True
        add_where_clause += ' AND ('
        for e in dow:
          if not is_first:
            add_where_clause += ' OR '
            e = int(e)
            add_where_clause += 'DAYOFWEEK_ISO(hleg_compartment.dptdt) = ' + str(e)
            is_first = False
        add_where_clause += ')'
            
        cursor = dbConnector.get_prosuser_curs()
        q = "SELECT hleg_class.dptdt,SUM(hleg_class.booked*hleg_class.fare)/SUM(hleg_class.booked)\
             FROM hleg_class,hleg_compartment\
             WHERE hleg_class.orgn = hleg_compartment.orgn AND\
                   hleg_class.dstn = hleg_compartment.dstn AND\
                   hleg_class.fltnum = hleg_compartment.fltnum AND\
                   hleg_class.dptdt = hleg_compartment.dptdt AND\
                   hleg_class.daysprior = hleg_compartment.daysprior AND\
                   hleg_class.cmpsym = '" + cmpt + "' AND\
                   hleg_class.clssym NOT IN ('F','U','G','A','X','E') AND\
                   ( hleg_compartment.orgn,hleg_compartment.dstn,hleg_compartment.fltnum,hleg_compartment.cmpsym,hleg_compartment.dptdt,hleg_compartment.daysprior ) IN\
                   ( SELECT hleg_compartment.orgn,hleg_compartment.dstn,hleg_compartment.fltnum,hleg_compartment.cmpsym,hleg_compartment.dptdt,MIN(hleg_compartment.daysprior)\
                     FROM hleg_compartment\
                     WHERE hleg_compartment.orgn = '" + self.orgn + "' AND\
                           hleg_compartment.dstn = '" + self.dstn + "' AND\
                           hleg_compartment.fltnum = '" + self.fltnum + "'" + add_where_clause + " AND\
                           hleg_compartment.cmpsym = '" + cmpt + "'\
                     GROUP BY hleg_compartment.orgn,hleg_compartment.dstn,hleg_compartment.fltnum,hleg_compartment.cmpsym,hleg_compartment.dptdt)\
             GROUP BY hleg_class.orgn,hleg_class.dstn,hleg_class.fltnum,hleg_class.cmpsym,hleg_class.dptdt\
             HAVING SUM(hleg_class.booked) <> 0\
             ORDER BY hleg_class.dptdt"
      else:
        if dfrom is not None and dto is not None:
          add_where_clause = " AND hleg.dptdt >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
                                   hleg.dptdt <= DATE('" + dto.strftime('%Y-%m-%d') + "')"
    else:
      add_where_clause = ""

      if dow is not None:
        is_first = True
        add_where_clause += ' AND ('
        for e in dow:
          if not is_first:
            add_where_clause += ' OR '
          e = int(e)
          add_where_clause += 'DAYOFWEEK_ISO(hleg.dptdt) = ' + str(e)
          is_first = False
        add_where_clause += ')'
            
      cursor = dbConnector.get_prosuser_curs()
      q = "SELECT hleg_class.dptdt,SUM(hleg_class.booked*hleg_class.fare)/SUM(hleg_class.booked)\
           FROM hleg_class,hleg\
           WHERE hleg_class.orgn = hleg.orgn AND\
                 hleg_class.dstn = hleg.dstn AND\
                 hleg_class.fltnum = hleg.fltnum AND\
                 hleg_class.dptdt = hleg.dptdt AND\
                 hleg_class.daysprior = hleg.daysprior AND\
                 hleg_class.clssym NOT IN ('F','U','G','A','X','E') AND\
                 ( hleg.orgn,hleg.dstn,hleg.fltnum,hleg.dptdt,hleg.daysprior ) IN\
                 ( SELECT hleg.orgn,hleg.dstn,hleg.fltnum,hleg.dptdt,MIN(hleg.daysprior)\
                   FROM hleg\
                   WHERE hleg.orgn = '" + self.orgn + "' AND\
                         hleg.dstn = '" + self.dstn + "' AND\
                         hleg.fltnum = '" + self.fltnum + "'" + add_where_clause + "\
                   GROUP BY hleg.orgn,hleg.dstn,hleg.fltnum,hleg.dptdt)\
           GROUP BY hleg_class.orgn,hleg_class.dstn,hleg_class.fltnum,hleg_class.dptdt\
           HAVING SUM(hleg_class.booked) <> 0\
           ORDER BY hleg_class.dptdt"

      cursor.execute(q)
      ret = []
      row = cursor.fetchone()
      while row is not None:
        ret.append([row[0],row[1]])
        row = cursor.fetchone()
    return ret

  def get_rev_future_ts(self,dfrom=None,dto=None):
    if dfrom is not None and dto is not None:
      add_where_clause = " AND leg_class.dptdt >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
                               leg_class.dptdt <= DATE('" + dto.strftime('%Y-%m-%d') + "')"
    else:
      add_where_clause = ""
    cursor = dbConnector.get_prosuser_curs()
    curr_dt = datetime.now()
    q = "SELECT leg_class.dptdt,\
                SUM(leg_class.booked*leg_class.fare),\
                SUM(leg_class.consfnldmd*leg_class.fare),\
                leg.fltaircrafttype\
         FROM leg_class,leg\
         WHERE leg_class.orgn = '" + self.orgn + "' AND\
               leg_class.dstn = '" + self.dstn + "' AND\
               leg_class.fltnum = '" + self.fltnum + "' AND\
               leg_class.orgn = leg.orgn AND\
               leg_class.dstn = leg.dstn AND\
               leg_class.fltnum = leg.fltnum AND\
               leg_class.dptdt = leg.dptdt AND\
               leg_class.dptdt >= DATE('" + curr_dt.strftime('%Y-%m-%d') + "') AND\
               leg_class.daysprior = leg.daysprior " + add_where_clause + " \
         GROUP BY leg_class.orgn,leg_class.dstn,leg_class.fltnum,leg_class.dptdt,leg.fltaircrafttype\
         ORDER BY leg_class.dptdt"
    cursor.execute(q)
    ret = []
    row = cursor.fetchone()
    while row is not None:
      actype = row[3][0:2]
      costs = 0
      if actype == '70' or actype == '90':
        costs = '8742' # costs/2
      else:
        costs = '10872' # costs/2
      ret.append([row[0],row[1],row[2],costs])
      row = cursor.fetchone()
    return ret

  def get_yield_future_ts(self,dfrom=None,dto=None):
    if dfrom is not None and dto is not None:
      add_where_clause = " AND leg_class.dptdt >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
                               leg_class.dptdt <= DATE('" + dto.strftime('%Y-%m-%d') + "')"
    else:
      add_where_clause = ""
    cursor = dbConnector.get_prosuser_curs()
    curr_dt = datetime.now()
    q = "SELECT leg_class.dptdt,\
           CASE WHEN SUM(leg_class.booked) = 0\
                THEN 0\
                ELSE SUM(leg_class.booked*leg_class.fare)/SUM(leg_class.booked) END,\
           CASE WHEN SUM(leg_class.consfnldmd) = 0\
                THEN 0\
                ELSE SUM(leg_class.consfnldmd*leg_class.fare)/SUM(leg_class.consfnldmd) END\
         FROM leg_class,leg\
         WHERE leg_class.orgn = '" + self.orgn + "' AND\
               leg_class.dstn = '" + self.dstn + "' AND\
               leg_class.fltnum = '" + self.fltnum + "' AND\
               leg_class.orgn = leg.orgn AND\
               leg_class.dstn = leg.dstn AND\
               leg_class.fltnum = leg.fltnum AND\
               leg_class.dptdt = leg.dptdt AND\
               leg_class.dptdt >= DATE('" + curr_dt.strftime('%Y-%m-%d') + "') AND\
               leg_class.daysprior = leg.daysprior " + add_where_clause + "\
         GROUP BY leg_class.orgn,leg_class.dstn,leg_class.fltnum,leg_class.dptdt\
         ORDER BY leg_class.dptdt"
    cursor.execute(q)
    ret = []
    row = cursor.fetchone()
    while row is not None:
      ret.append([row[0],row[1],row[2]])
      row = cursor.fetchone()
    return ret

  def get_rev_cmpt_ts(self,cmpt):
    cursor = dbConnector.get_prosuser_curs()
    q = "SELECT dptdt,SUM(booked*fare)\
         FROM hleg_class\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "' AND\
               daysprior = -1 AND\
               cmpsym = '" + cmpt + "'\
         GROUP BY orgn,dstn,fltnum,dptdt\
         ORDER BY dptdt"
    cursor.execute(q)
    ret = []
    row = cursor.fetchone()
    while row is not None:
      ret.append([row[0],row[1]])
      row = cursor.fetchone()
    return ret

  def get_first_dep_date(self):
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT MIN(dptdt) FROM hleg_compartment\
         WHERE orgn = '" + self.orgn + "' AND dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "'"
    curs.execute(q)
    row = curs.fetchone()
    return row[0]

  def get_last_dep_date(self):
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT MAX(dptdt) FROM hleg_compartment\
         WHERE orgn = '" + self.orgn + "' AND dstn = '" + self.dstn + "' AND\
               fltnum = '" + self.fltnum + "'"
    curs.execute(q)
    row = curs.fetchone()
    return row[0]

  def get_num_deps(self):
    if self.dfrom is not None and self.dto is not None:
      # cancelled departures aren't counted
      curs = dbConnector.get_prosuser_curs()
      q = "SELECT COUNT(DISTINCT dptdt) FROM hleg_compartment\
           WHERE orgn = '" + self.orgn + "' AND dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND daysprior = '-1' AND\
                 dptdt >= DATE('" + self.dfrom.strftime('%Y-%m-%d') + "') AND\
                 dptdt <= DATE('" + self.dto.strftime('%Y-%m-%d') + "')"
      curs.execute(q)
      row = curs.fetchone()
      return row[0]
    else:
      # all departures (past,cancelled and future)
      curs = dbConnector.get_prosuser_curs()
      q = "SELECT COUNT(DISTINCT dptdt) FROM hleg_compartment\
           WHERE orgn = '" + self.orgn + "' AND dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "'"
      curs.execute(q)
      row = curs.fetchone()
      return row[0]

  def get_num_flown_deps(self):
    if self.dfrom is not None and self.dto is not None:
      pass
    else:
      curs = dbConnector.get_prosuser_curs()
      q = "SELECT COUNT(DISTINCT dptdt) FROM hleg_compartment\
           WHERE orgn = '" + self.orgn + "' AND dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND daysprior = '-1'"
      curs.execute(q)
      row = curs.fetchone()
      return row[0]

  def get_num_past_deps(self):
    if self.dfrom is not None and self.dto is not None:
      pass
    else:
      curs = dbConnector.get_prosuser_curs()
      q = "SELECT COUNT(DISTINCT dptdt) FROM hleg_compartment\
           WHERE orgn = '" + self.orgn + "' AND dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND dptdt < DATE('" + datetime.now().strftime('%Y-%m-%d') + "')"
      curs.execute(q)
      row = curs.fetchone()
    return row[0]

  def get_future_deps(self,dfrom,dto):
    curs = dbConnector.get_prosuser_curs()
    if dfrom is not None and dto is not None:
      q = "SELECT DISTINCT orgn,dstn,fltnum,dptdt FROM hleg\
           WHERE orgn = '" + self.orgn + "' AND dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND\
                 dptdt >= TO_DATE('" + dfrom.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                 dptdt <= TO_DATE('" + dto.strftime('%Y-%m-%d') + "','yyyy-mm-dd') ORDER BY dptdt"
    else:
      q = "SELECT DISTINCT orgn,dstn,fltnum,dptdt FROM hleg\
           WHERE orgn = '" + self.orgn + "' AND dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND\
                 dptdt > TO_DATE('" + datetime.now().strftime('%Y-%m-%d') + "','yyyy-mm-dd') ORDER BY dptdt"
    print q
    curs.execute(q)
    row = curs.fetchone()
    deps = []
    while row is not None:
      dep = Departure(row[0],row[1],row[2],row[3])
      deps.append(dep)
      row = curs.fetchone()
    return deps

  def get_num_standbys(self):
    curs = dbConnector.get_ads_curs()
    q = "SELECT COUNT(ads_bkg.bkg_id)\
         FROM ads_bkg, ads_flight, ads_checkin\
         WHERE ads_bkg.opr_flt_id = ads_flight.flt_id AND\
               ads_bkg.bkg_id = ads_checkin.bkg_id AND\
               ads_bkg.cabin_cd = 'Y' AND\
               ads_bkg.confirm_ind = 'N' AND\
               ads_bkg.dead_ind = 'N' AND\
               ads_bkg.bkg_cancel_dt_tm IS NULL AND\
               ads_checkin.bk_pdi_infantindicator = 'N' AND\
               ads_bkg.boarding_ind = 'Y' AND\
               ads_checkin.boarding_status = 'BDD' AND\
               ads_flight.flt_date >= DATE('"+self.dfrom.strftime('%Y-%m-%d')+"') AND\
               ads_flight.flt_date <= DATE('"+self.dto.strftime('%Y-%m-%d')+"') AND\
               ads_flight.flt_carrer_cd = 'AY' AND\
               ads_flight.flight_nbr = '" + self.fltnum.lstrip('0') + "'"
    curs.execute(q)
    row = curs.fetchone()
    return row[0]

  def get_length(self): 
    orgn_city = flight.get_city(self.orgn)
    dstn_city = flight.get_city(self.dstn)
    curs = dbConnector.get_dwadm_curs()
    q = "SELECT gckm FROM traffic_leg\
         WHERE ayfrom = '" + orgn_city + "' AND\
               ayto = '" + dstn_city + "'"
    curs.execute(q)
    res = curs.fetchone()[0]
    return res

  def get_vircap_stats(self,daysprior='-1',cmpt=''):
    res = []
    if cmpt == '':
      res_j = self.get_vircap_stats(daysprior=daysprior,cmpt=cmpt)
      res_y = self.get_vircap_stats(daysprior=daysprior,cmpt=cmpt)
      for e in zip(res_j,res_y):
        assert e[0][0] == e[1][0]
        res.append([e[0][0],e[0][1]+e[1][1]])
    else:
      curs = dbConnector.get_prosuser_curs()
      q = "SELECT dptdt,vircap FROM hleg_compartment\
           WHERE orgn = '" + self.orgn + "' AND\
                 dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND\
                 daysprior = '" + daysprior + "' AND\
                 dptdt >= TO_DATE('" + self.dfrom.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                 dptdt <= TO_DATE('" + self.dto.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                 cmpsym = '" + cmpt + "'\
           ORDER BY dptdt"
      curs.execute(q)
      rows = curs.fetchall()
      for row in rows:
        res.append([row[0],row[1]])
    return res

  def get_dfrom(self):
    return self.dfrom

  def get_dto(self):
    return self.dto






