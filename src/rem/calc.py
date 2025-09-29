import sys
import os
import numpy as np
import ConfigParser
from datetime import date,datetime,timedelta
from marketowners import marketowners as mo

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))
sys.path.append(config.get('PATHS','optimizer'))

from flight import Flight
from departure import Departure
from rem import simulate, simulate_const
from emsr import *
from db_connector import dbConnector

def get_rem(dep):
  fs,mus,stds = dep.get_fares_means_stds()
  # Petrubate stds
  stds = [e if e != 0.0 else 0.01 for e in stds]

  cap = dep.get_adjcap('J',daysprior='0') + dep.get_adjcap('Y',daysprior='0')
  rev = dep.get_revenue()
  nruns = 10000

  try:

    # Simulate with random protection limits 
    rrevs,rprots = simulate(fs,mus,stds,cap,nruns)
    srevs = np.array([e[0] for e in rrevs])
    drevs = np.array([e[1] for e in rrevs])
    bp = float(np.mean(srevs))
    bv = float(np.std(srevs))
    mv = bv - float(np.std(drevs))

    # Simulate with EMSRb protection limits
    emsrb_prots = emsrb_prots_cap(fs,mus,stds,cap)
    crevs = simulate_const(fs,mus,stds,cap,emsrb_prots,nruns)
    erev = float(np.mean(crevs))

    return bp,bv,mv,rev,(rev - bp)/bv,erev
  except Exception as e:
    print e
    return None,None,None,None,None,None

if __name__ == '__main__':

  or_curs = dbConnector.get_or_curs()
  or_conn = dbConnector.get_or_conn()

  markets = mo.get_markets()

  for market in markets:
    print market
    flights = Flight.get_managed_flights()
    for orgn,dstn,fltnum in flights:
      orgn = orgn.strip()
      dstn = dstn.strip()
      fltnum = fltnum.strip()
      if orgn != market and dstn != market:
        continue
      dto = datetime.now().date() - timedelta(days=1)
      dfrom = dto - timedelta(days=400)
      dt = dfrom
      while dt <= dto:
        # If generated, skip
        q = "SELECT * FROM rem\
             WHERE orgn = '" + orgn + "' AND\
                   dstn = '" + dstn + "' AND\
                   fltnum = '" + fltnum + "' AND\
                   dptdt = DATE('" + dt.strftime('%Y-%m-%d') + "')"
        or_curs.execute(q)
        rows = or_curs.fetchall()

        if len(rows) != 0:
          print orgn+'-'+dstn+'-'+fltnum+'-'+dt.strftime('%Y-%m-%d')+' already calculated'
          dt = dt + timedelta(days=1)
          continue

        dep = Departure(orgn,dstn,fltnum,dt)

        if not dep.is_departed():
          print orgn+'-'+dstn+'-'+fltnum+'-'+dt.strftime('%Y-%m-%d')+' not departed'
          dt = dt + timedelta(days=1)
          continue

        print datetime.now().strftime('%H:%m:%S'),
        print orgn+'-'+dstn+'-'+fltnum+'-'+dt.strftime('%Y-%m-%d'),
        bp,bv,mv,rev,eff,erev = get_rem(dep)
        print bp,bv,mv,rev,eff,erev
        if bp is not None and bv is not None and mv is not None and rev is not None and eff is not None and erev is not None:
          q = "INSERT INTO rem (orgn,dstn,fltnum,dptdt,bp,bv,mv,rev,eff,erev)\
               VALUES ('"+orgn+"','"+dstn+"','"+fltnum+"','"+dt.strftime('%Y-%m-%d')+\
               "',"+str(bp)+","+str(bv)+","+str(mv)+","+str(rev)+","+str(eff)+","+str(erev)+")"
          or_curs.execute(q)
          or_conn.commit()
        dt = dt + timedelta(days=1)    



