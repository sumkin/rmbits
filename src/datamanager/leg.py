import os
import sys
import time
from datetime import datetime, date, timedelta
import pickle
import ConfigParser

from neo4jrestclient.client import GraphDatabase

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector
from crm_case import *

gdb = GraphDatabase('http://localhost:7474/db/data')

class Leg:
  def __init__(self,orgn,dstn):
    self.orgn = orgn
    self.dstn = dstn

  @staticmethod
  def get_legs():
    # FIXME: leg is origin+destination. No flight number.
    pros_curs = dbConnector.get_prosuser_curs()
    pros_curs.execute("SELECT DISTINCT orgn,dstn,fltnum,dptdt FROM hleg")
    ress = pros_curs.fetchall()
    for res in ress:
      yield [res[0].strip(),res[1].strip(),res[2].strip(),res[3].strftime('%Y-%m-%d')]

  @staticmethod
  def get_managed_legs():
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT DISTINCT orgn,dstn\
         FROM leg\
         WHERE (fltnum > '00000' AND fltnum < '01000') OR\
               (fltnum > '03000' AND fltnum < '03300') OR\
               (fltnum > '03600' AND fltnum < '04000')\
         ORDER BY orgn,dstn"
    curs.execute(q)
    rows = curs.fetchall()
    res = [Leg(e[0].strip(),e[1].strip()) for e in rows]
    return res

  def get_fltnums(self):
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT DISTINCT fltnum FROM leg\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "'"
    curs.execute(q)
    rows = curs.fetchall()
    return [e[0] for e in rows]

  def get_fltnums_day(self,dt):
    """Returns distinct flight numbers
       for given date"""
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT DISTINCT fltnum FROM hleg\
         WHERE dptdt = TO_DATE('"+dt.strftime('%Y-%m-%d')+"','yyyy-mm-dd') AND\
               orgn = '"+self.orgn+"' AND\
               dstn = '"+self.dstn+"'"
    curs.execute(q)
    rows = curs.fetchall()
    return [e[0] for e in rows]

  def get_au_booked_adjcap_day(self,dt,cmpt=''):
    """Calculates total number of overbooked seats 
       for given date. Number of overbooked seats
       is calculated for daysprior 0"""
    if cmpt == '':
      au_j,booked_j,adjcap_j = self.get_au_booked_adjcap_day(dt,cmpt='J')
      au_y,booked_y,adjcap_y = self.get_au_booked_adjcap_day(dt,cmpt='Y')
      return au_j+au_y,booked_j+booked_y,adjcap_j+adjcap_y
    else:
      curs = dbConnector.get_prosuser_curs()
      q = "SELECT SUM(au),AVG(booked),SUM(adjcap) FROM hleg_compartment\
           WHERE dptdt = TO_DATE('"+dt.strftime('%Y-%m-%d')+"','yyyy-mm-dd') AND\
                 daysprior = '0' AND orgn='"+self.orgn+"' AND dstn='"+self.dstn+"' AND\
                 cmpsym='"+cmpt+"'"
      curs.execute(q)
      row = curs.fetchone()
      au,booked,adjcap = row
      return au,booked,adjcap

  def get_mrkt(self):
    if self.orgn != 'HEL':
      return self.orgn
    else:
      return self.dstn

  def transit_from_npax(self):
    mrkt = self.get_mrkt()
    q = "START n = node(*)\
         MATCH (n)-[r:FROM_TO_DAILY]->(m)\
         WHERE n.code? = '" + mrkt + "'\
         RETURN SUM(r.num_pax)"
    results = gdb.query(q)
    return results[0][0]    

  def transit_to_npax(self):
    mrkt = self.get_mrkt()
    q = "START n = node(*)\
         MATCH (n)-[r:FROM_TO_DAILY]->(m)\
         WHERE m.code? = '" + mrkt + "'\
         RETURN SUM(r.num_pax)"
    results = gdb.query(q)
    return results[0][0]
 
  def transit_from_rev(self):
    mrkt = self.get_mrkt()
    q = "START n = node(*)\
         MATCH (n)-[r:FROM_TO_DAILY]->(m)\
         WHERE n.code? = '" + mrkt + "'\
         RETURN SUM(r.rev)"
    results = gdb.query(q)
    return results[0][0]

  def transit_to_rev(self):
    mrkt = self.get_mrkt()
    q = "START n = node(*)\
         MATCH (n)-[r:FROM_TO_DAILY]->(m)\
         WHERE m.code? = '" + mrkt + "'\
         RETURN SUM(r.rev)"
    results = gdb.query(q)
    return results[0][0]
 
  def p2p_from_npax(self):
    mrkt = self.get_mrkt()
    q = "START n = node(*)\
         MATCH (n)-[r:FROM_TO_DAILY]->(m)\
         WHERE n.code? = '" + mrkt + "' AND\
               m.code? = 'HEL'\
         RETURN SUM(r.num_pax)" 
    results = gdb.query(q)
    return results[0][0]

  def p2p_to_npax(self):
    mrkt = self.get_mrkt()
    q = "START n = node(*)\
         MATCH (n)-[r:FROM_TO_DAILY]->(m)\
         WHERE m.code? = '" + mrkt + "' AND\
               n.code? = 'HEL'\
         RETURN SUM(r.num_pax)"
    results = gdb.query(q)
    return results[0][0]

  def p2p_from_rev(self):
    mrkt = self.get_mrkt()
    q = "START n = node(*)\
         MATCH (n)-[r:FROM_TO_DAILY]->(m)\
         WHERE n.code? = '" + mrkt + "' AND\
               m.code? = 'HEL'\
         RETURN SUM(r.rev)"
    results = gdb.query(q)
    return results[0][0]

  def p2p_to_rev(self):
    mrkt = self.get_mrkt()
    q = "START n = node(*)\
         MATCH (n)-[r:FROM_TO_DAILY]->(m)\
         WHERE m.code? = '" + mrkt + "' AND\
               n.code? = 'HEL'\
         RETURN SUM(r.rev)"
    results = gdb.query(q)
    return results[0][0]

  def adjacent_num(self):
    mrkt = self.get_mrkt()
    if self.dstn == mrkt:
      q = "START n = node(*)\
           MATCH (n)-[r:FROM_TO_DAILY]->(m)\
           WHERE m.code ? = '" + mrkt + "'\
           RETURN COUNT(DISTINCT n.code?)"
    else:
      q = "START n = node(*)\
           MATCH (n)-[r:FROM_TO_DAILY]->(m)\
           WHERE n.code? = '" + mrkt + "'\
           RETURN COUNT(DISTINCT m.code?)"
    results = gdb.query(q)
    return results[0][0]

  def get_db_costs_day(self,dt):
    """Calculates costs related to
       overbooking"""
    # FIXME: add downgrading costs
    fltnums = self.get_fltnums_day(dt)
    sm = 0
    np = 0
    for fltnum in fltnums:
      sm += crmCase.get_dep_db_total_compensation(self.orgn,self.dstn,fltnum,dt)
      np += crmCase.get_dep_db_total_num_pax(self.orgn,self.dstn,fltnum,dt)
    return np,sm

  def get_ob_measures_day(self,dt):
    """Calculated ob measures:
         - Overbooking actual
         - Overbooking allowed
         - Costs (compensation)
         - Gains (average fare)"""
    try:
      au,booked,adjcap = self.get_au_booked_adjcap_day(dt)
      avg_fare = self.get_avg_fare_day(dt)

      ob_actual = max(float(booked-adjcap)/adjcap,0)
      ob_allowed = max(float(au-adjcap)/adjcap,0)
      gain = max(booked-adjcap,0) * avg_fare
      db_num_pax,db_costs = self.get_db_costs_day(dt)
      costs = db_costs + db_num_pax * (avg_fare + float(41))

      return ob_actual,ob_allowed,gain,costs
    except:
      return None,None,None,None

  def _get_avg_fare_day(self,dt):
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT AVG(fare) FROM hleg_class\
         WHERE dptdt = TO_DATE('"+dt.strftime('%Y-%m-%d')+"','yyyy-mm-dd') AND\
               daysprior = '0' AND orgn='"+self.orgn+"' AND dstn='"+self.dstn+"'"
    curs.execute(q)
    row = curs.fetchone()
    return row[0]

  def get_avg_fare_day(self,dt):
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT SUM(booked*fare)/SUM(booked) FROM hleg_class\
         WHERE dptdt = TO_DATE('"+dt.strftime('%Y-%m-%d')+"','yyyy-mm-dd') AND\
               daysprior = '0' AND orgn='"+self.orgn+"' AND dstn='"+self.dstn+"'"
    curs.execute(q)
    row = curs.fetchone()
    return row[0]

  def get_booked_weekly(self,dfrom,dto,clss):
    clss = ["'"+cls+"'" for cls in clss]
    clss_s = ','.join(clss)

    curs = dbConnector.get_prosuser_curs()
    q = "SELECT WN,SUM(booked) FROM\
         (SELECT booked,TO_CHAR(dptdt,'YYYY-WW') AS WN FROM hleg_class\
          WHERE orgn = '"+self.orgn+"' AND dstn = '"+self.dstn+"' AND\
                daysprior = '-1' AND\
                dptdt >= TO_DATE('"+dfrom.strftime('%Y-%m-%d')+"','yyyy-mm-dd') AND\
                dptdt <= TO_DATE('"+dto.strftime('%Y-%m-%d')+"','yyyy-mm-dd') AND\
                clssym IN ("+clss_s+"))\
         GROUP BY WN\
         ORDER BY WN" 
    curs.execute(q)   
    rows = curs.fetchall()
    return rows

  def get_avg_pif(self,cls):
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT AVG(fare) FROM leg_class\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               clssym = '" + cls + "'"
    curs.execute(q)
    row = curs.fetchone()
    return row[0]

  def get_avg_pseudo_fare(self,cls):
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT AVG(pseudofare) FROM leg_class\
         WHERE orgn = '" + self.orgn + "' AND\
               dstn = '" + self.dstn + "' AND\
               clssym = '" + cls + "'"
    curs.execute(q)
    row = curs.fetchone()
    return row[0]

  @staticmethod
  def write_ob_pickle_files(dfrom,dto):
    """Returns dictionary like
        'HEL-BKK': ['2013-01-01': [ob_actual,ob_costs,gain,costs],..."""
    legs = Leg.get_managed_legs()

    for leg in legs:
      if leg.orgn != 'HEL' and leg.dstn != 'HEL':
        continue
      print leg.orgn,'-',leg.dstn
      fname = config.get('PATHS','ob_data')+'/'+leg.orgn+'-'+leg.dstn+'.pkl'
      if os.path.exists(fname):
        continue
      l = Leg(leg.orgn,leg.dstn)
      res = []
      dt = dfrom
      while dt < dto:
        print '\t',dt.strftime('%Y-%m-%d')
        res.append([dt.strftime('%Y-%m-%d'),l.get_ob_measures_day(dt)])
        dt += timedelta(days=1)
      pickle.dump(res,open(fname,'w'))

if __name__ == '__main__':
  dfrom = date(2012,6,25)
  dto = date(2013,6,25)
 
  Leg.write_ob_pickle_files(dfrom,dto) 


