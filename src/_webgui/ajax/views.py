import sys
import os
import ConfigParser

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','ofc_library'))
sys.path.append(config.get('PATHS','datamanager'))
sys.path.append(config.get('PATHS','analyzer'))

import json

from django.http import HttpResponse
from django.template import Context, loader
from datetime import date, datetime, timedelta

from db_connector import dbConnector

gdb = dbConnector.get_neo4j_conn()

def place(request):
  term = request.GET['term']
  places = airport.get_places(term)
  return HttpResponse(json.dumps(places))

def legs(request):
  ans = []
  q = "START n=node(*)\
       MATCH (n)-[r:FROM_TO_DAILY]->(m)\
       WHERE n.code? = 'HEL' OR m.code? = 'HEL'\
       RETURN DISTINCT n.code?+'-'+m.code? AS leg\
       ORDER BY leg"
  results = gdb.query(q)
  ans = [result[0] for result in results]
  return HttpResponse(json.dumps(ans))
 
 
