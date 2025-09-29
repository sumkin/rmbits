import os
import re
import sys
import csv
from datetime import datetime, date, timedelta
import shlex
import ConfigParser
import sqlite3

from django.conf import settings

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)
sys.path.append(config.get('PATHS','datamanager'))

from pyairport.airport import Airport
from emailsender.email_sender import EmailSender
from dt_func import date_str_to_date
from db_connector import dbConnector

def get_modulo_diff(dfrom_dow,dow):
  for diff in range(7):
    if (dfrom_dow + diff)%7 == dow:
      return diff

def def_additive(a,b,m):
  # FIXME: broute force solution
  # of equation.
  x = 0
  while True:
    if (a+x) % m == b:
      return x
    x += 1

class OrDataUpdater():

  def __init__(self,fname):
    self.fname = fname

  def save_to_db(self):
    curs = dbConnector.get_or_curs()
    conn = dbConnector.get_or_conn()

    dfrom_s,dto_s = re.findall('\d{8}',self.fname)
    self.dfrom = date_str_to_date(dfrom_s.strip())
    self.dto = date_str_to_date(dto_s.strip())

    csv_reader = csv.reader(open(self.fname,'rb'))
    i = 0
    for row in csv_reader:
      if len(row) == 0:
        continue
      els = shlex.split(row[0])

      i += 1

      if len(els) != 23:
        print i
        continue

      code = els[0]
      trip_orgn = els[1]
      trip_dstn = els[2]
      cls = els[3]
      poc = els[4]
      pos = els[5]
      in_out = els[6]
      fare_basis_group = els[7]
      fare_basis_code = els[8]
      market_fare_ind = els[9]
      total_fare = els[10]
      total_net_net_fare = els[11]
      pax_cnt = els[12]
      cur_code = els[13]
      online_orgn = els[14]
      online_dstn = els[15]
      tot_client_rev = els[16]
      tot_client_net_net_rev = els[17]
      oac = els[18]
      flag = els[19]
      path = els[20]
      dow = els[21]
      dep_time = els[22]
      dep_date = 'YYYY-MM-DD'

      dfrom_dow = date.weekday(self.dfrom)
      dto_dow = date.weekday(self.dto)

      dep_date = self.dfrom + timedelta(days=get_modulo_diff(dfrom_dow,int(dow)))

      q = "INSERT INTO ra_data\
           (code,trip_orgn,trip_dstn,cls,poc,pos,in_out,\
            fare_basis_group,fare_basis_code,market_fare_ind,\
            total_fare,total_net_net_fare,pax_cnt,cur_code,\
            online_orgn,online_dstn,tot_client_rev,\
            tot_client_net_net_rev,oac,flag,path,dow,dep_time,\
            dep_date) VALUES (\
            '" + code + "',\
            '" + trip_orgn + "',\
            '" + trip_dstn + "',\
            '" + cls + "',\
            '" + poc + "',\
            '" + pos + "',\
            '" + in_out + "',\
            '" + fare_basis_group + "',\
            '" + fare_basis_code + "',\
            '" + market_fare_ind + "',\
             " + total_fare + ",\
             " + total_net_net_fare + ",\
             " + pax_cnt + ",\
            '" + cur_code + "',\
            '" + online_orgn + "',\
            '" + online_dstn + "',\
             " + tot_client_rev + ",\
             " + tot_client_net_net_rev + ",\
            '" + oac + "',\
            '" + flag + "',\
            '" + path + "',\
            '" + dow + "',\
            '" + dep_time + "',\
            '" + dep_date.strftime('%Y-%m-%d') + "')"

      curs.execute(q)

    conn.commit()
    return i

  def get_min_max_dt(self):
    curs = dbConnector.get_or_curs()
    conn = dbConnector.get_or_conn()

    q = "SELECT MIN(dep_date) FROM ra_data"
    curs.execute(q)
    row = curs.fetchone()
    min_dt_s = row[0]

    q = "SELECT MAX(dep_date) FROM ra_data"
    curs.execute(q)
    row = curs.fetchone()
    max_dt_s = row[0]

    min_y,min_m,min_d = [int(e) for e in min_dt_s.split('-')]
    min_dt = date(min_y,min_m,min_d)

    max_y,max_m,max_d = [int(e) for e in max_dt_s.split('-')]
    max_dt = date(max_y,max_m,max_d)

    return min_dt,max_dt

  def check_missing_daily(self):
    curs = dbConnector.get_or_curs()
    conn = dbConnector.get_or_conn()

    min_dt,max_dt = self.get_min_max_dt()
    cur_dt = min_dt
    while cur_dt <= max_dt:
      print cur_dt
      q = "SELECT COUNT(*) FROM ra_data\
           WHERE dep_date = '"+cur_dt.strftime('%Y-%m-%d')+"'"
      curs.execute(q)
      row = curs.fetchone()
      if int(row[0]) == 0:
        print 'ERROR: no data for '+cur_dt.strftime('%Y-%m-%d')
      cur_dt = cur_dt + timedelta(days=1)

  def check_and_delete_duplicates_daily(self):
    curs = dbConnector.get_or_curs()
    conn = dbConnector.get_or_conn()

    min_dt,max_dt = self.get_min_max_dt()
    cur_dt = min_dt
    while cur_dt <= max_dt:
      q = "SELECT id,cls,code,cur_code,dep_date,dep_time,\
                  dow,fare_basis_code,fare_basis_group,flag,\
                  flight_nums,in_out,market_fare_ind,oac,\
                  online_dstn,online_orgn,path,pax_cnt,poc,\
                  pos,tot_client_net_net_rev,tot_client_rev,\
                  total_fare,total_net_net_fare,trip_dstn,trip_orgn\
           FROM ra_data\
           WHERE dep_date = '" + cur_dt.strftime('%Y-%m-%d') + "'\
           ORDER BY cls,code,cur_code,dep_date,dep_time,\
             dow,fare_basis_code,fare_basis_group,flag,\
             flight_nums,in_out,market_fare_ind,oac,\
             online_dstn,online_orgn,path,pax_cnt,poc,\
             pos,tot_client_net_net_rev,tot_client_rev,\
             total_fare,total_net_net_fare,trip_dstn,trip_orgn"
      curs.execute(q)
      row = curs.fetchone()
      prev_row = None
      to_delete = []
      while row is not None:
        if prev_row is not None:
          if row[1:] == prev_row[1:]:
            to_delete.append(prev_row[0])
        prev_row = row
        row = curs.fetchone()

      print cur_dt,':',to_delete
      for e in to_delete:
        q = "DELETE FROM ra_data WHERE id = "+str(e)+";"
        curs.execute(q)
      conn.commit()  

      cur_dt = cur_dt + timedelta(days=1)

  def update(self):
    #self.fname = settings.MEDIA_ROOT + self.fname
    num_added = self.save_to_db()
    

    # Send email
    es = EmailSender('157.200.13.44',25)
    sbj = 'Revenue accounting file has been uploaded to or_data database'
    txt = 'Revenue accouting data date range: '+self.dfrom.strftime('%Y-%m-%d')+'-'+self.dto.strftime('%Y-%m-%d')+'\r\n'
    txt += 'Number of endries added: ' + str(num_added) + '\r\n\r\n'
    es.send_quick('fedor.nikitin@finnair.com','fedor.nikitin@finnair.com',sbj,txt)

if __name__ == '__main__':
  odu = OrDataUpdater('./20110101-20110108.txt')
  odu.update()


