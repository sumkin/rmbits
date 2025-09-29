import sys
import os
import ConfigParser
import csv
from threading import Lock
from copy import copy

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from django.http import HttpResponse
from django.template import Context, loader
from datetime import date, datetime, timedelta

from flight import Flight
from cls import get_clss
import gviz_api

lock = Lock()

def book(request,orgn,dstn,fltnum):
    lock.acquire()
    try:
        fl = Flight(orgn,dstn,fltnum)
        booked_ts = fl.get_booked_ts()
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=booked_'+orgn+'_'+dstn+'_'+fltnum+'.csv'
        writer = csv.writer(response)
        writer.writerow(['Date','Booked'])
        for e in booked_ts:
            writer.writerow([e[0],e[1]])
    finally:
        resp = copy(response)
        lock.release()
        return resp

def book_yield(request,orgn,dstn,fltnum,cmpt=None,cls=None,dow=None):
    lock.acquire()
    try:
        fl = Flight(orgn,dstn,fltnum)
        dfrom = datetime(2012,5,1)
        dto = datetime(2012,6,1)
        by_ts = fl.get_booked_yield_ts(dfrom=dfrom,dto=dto,cmpt=cmpt,cls=None,dow=dow)
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=booked_yield_'+orgn+'_'+dstn+'_'+fltnum+'_'+dow+'.csv'
        writer = csv.writer(response,delimiter=';')
        writer.writerow(['Booked','Yield'])
        for e in by_ts:
            writer.writerow([e[0],e[1]])
    finally:
        lock.release()
        return response

def book_past(request,orgn,dstn,fltnum,cmpt,cls,dow=None):
    if dow is not None and dow.strip() == '':
        dow = None
    lock.acquire()
    try:
        fl = Flight(orgn,dstn,fltnum)
        booked_ts = fl.get_booked_ts(dfrom = datetime.now() - timedelta(days=700),
                                     dto = datetime.now(),
                                     cmpt=cmpt,
                                     cls=cls,
                                     dow=dow)
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=booked_past_'+orgn+'_'+dstn+'_'+fltnum+'.csv'

        writer = csv.writer(response)
        writer.writerow(['Date','Booked'])
        for e in booked_ts:
            writer.writerow([e[0],e[1]])
    finally:
        lock.release()
        return response

# that is forecast for booked figures
def book_future(requestn,orgn,dstn,fltnum,cmpt,cls,dow=None):
    if dow is not None and dow.strip() == '':
        dow = None
    lock.acquire()
    response = HttpResponse()
    try:
        fl = Flight(orgn,dstn,fltnum)
        booked_ts = fl.get_forecast_booked_ts(dfrom = datetime.now(),
                                              dto = datetime.now() + timedelta(days=300),
                                              cmpt=cmpt,
                                              cls=cls,
                                              dow=dow)
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=booked_future_'+orgn+'_'+dstn+'_'+fltnum+'.csv'
        writer = csv.writer(response)
        writer.writerow(['Date','Frcst fnl booked','Frcst ach booked','Curr booked'])
        for e in booked_ts:
            writer.writerow([e[0],e[1],e[2],e[3]])
    except:
        print 'Unexpected error', sys.exc_info()[0]
    finally:
        resp = copy(response)
        lock.release()
        return resp

def book_cmpt(request,orgn,dstn,fltnum,cmpt):
    lock.acquire()
    try:
        fl = Flight(orgn,dstn,fltnum)
        booked_ts = fl.get_booked_cmpt_ts(cmpt)
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=booked_'+orgn+'_'+dstn+'_'+fltnum+'_'+cmpt+'.csv'
        writer = csv.writer(response)
        writer.writerow(['Date','Adj cap','Booked'])
        for e in booked_ts:
            writer.writerow([e[0],e[1],e[2]])
    finally:
        resp = copy(response)
        lock.release()
        return resp

def rev(request,orgn,dstn,fltnum):
    lock.acquire()
    try:
        fl = Flight(orgn,dstn,fltnum)
        rev_ts = fl.get_rev_ts(dfrom = datetime.now() - timedelta(days=700),
                               dto = datetime.now())
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=rev_'+orgn+'_'+dstn+'_'+fltnum+'.csv'
        writer = csv.writer(response)
        writer.writerow(['Date','Revenue','Costs'])
        for e in rev_ts:
            writer.writerow([e[0],e[1],e[2]])
    finally:
        resp = copy(response)
        lock.release()
        return resp

def yield_(request,orgn,dstn,fltnum):
    lock.acquire()
    try:
        fl = Flight(orgn,dstn,fltnum)
        yield_ts = fl.get_yield_ts(dfrom = datetime.now() - timedelta(days=700),
                                   dto = datetime.now())
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=yield_'+orgn+'_'+dstn+'_'+fltnum+'.csv'
        writer = csv.writer(response)
        writer.writerow(['Date','Yield'])
        for e in yield_ts:
            writer.writerow([e[0],e[1]])
    finally:
        resp = copy(response)
        lock.release()
        return resp

def rev_future(request,orgn,dstn,fltnum):
    lock.acquire()
    try:
        fl = Flight(orgn,dstn,fltnum)
        rev_ts = fl.get_rev_future_ts(dfrom = datetime.now(),
                                      dto = datetime.now() + timedelta(days=300))
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=rev_future_'+orgn+'_'+dstn+'_'+fltnum+'.csv'
        writer = csv.writer(response)
        writer.writerow(['Date','Revenue','Frcst revenue','Costs'])
        for e in rev_ts:
            writer.writerow([e[0],e[1],e[2],e[3]])
    finally:
        resp = copy(response)
        lock.release()
        return resp

def yield_future(request,orgn,dstn,fltnum):
    lock.acquire()
    try:
        fl = Flight(orgn,dstn,fltnum)
        yield_ts = fl.get_yield_future_ts(dfrom = datetime.now(),
                                          dto = datetime.now() + timedelta(days=300))
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=yield_future_'+orgn+'_'+dstn+'_'+fltnum+'.csv'
        writer = csv.writer(response)
        writer.writerow(['Date','Yield','Fcst yield'])
        for e in yield_ts:
            writer.writerow([e[0],e[1],e[2]])
    finally:
        resp = copy(response)
        lock.release()
        return resp

def rev_cmpt(request,orgn,dstn,fltnum,cmpt):
    lock.acquire()
    try:
        fl = Flight(orgn,dstn,fltnum)
        rev_cmpt_ts = fl.get_rev_cmpt_ts(cmpt)
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=rev_'+orgn+'_'+dstn+'_'+fltnum+'_'+cmpt+'.csv'
        writer = csv.writer(response)
        writer.writerow(['Date','Revenue'])
        for e in rev_cmpt_ts:
            writer.writerow([e[0],e[1]])
    finally:
        resp = copy(response)
        lock.release()
        return resp

def class_mix(request,orgn,dstn,fltnum):
    lock.acquire()
    try:
        fl = Flight(orgn,dstn,fltnum)
        class_mix_ts = fl.get_booked_cls_mix_ts()
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=class_mix_'+orgn+'_'+dstn+'_'+fltnum+'.csv'
        writer = csv.writer(response)
        clss = get_clss()
        first_row = ['Date']
        for cls in clss:
            first_row.append(cls)
        writer.writerow(first_row)
        for row in class_mix_ts:
            csv_row = []
            for e in row:
                csv_row.append(e)
            writer.writerow(csv_row)
    finally: 
        lock.release()
        return response


