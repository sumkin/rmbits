import os
import sys
import csv
from datetime import datetime, date, timedelta
import sqlite3
import pickle
import ConfigParser

from django.conf import settings
from neo4jrestclient.client import GraphDatabase

from pyairport.airport import Airport
from emailsender.email_sender import EmailSender

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)
sys.path.append(config.get('PATHS','datamanager'))
sys.path.append(config.get('PATHS','network_analysis'))

from features import *
from db_connector import dbConnector

def def_additive(a,b,m):
  # FIXME: broute force solution
  # of equation.
  x = 0
  while True:
    if (a+x) % m == b:
      return x
    x += 1

class Neo4jUpdater():
  def __init__(self,fname=None):
    self.fname = fname

  def sqlite_db_init(self):
    self.conn = sqlite3.connect(':memory:')
    self.curs = self.conn.cursor()

  def store_to_sqlite_db(self):
    # Drop table if exists
    try:
      q = "DROP TABLE data;"
      self.curs.execute(q)
    except:
      pass

    # Create table
    q = "CREATE TABLE data (orgn CHAR(3),dstn CHAR(3),cls CHAR(1),\
                            dt DATE,dow INT,week_num INT,num_pax INT,rev FLOAT);"
    self.curs.execute(q)

    # Fill table
    reader = csv.reader(open(self.fname,'rb'),delimiter=' ')
    dfrom = dto = None

    num_added = 0
    for line in reader:
      # Skip empty lines
      if len(line) == 0:
        continue
      code = line[0].strip()
      if code == 'CRG':
        # First line
        dfrom = line[1]
        dto = line[2]
        dfroms = [dfrom[:4],dfrom[4:6],dfrom[6:8]]
        dtos = [dto[:4],dto[4:6],dto[6:8]]
        dfrom = date(int(dfroms[0]),int(dfroms[1]),int(dfroms[2]))
        dto = date(int(dtos[0]),int(dtos[1]),int(dtos[2]))
      else:
        assert dfrom != None and dto != None
        cls = line[7]
        if line[8] == 'ID':
          rev = float(line[12])
          num_pax = int(line[13])
          orgn = line[15]
          dstn = line[16]
          dow = int(line[22])
        else:
          rev = float(line[11])
          num_pax = int(line[12])
          orgn = line[14]
          dstn = line[15]
          dow = int(line[21])

        dt = dfrom + timedelta(def_additive(int(dfrom.weekday()),int(dow),7))
        week_num = int(dt.isocalendar()[1])

        if dt > dto:
          print [orgn,dstn,dt,dow,week_num,cls,num_pax,rev]
          print [dow,week_num,dfrom,dt,dto]
          print 'WARNING! DISCREPANCY IN RA DATA'
          continue

        q = "INSERT INTO data (orgn,dstn,cls,dt,dow,week_num,num_pax,rev) VALUES\
             ('"+orgn+"','"+dstn+"','"+cls+"',\
              '"+dt.strftime('%Y-%m-%d')+"',"+str(dow)+","+str(week_num)+","+str(num_pax)+","+str(rev)+")"
        self.curs.execute(q)
        num_added += 1
    self.conn.commit()

    return dfrom,dto,num_added

  def add_airports(self):
    gdb = GraphDatabase('http://localhost:7474/db/data/')
    self.airport_ind = gdb.nodes.indexes.create('airport_ind')

    q = "SELECT DISTINCT orgn FROM data"
    self.curs.execute(q)
    rows = self.curs.fetchall()
    orgns = [e[0].strip() for e in rows]

    q = "SELECT DISTINCT dstn FROM data"
    self.curs.execute(q)
    rows = self.curs.fetchall()
    dstns = [e[0].strip() for e in rows]

    airports = list(set(orgns+dstns))    

    num_added = 0    
    for airport in airports:
      ap = Airport(airport)
      try:
        lo = float(ap.get_longitude())
      except:
        lo = 0.0
      try:
        la = float(ap.get_latitude())
      except:
        la = 0.0

      hits = self.airport_ind['code'][airport]
      assert len(hits) < 2  # 0 or 1 entry
      if len(hits) == 0:
        airport_node = gdb.nodes.create(code=airport,longitude=lo,latitude=la)
        self.airport_ind.add('code',airport,airport_node)
        num_added += 1
        print 'Airport ',airport,' added'
      else:
        airport_node = hits[0]
        airport_node['code'] = airport
        airport_node['longitude'] = lo
        airport_node['latitude'] = la
    return num_added

  def update_stoch_matrix_day(self,dt):
    gdb = dbConnector.get_neo4j_conn()
    self.sm_ind = gdb.nodes.indexes.create('sm_ind')

    code_list = get_code_list()
    m = rw_matrix_day(dt,code_list)

    dt_s = dt.strftime('%Y-%m-%d')
    updated_s = datetime.now().date().strftime('%Y-%m-%d')
    m_s = pickle.dumps(m)

    sm_node = gdb.nodes.create(dt=dt_s,updated=updated_s,m=m_s)
    self.sm_ind.add('dt',dt.strftime('%Y-%m-%d'),sm_node)    

  def update_stoch_matrix(self,every=False):
    gdb = dbConnector.get_neo4j_conn()

    min_dt,max_dt = self.get_min_max_dt()

    if every:
      dt = min_dt
      while dt <= max_dt:
        self.update_stoch_matrix_day(dt)
        dt += timedelta(days=1)
        print dt
    else:
      pass  

  def add_from_to_daily(self):
    gdb = GraphDatabase('http://localhost:7474/db/data/')
    self.ftd_ind = gdb.relationships.indexes.create('ftd_ind')

    q = "SELECT orgn,dstn,dt,SUM(num_pax),SUM(rev)\
         FROM data\
         GROUP BY orgn,dstn,dt"
    self.curs.execute(q)
    rows = self.curs.fetchall()

    num_added = 0
    for row in rows:
      orgn = row[0]
      dstn = row[1]
      dt = row[2]
      num_pax = row[3]
      rev = row[4]
      orgn_node = self.airport_ind['code'][orgn][0]
      dstn_node = self.airport_ind['code'][dstn][0]
      rel = orgn_node.FROM_TO_DAILY(dstn_node,dt=dt,num_pax=int(num_pax),rev=float(rev))
      self.ftd_ind.add('code',orgn+'-'+dstn+'-'+dt,rel)
      num_added += 1
      print '\t',orgn,'-',dstn,'-',dt,' added'      
    return num_added

  def add_from_to_weekly(self):
    self.ftw_ind = gdb.relationships.indexes.create('ftw_ind')

    q = "SELECT DISTINCT orgn,dstn,week_num,SUM(num_pax),SUM(rev)\
         FROM data\
         GROUP BY orgn,dstn,week_num"
    self.curs.execute(q)
    rows = self.curs.fetchall()
    for row in rows:
      orgn = row[0]
      dstn = row[1]
      week_num = row[2]
      num_pax = row[3]
      rev = row[4]
      orgn_node = self.airport_ind['code'][orgn][0]
      dstn_node = self.airport_ind['code'][dstn][0]
      rel = orgn_node.FROM_TO_WEEKLY(dstn_node,week_num=week_num,num_pax=int(num_pax),rev=float(rev))
      self.ftw_ind.add('code',orgn+'-'+dstn+'-'+week_num,rel)
      print '\t',orgn,'-',dstn,'-',week_num,' added'

  def add_from_to_monthly(self):
    self.ftm_ind = gdb.relationships.indexes.create('ftm_ind')

    q = "SELECT DISTINCT SUBSTR(dt,0,8) AS mnth\
         FROM data\
         ORDER BY mnth"
    self.curs.execute(q)
    rows = self.curs.fetchall()
    months = [e[0].strip() for e in rows]

    for month in months:
      q = "SELECT orgn,dstn,SUM(num_pax),SUM(rev)\
           FROM data\
           WHERE dt LIKE '"+month+"%'\
           GROUP BY orgn,dstn"
      self.curs.execute(q)
      rows = self.curs.fetchall()
      for row in rows:
        orgn = row[0]
        dstn = row[1]
        num_pax = row[2]
        rev = row[3]
        orgn_node = self.airport_ind['code'][orgn][0]
        dstn_node = self.airport_ind['code'][dstn][0]
        rel = orgn_node.FROM_TO_MONTHLY(dstn_node,month=month,weight=int(num_pax),num_pax=int(num_pax),rev=float(rev))
        self.ftm_ind.add('code',orgn+'-'+dstn+'-'+month,rel)
        print '\t',orgn,'-',dstn,'-',month,' added'

  def add_from_to_yearly(self):
    self.fty_ind = gdb.relationships.indexes.create('fty_ind')

    q = "SELECT DISTINCT SUBSTR(dt,0,5) AS year\
         FROM data\
         ORDER BY year"
    self.curs.execute(q)
    rows = self.curs.fetchall()
    years = [e[0].strip() for e in rows]

    for year in years:
      q = "SELECT orgn,dstn,SUM(num_pax),SUM(rev)\
           FROM data\
           WHERE dt LIKE '"+year+"%'\
           GROUP BY orgn,dstn"
      self.curs.execute(q)
      rows = self.curs.fetchall()
      for row in rows:
        orgn = row[0]
        dstn = row[1]
        num_pax = row[2]
        rev = row[3]
        orgn_node = self.airport_ind['code'][orgn][0]
        dstn_node = self.airport_ind['code'][dstn][0]
        rel = orgn_node.FROM_TO_MONTHLY(dstn_node,year=year,weight=int(num_pax),num_pax=int(num_pax),rev=float(rev))
        self.fty_ind.add('code',orgn+'-'+dstn+'-'+year,rel)
        print '\t',orgn,'-',dstn,'-',year,' added'

  def check_missing_daily(self):
    # Check that there are data for every date.
    gdb = GraphDatabase('http://localhost:7474/db/data/')

    min_dt,max_dt = self.get_min_max_dt()

    # Check that on every date there were travellers
    cur_dt = min_dt
    while cur_dt <= max_dt:
      q = "START n=node(*)\
           MATCH (n)-[r:FROM_TO_DAILY]->(m)\
           WHERE r.dt = '"+cur_dt.strftime('%Y-%m-%d')+"'\
           RETURN COUNT(r.dt)"
      result = gdb.query(q)
      num = result[0][0]
      if num == 0:
        print 'WARNING: no edges '+cur_dt.strftime('%Y-%m-%d')
      cur_dt = cur_dt + timedelta(days=1)

  def check_and_delete_duplicates_daily(self):
    gdb = GraphDatabase('http://localhost:7474/db/data/')

    min_dt,max_dt = self.get_min_max_dt()
    cur_dt = min_dt
    while cur_dt <= max_dt:
      q = "START n=node(*)\
           MATCH (n)-[r:FROM_TO_DAILY]->(m)\
           WHERE r.dt = '" + cur_dt.strftime('%Y-%m-%d') + "'\
           RETURN n.code?,m.code?,r.dt?,r.rev?,r.num_pax?,ID(r)\
           ORDER BY n.code?,m.code?"
      result = gdb.query(q)
      prev_row = None
      print cur_dt
      for row in result:
        # orgn,dstn,dt,rev,num_pax,id
        if prev_row is not None:
          if row[0] == prev_row[0] and\
             row[1] == prev_row[1] and\
             row[2] == prev_row[2]:
            if row[:5] == prev_row[:5]:
              gdb.relationships[prev_row[5]].delete()
              print '\t',prev_row[5],'deleted'
            else:
              print '\t','ERROR! Rows have different values.'
        prev_row = row
      cur_dt = cur_dt + timedelta(days=1)

  def update_relationships_from_or_data(self,dt=None):
    gdb = GraphDatabase('http://localhost:7474/db/data/')

    curs = dbConnector.get_or_curs()
    conn = dbConnector.get_or_conn()

    min_dt,max_dt = self.get_min_max_dt()
    cur_dt = min_dt

    if dt is not None:
      cur_dt = dt

    while cur_dt <= max_dt:
      print cur_dt
      q = "SELECT online_orgn,online_dstn,SUM(pax_cnt),SUM(tot_client_net_net_rev)\
           FROM ra_data\
           WHERE dep_date = '" + cur_dt.strftime('%Y-%m-%d') + "'\
           GROUP BY online_orgn,online_dstn"
      curs.execute(q)

      row = curs.fetchone()
      while row is not None:
        online_orgn = row[0]
        online_dstn = row[1]
        num_pax = row[2]
        rev = row[3]

        gq = "START n=node(*)\
              MATCH (n)-[r:FROM_TO_DAILY]->(m)\
              WHERE n.code? = '" + online_orgn + "' AND\
                    m.code? = '" + online_dstn + "' AND\
                    r.dt? = '" + cur_dt.strftime('%Y-%m-%d') + "'\
              RETURN ID(r)"
        result = gdb.query(gq)
        
        try:
          idd = result[0][0]
          gq = "START n=node(*)\
                MATCH (n)-[r:FROM_TO_DAILY]->(m)\
                SET r.rev = " + str(rev) + "\
                WHERE ID(r) = " + str(idd) + "\
                RETURN ID(r)"
          result = gdb.query(gq)
        except:
          pass

        row = curs.fetchone()
      cur_dt = cur_dt + timedelta(days=1)

  def get_min_max_dt(self):
    gdb = GraphDatabase('http://localhost:7474/db/data/')

    # Get minimum and maximum dates
    q = "START n=node(*)\
         MATCH (n)-[r:FROM_TO_DAILY]->(m)\
         RETURN MIN(r.dt)"
    result = gdb.query(q)
    min_dt_s = result[0][0]

    q = "START n=node(*)\
         MATCH (n)-[r:FROM_TO_DAILY]->(m)\
         RETURN MAX(r.dt)"
    result = gdb.query(q)
    max_dt_s = result[0][0]

    min_y,min_m,min_d = [int(e) for e in min_dt_s.split('-')]
    min_dt = date(min_y,min_m,min_d)

    max_y,max_m,max_d = [int(e) for e in max_dt_s.split('-')]
    max_dt = date(max_y,max_m,max_d)

    return min_dt,max_dt

  def update(self):
    fname = settings.MEDIA_ROOT + self.fname
    self.sqlite_db_init()
    dfrom,dto,num_added = self.store_to_sqlite_db()
    num_ap_added = self.add_airports()
    num_ftd_added = self.add_from_to_daily()

    fnames = fname.split('/')

    # Send email
    es = EmailSender('157.200.13.44',25)
    sbj = 'Revenue accounting file has been uploaded.'
    txt  = 'File '+fnames[len(fnames)-1]+' has been uploaded.\r\n\r\n'
    txt += 'Revenue accouting data date range: '+dfrom.strftime('%Y-%m-%d')+'-'+dto.strftime('%Y-%m-%d')+'\r\n'
    txt += 'Number of entries in file: ' + str(num_added) + '\r\n'
    txt += 'Number of nodes added: ' + str(num_ap_added) + '\r\n'
    txt += 'Number of relationships added: ' + str(num_ftd_added) + '\r\n\r\n'
    es.send_quick('fedor.nikitin@finnair.com','fedor.nikitin@finnair.com',sbj,txt)

if __name__ == '__main__':
  nu = Neo4jUpdater()
  nu.update_stoch_matrix(every=True)



