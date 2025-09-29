from django.shortcuts import render_to_response
from django.template import Context, RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect

from neo4jrestclient.client import GraphDatabase

import os
import sys
import json
from datetime import date

import ConfigParser

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)
sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector

def index(request):
  tmpl = loader.get_template('sigod/index.htm')
  cntx = Context({})
  return HttpResponse(tmpl.render(cntx))

def json_revenue(request,dfrom,dto):
  curs = dbConnector.get_or_curs()

  # Define time range
  if dfrom == None or dto == None:
    q = "SELECT MIN(dep_date) FROM ra_data"
    curs.execute(q)
    row = curs.fetchone()
    dfrom = row[0]

    q = "SELECT MAX(dep_date) FROM ra_data"
    curs.execute(q)
    row = curs.fetchone()
    dto = row[0]
  
  dfroms = dfrom.split('-')
  dtos = dto.split('-')

  dfrom = date(int(dfroms[0]),int(dfroms[1]),int(dfroms[2]))
  dto = date(int(dtos[0]),int(dtos[1]),int(dtos[2]))

  # Get data
  q = "SELECT trip_orgn,online_orgn,online_dstn,trip_dstn,SUM(tot_client_net_net_rev) AS rev\
       FROM ra_data\
       WHERE dep_date >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
             dep_date <= DATE('" + dto.strftime('%Y-%m-%d') + "')\
       GROUP BY trip_orgn,online_orgn,online_dstn,trip_dstn\
       ORDER BY rev DESC LIMIT 2400"
  curs.execute(q)
  sigod_list = []
  row = curs.fetchone()
  while row is not None:
    e = {}
    e['trip_orgn'] = row[0]
    e['online_orgn'] = row[1]
    e['online_dstn'] = row[2]
    e['trip_dstn'] = row[3]
    e['rev'] = int(row[4])
    sigod_list.append(e)
    row = curs.fetchone()
  return HttpResponse(json.dumps(sigod_list))

def json_num_pax(request):
  return HttpResponse(json.dumps([]))

def json_mindt(request):
  curs = dbConnector.get_or_curs()
  q = "SELECT MIN(dep_date) FROM ra_data"
  curs.execute(q)
  row = curs.fetchone()
  return HttpResponse(json.dumps(row[0]))

def json_maxdt(request):
  curs = dbConnector.get_or_curs()
  q = "SELECT MAX(dep_date) FROM ra_data"
  curs.execute(q)
  row = curs.fetchone()
  return HttpResponse(json.dumps(row[0]))



