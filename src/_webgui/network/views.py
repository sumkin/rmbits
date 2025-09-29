from django.shortcuts import render_to_response
from django.template import Context, RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect

from neo4jrestclient.client import GraphDatabase

import json

def index(request):
  tmpl = loader.get_template('network/index.htm')
  cntx = Context({})
  return HttpResponse(tmpl.render(cntx))

def json_airports(request):
  gdb = GraphDatabase('http://localhost:7474/db/data/')
  q = "START n=node(*)\
       RETURN DISTINCT n.code?,n.longitude?,n.latitude?"
  result = gdb.query(q)

  airports = []
  for e in result:
    airport = {}
    if e[0] is None:
      continue
    airport['code'] = e[0].strip()
    airport['longitude'] = e[1]
    airport['latitude'] = e[2]
    airports.append(airport)
  return HttpResponse(json.dumps(airports))
