import sys
import csv
import os
import ConfigParser
from datetime import datetime,date,time,timedelta
import time

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from django.shortcuts import render_to_response
from django.template import Context, RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect

import json

from flight import Flight
from db_connector import dbConnector

def index(request):
  curs = dbConnector.get_or_curs()
  q = "SELECT DISTINCT orgn,dstn FROM rem ORDER BY orgn,dstn"
  curs.execute(q)
  rows = curs.fetchall()
  legs = [e[0].strip()+'-'+e[1].strip() for e in rows]

  tmpl = loader.get_template('eff/index.htm')
  cntx = Context({'legs': legs})
  return HttpResponse(tmpl.render(cntx))

def json_flights(request):
  flights = Flight.get_flights()
  res = flights
  return HttpResponse(json.dumps(res))

def json_dates(request):
  dto = datetime.now().date()
  dto = dto - timedelta(days=1)
  dfrom = dto - timedelta(days=50)
  res = []
  dt = dfrom
  while dt <= dto:
    res.append(dt.strftime('%Y-%m-%d'))
    dt += timedelta(days=1)
  return HttpResponse(json.dumps(res))

def csv_ab_rev(request,leg='ALL'):
  fname = 'ab_rev_'+leg+'_'+str(time.time())+'.csv'
  response = HttpResponse(mimetype='text/csv')
  response['Content-Disposition'] = 'attachment; filename='+fname

  curs = dbConnector.get_or_curs()
  if leg == 'ALL':
    q = "SELECT dptdt,AVG(bp),AVG(rev) FROM rem\
         GROUP BY dptdt\
         ORDER BY dptdt"
  else:
    orgn,dstn = leg.split('-')
    q = "SELECT dptdt,AVG(bp),AVG(rev) FROM rem\
         WHERE orgn = '" + orgn + "' AND\
               dstn = '" + dstn + "'\
         GROUP BY dptdt\
         ORDER BY dptdt"
  curs.execute(q)
  rows = curs.fetchall() 

  writer = csv.writer(response)
  writer.writerow(['Date','BlRev','ActRev'])

  for row in rows:
    writer.writerow([row[0].strftime('%Y-%m-%d'),row[1],row[2]])

  return response
  
 
def csv_eff(request,leg='ALL'):
  fname = 'eff_'+leg+'_'+str(time.time())+'.csv'
  response = HttpResponse(mimetype='text/csv')
  response['Content-Disposition'] = 'attachment; filename='+fname

  curs = dbConnector.get_or_curs()
  if leg == 'ALL':
    q = "SELECT dptdt,AVG(eff) FROM rem\
         GROUP BY dptdt\
         ORDER BY dptdt"
  else:
    orgn,dstn = leg.split('-')
    q = "SELECT dptdt,AVG(eff) FROM rem\
         WHERE orgn = '" + orgn.strip() + "' AND\
               dstn = '" + dstn.strip() + "'\
         GROUP BY dptdt\
         ORDER BY dptdt"
  curs.execute(q)
  rows = curs.fetchall()

  writer = csv.writer(response)
  writer.writerow(['Date','Eff'])

  for row in rows:
    writer.writerow([row[0],row[1]])

  return response


def csv_mv(request,leg='ALL'):
  fname = 'mv_'+leg+'_'+str(time.time())+'.csv'
  response = HttpResponse(mimetype='text/csv')
  response['Content-Disposition'] = 'attachment; filename='+fname

  curs = dbConnector.get_or_curs() 
  if leg == 'ALL':
    q = "SELECT dptdt,AVG(mv) FROM rem\
         GROUP BY dptdt\
         ORDER BY dptdt"
  else:
    orgn,dstn = leg.split('-')
    q = "SELECT dptdt,AVG(mv) FROM rem\
         WHERE orgn = '" + orgn.strip() + "' AND\
               dstn = '" + dstn.strip() + "'\
         GROUP BY dptdt\
         ORDER BY dptdt"
  curs.execute(q)
  rows = curs.fetchall()

  writer = csv.writer(response)
  writer.writerow(['Date','MrktVol'])

  for row in rows:
    writer.writerow([row[0],row[1]])

  return response


 
