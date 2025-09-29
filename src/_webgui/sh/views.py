import sys
import os
import ConfigParser
from datetime import datetime,date,timedelta
import csv
import random
from multiprocessing import Process
from time import time

from django.shortcuts import render_to_response
from django.template import Context, RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','network_analysis'))

from pca import read_first_pc
from features import *

def index(request):
  tmpl = loader.get_template('sh/index.htm')
  cntx = Context({})
  return HttpResponse(tmpl.render(cntx))

def csv_rev(request):
  fname = 'rev_'+str(time())+'.csv'
  data = rev_ts()

  response = HttpResponse(mimetype='text/csv')
  response['Content-Disposition'] = 'attachment; filename='+fname

  writer = csv.writer(response)
  writer.writerow(['Date','Rev'])
  for d in data:
    writer.writerow(d)
  return response

def csv_npax(request):
  fname = 'npax_'+str(time())+'.csv'
  data = npax_ts()
  
  response = HttpResponse(mimetype='text/csv')
  response['Content-Disposition'] = 'attachment; filename='+fname

  writer = csv.writer(response)
  writer.writerow(['Date','Npax'])
  for d in data:
    writer.writerow(d)
  return response 

def csv_yield(request):
  fname = 'yield_'+str(time())+'.csv'
  data = yield_ts()

  response = HttpResponse(mimetype='text/csv')
  response['Content-Disposition'] = 'attachment; filename='+fname
 
  writer = csv.writer(response)
  writer.writerow(['Date','Yield'])
  for d in data:
    writer.writerow(d)
  return response

def csv_nedge(request):
  fname = 'nedge_'+str(time())+'.csv'
  data = nedge_ts()

  response = HttpResponse(mimetype='text/csv')
  response['Content-Disposition'] = 'attachment; filename='+fname

  writer = csv.writer(response)
  writer.writerow(['Date','nedge'])
  for d in data:
    writer.writerow(d)
  return response

def csv_p2p_npax_ratio(request):
  fname = 'p2p_ratio_'+str(time())+'.csv'
  data = p2p_npax_ratio_ts()

  response = HttpResponse(mimetype='text/csv')
  response['Content-Dispositoin'] = 'attachment; filename='+fname

  writer = csv.writer(response)
  writer.writerow(['Date','p2p_ratio'])
  for d in data:
    writer.writerow(d)
  return response

def csv_first_pc(request):
  fname = 'first_pc_'+str(time())+'.csv'
  response = HttpResponse(mimetype='text/csv')
  response['Content-Disposition'] = 'attachment; filename='+fname

  get_dict = dict(request.GET.iterlists())
  try:
    hol = get_dict['hol']
    hol = [str(e) for e in hol if str(e) != '']
    hol1 = hol[::2]
    hol2 = hol[1::2]
    hol = zip(hol1,hol2)
  except:
    hol = []

  try:
    h_r = float(get_dict['h'][0])
  except:
    h_r = None

  try:
    breaks_r = int(get_dict['breaks'][0])
  except:
    breaks_r = None  

  if h_r is not None:
    if breaks_r is not None:
      dts,data = read_first_pc(holidays=hol,h_r=h_r,breaks_r=breaks_r)
    else:
      dts,data = read_first_pc(holidays=hol,h_r=h_r)
  else:
    if breaks_r is not None:
      dts,data = read_first_pc(holidays=hol,breaks_r=breaks_r)
    else:
      dts,data = read_first_pc(holidays=hol)

  orig = data[0]
  lintr = data[1]

  writer = csv.writer(response)
  writer.writerow(['Date','PC','LinTr'])
  i = 0
  for i in range(len(orig)):
    writer.writerow([dts[i],orig[i],lintr[i]])
  return response


