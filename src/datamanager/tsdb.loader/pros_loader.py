import os
import sys
import time
from datetime import date,datetime,timedelta
import ConfigParser

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector
from tsdb_pusher import TSDBPusher

def update_pros_metrics(days_taken_back=1):
  """Update PROS metrics.
     Tags:
       orgn,dstn,fltnum,dptdt,
       cmpt,cls,taken."""

  taken = datetime.now().strftime('%Y-%m-%d')
  pusher = TSDBPusher()

  dfrom = (datetime.now()-timedelta(days=days_taken_back)).date()
  dto = (datetime.now()-timedelta(days=1)).date()

  curs = dbConnector.get_prosuser_curs()
  q = "SELECT consfnldmd,achfnldmd,\
              orgn,dstn,fltnum,dptdt,cmpsym,clssym,last_upd\
       FROM leg_class ORDER BY last_upd DESC"
  curs.execute(q)

  row = curs.fetchone()
  while row is not None:
    consfnldmd = row[0]
    achfnldmd = row[1]
    orgn = row[2]
    dstn = row[3]
    fltnum = row[4]
    dptdt = row[5]
    cmpt = row[6]
    cls = row[7]
    last_upd = row[8].date()
    taken = last_upd

    print dfrom,last_upd,dto

    if last_upd > dto:
      row = curs.fetchone()
      print last_upd,dfrom,dto,' skip'
      continue

    if last_upd < dfrom:
      print 'Done'
      break

    taken = last_upd.strftime('%Y-%m-%d')
    tags = {'orgn': orgn, 'dstn': dstn, 'fltnum': fltnum,
            'dptdt': dptdt.strftime('%Y-%m-%d'), 'cmpt': cmpt,
            'cls': cls, 'taken': taken}

    timestamp = time.mktime(dptdt.timetuple())    
    timestamp = int(timestamp)

    # FIXME: replace <timestamp> and <value>
    pusher.push('pros.forecast.consfnldmd',timestamp,consfnldmd,tags)
    pusher.push('pros.forecast.achfnldmd',timestamp,achfnldmd,tags)
    row = curs.fetchone()

def update_pros_forecast_error(days_taken_back=1):
  """
  Update PROS metrics for forecast error.
     Tags: orgn,dstn,route,fltnum,dptdt,cmpt,cls,taken.
     
     route = 'BKK' means both legs 'HEL-BKK', 'BKK-HEL'.
  """
  taken = datetime.now().strftime('%Y-%m-%d')
  pusher = TSDBPusher()

    


def update_metrics(days_taken_back=1):
  """Updates all the metrics taken  
     <days_taken_back> days back.
     Tags:
       orgn,dstn,fltnum,dptdt,
       cmpt,cls,taken"""

  update_pros_metrics(days_taken_back)

if __name__ == '__main__':
  update_metrics(days_taken_back=5)


