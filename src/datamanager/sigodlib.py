import sys
import csv

from datetime import date
from db_connector import dbConnector

def total_rev(dfrom,dto):
  curs = dbConnector.get_or_curs()
  q = "SELECT SUM(tot_client_net_net_rev) AS rev\
       FROM ra_data\
       WHERE dep_date >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
             dep_date <= DATE('" + dto.strftime('%Y-%m-%d') + "')"
  curs.execute(q)
  row = curs.fetchone()
  return row[0]

def total_npax(dfrom,dto):
  curs = dbConnector.get_or_curs()
  q = "SELECT SUM(pax_cnt)\
       FROM ra_data\
       WHERE dep_date >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
             dep_date <= DATE('" + dto.strftime('%Y-%m-%d') + "')"
  curs.execute(q)
  row = curs.fetchone()
  return row[0]

def rev_in_file(dfrom,dto,fname):
  curs = dbConnector.get_or_curs()
  rev = 0
  try:
    with open(fname,'rb') as csvfile:
      reader = csv.reader(csvfile)
      for line in reader:
        trip_orgn = line[0]
        trip_dstn = line[1]
        online_orgn = line[2]
        online_dstn = line[3]
        q = "SELECT SUM(tot_client_net_net_rev)\
             FROM ra_data\
             WHERE dep_date >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
                   dep_date <= DATE('" + dto.strftime('%Y-%m-%d') + "') AND\
                   trip_orgn = '" + trip_orgn + "' AND\
                   trip_dstn = '" + trip_dstn + "' AND\
                   online_orgn = '" + online_orgn + "' AND\
                   online_dstn = '" + online_dstn + "'"
        curs.execute(q)
        row = curs.fetchone()
        if row[0] is None:
          continue
        else:
          rev += row[0]
  except:
    rev = 0
  return rev     

def npax_in_file(dfrom,dto,fname):
  curs = dbConnector.get_or_curs()
  npax = 0
  try:
    with open(fname,'rb') as csvfile:
      reader = csv.reader(csvfile)
      for line in reader:
        trip_orgn = line[0]
        trip_dstn = line[1]
        online_orgn = line[2]
        online_dstn = line[3]
        q = "SELECT SUM(pax_cnt)\
             FROM ra_data\
             WHERE dep_date >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
                   dep_date <= DATE('" + dto.strftime('%Y-%m-%d') + "') AND\
                   trip_orgn = '" + trip_orgn + "' AND\
                   trip_dstn = '" + trip_dstn + "' AND\
                   online_orgn = '" + online_orgn + "' AND\
                   online_dstn = '" + online_dstn + "'"
        curs.execute(q)
        row = curs.fetchone()
        if row[0] is None:
          continue
        else:
          npax += row[0]
  except:
    pass
  return npax

def sigod_list_rev(dfrom=None,dto=None,limit=None):
  curs = dbConnector.get_or_curs()
  if dfrom is None or dto is None:
    q = "SELECT MIN(dep_date) FROM ra_data"
    curs.execute(q)
    row = curs.fetchone()
    dfrom = row[0]
    dfroms = dfrom.split('-')
    dfrom = date(int(dfroms[0]),int(dfroms[1]),int(dfroms[2]))

    q = "SELECT MAX(dep_date) FROM ra_data"
    curs.execute(q)
    row = curs.fetchone()
    dto = row[0]
    dtos = dto.split('-')
    dto = date(int(dtos[0]),int(dtos[1]),int(dtos[2]))

  if limit is None:
    limit_clause = ''
  else:
    limit_clause = ' LIMIT '+str(limit)

  q = "SELECT trip_orgn,online_orgn,online_dstn,trip_dstn,pos,SUM(tot_client_net_net_rev) AS rev\
       FROM ra_data\
       WHERE dep_date >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
             dep_date <= DATE('" + dto.strftime('%Y-%m-%d') + "')\
       GROUP BY trip_orgn,online_orgn,online_dstn,trip_dstn,pos\
       ORDER BY rev DESC "+limit_clause
  curs.execute(q)

  sm = 0
  num = 0
  res = []
  row = curs.fetchone()
  
  while row is not None:
    trip_orgn = row[0]
    online_orgn = row[1]
    online_dstn = row[2]
    trip_dstn = row[3]
    pos = row[4]
    rev = int(row[5])
    num += 1
    sm += rev
    res.append([num,trip_orgn,online_orgn,online_dstn,trip_dstn,pos,rev,sm])

    row = curs.fetchone()

  return res  

def sigod_list_npax(dfrom=None,dto=None,limit=None):
  curs = dbConnector.get_or_curs()
  if dfrom is None or dto is None:
    q = "SELECT MIN(dep_date) FROM ra_data"
    curs.execute(q)
    row = curs.fetchone()
    dfrom = row[0]
    dfroms = dfrom.split('-')
    dfrom = date(int(dfroms[0]),int(dfroms[1]),int(dfroms[2]))

    q = "SELECT MAX(dep_date) FROM ra_data"
    curs.execute(q)
    row = curs.fetchone()
    dto = row[0]
    dtos = dto.split('-')
    dto = date(int(dtos[0]),int(dtos[1]),int(dtos[2]))

  if limit is None:
    limit_clause = ''
  else:
    limit_clause = ' LIMIT '+str(limit)

  q = "SELECT trip_orgn,online_orgn,online_dstn,trip_dstn,pos,SUM(pax_cnt) AS npax\
       FROM ra_data\
       WHERE dep_date >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
             dep_date <= DATE('" + dto.strftime('%Y-%m-%d') + "')\
       GROUP BY trip_orgn,online_orgn,online_dstn,trip_dstn,pos\
       ORDER BY npax DESC "+limit_clause
  curs.execute(q)

  sm = 0
  num = 0
  res = []
  row = curs.fetchone()

  while row is not None:
    trip_orgn = row[0]
    online_orgn = row[1]
    online_dstn = row[2]
    trip_dstn = row[3]
    pos = row[4]
    npax = int(row[5])
    num += 1
    sm += npax
    res.append([num,trip_orgn,online_orgn,online_dstn,trip_dstn,pos,npax,sm])

    row = curs.fetchone()

  return res

def sigod_lists_diff(sigod_list1,sigod_list2):
  """
  Returns the following values
  
  added to sigod_list2: not presented in sigod_list1, but in sigod_list2
  removed from sigod_list2: presented in sigod_list1, but not in sigod_list2

  list: num,trip_orgn,online_orgn,online_dstn,trip_dstn,rev,cum_rev
  """

  sl1 = [[e[1],e[2],e[3],e[4],e[5]] for e in sigod_list1]
  sl2 = [[e[1],e[2],e[3],e[4],e[5]] for e in sigod_list2]

  diff12 = []
  for e in sl2:
    if e not in sl1:
      diff12.append(e)

  diff21 = []
  for e in sl1:
    if e not in sl2:
      diff21.append(e)

  return diff12,diff21

if __name__ == '__main__':

  dfrom1 = date(2012,5,1)
  dto1 = date(2012,7,1)

  dfrom2 = date(2012,7,1)
  dto2 = date(2012,9,1)

  sigod_list1 = sigod_list_rev(dfrom1,dto1,limit=2400)
  sigod_list2 = sigod_list_rev(dfrom2,dto2,limit=2400)

  added,removed = sigod_lists_diff(sigod_list1,sigod_list2)



 
