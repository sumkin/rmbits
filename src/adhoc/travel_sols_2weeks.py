"""
This script is written by Fedor Nikitin in order to 
estimate the number of possible flight combinations
for OD.
"""

import os
import sys
import ConfigParser
import csv
import sqlite3
import time
import datetime

from pyairport.airport import Airport

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__), '../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)
sys.path.append(config.get('PATHS', 'datamanager'))
tmpdir = config.get('PATHS', 'tmpdir')

from db_connector import dbConnector
from cls import classes

nrm_curs = dbConnector.get_nrm_curs()


def create_and_fill_table():
  """
  Create sqlite3 table from booking data (NRM) with
  counts of different travel solutions on origin,
  destination, pos and departure level.
  """

  upto = (datetime.datetime.now() + datetime.timedelta(weeks=2)).strftime('%Y-%m-%d')

  # Create table.
  dbname = tmpdir + '/' + 'ts2w_' + str(time.time()) + '.db'
  conn = sqlite3.connect(dbname)
  sql3_curs = conn.cursor()
  sql3_curs.execute('''CREATE TABLE ts2weeks
                       (id INTEGER PRIMARY KEY AUTOINCREMENT,\
                       cnt INTEGER,pax_cnt INTEGER,orig,dstn,pos,dpdt)''')
  conn.commit()

  # Query nrm database. 
  q = "select  count(distinct FK_BASE_TRAVEL_SOLUTIONS) as cnt,\
               sum(seg_pax_count) as pax_cnt,\
               OD_DEPT_AIRPORT,\
               OD_ARR_AIRPORT,\
               POS,\
               OD_DEPT_DATE\
         from NRM.V_F_NRM_BOF_CURRENT\
         where BOOKING_CLASS != 'A' and\
               OD_DEPT_DATE <= TO_DATE('" + upto + "', 'yyyy-mm-dd') and\
               SEG_OPR_AIRLINE = 'AY' AND SEG_MKT_AIRLINE = 'AY'\
         group by OD_DEPT_AIRPORT,\
                  OD_ARR_AIRPORT,\
                  POS,\
                  OD_DEPT_DATE"
  nrm_curs.execute(q)
  print "Query to NRM has been executed."

  for cnt, pax_cnt, orig, dstn, pos, dpdt in nrm_curs:
    sq = "INSERT INTO ts2weeks \
          (cnt, pax_cnt, orig, dstn, pos, dpdt) VALUES\
          ('" + str(cnt) + "',\
           '" + str(pax_cnt) + "',\
           '" + orig + "',\
           '" + dstn + "',\
           '" + pos + "',\
           '" + str(dpdt) + "')"
    print sq
    sql3_curs.execute(sq) 
  conn.commit()

  print dbname, ' db has been populated'


def update_onoff(sql3fname):
  """
  Add onoff INTEGER field to ts2weeks db
  and fills it based on the following
  onoff = 0 if origin is in pos
  onoff = 1 if dstn is in pos
  onoff = 2 default.
  """
  # Create new column.
  conn = sqlite3.connect(sql3fname)
  sql3_curs = conn.cursor()
  #sql3_curs.execute('''ALTER TABLE ts2weeks ADD COLUMN onoff DEFAULT 2''')   
  #conn.commit()

  # Go over entries and update onoff field.
  q = "SELECT id, orig, dstn, pos from ts2weeks"
  sql3_curs.execute(q)

  res = []
  for id_,orig, dstn, pos in sql3_curs:
    res.append([id_,orig,dstn,pos])

  for id_,orig,dstn,pos in res:
    origa = Airport(orig)
    dstna = Airport(dstn)
    if origa.get_country_code() == pos:
      onoff = 0
    elif dstna.get_country_code() == pos:
      onoff = 1
    else:
      onoff = 2
    sq = "UPDATE ts2weeks SET onoff='"+str(onoff)+"' WHERE id=" + str(id_)
    sql3_curs.execute(sq)
  conn.commit()



if __name__ == "__main__":
  update_onoff(tmpdir + '/ts2w_2018-03-13.db') 











