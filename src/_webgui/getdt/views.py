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

from flight import *
from cls import get_cmpt_clss
import gviz_api

lock = Lock()

def class_mix(request,orgn,dstn,fltnum):
    lock.acquire()
    response = HttpResponse()
    try:
        fl = flight(orgn,dstn,fltnum)
        clss_j = get_cmpt_clss('J')
        clss_y = get_cmpt_clss('Y')
        description = {"date": ("string","Date")}
        for cls_j in clss_j:
            description[cls_j] = ("number",cls_j + " class")
        for cls_y in clss_y:
            description[cls_y] = ("number",cls_y + " class")

        dto = datetime.now()
        ddelta = timedelta(days=35)
        dfrom = dto - ddelta
        
        class_mix_ts = fl.get_booked_cls_mix_ts(dfrom,dto)
        data_table = gviz_api.DataTable(description)
        data_table.LoadData(class_mix_ts)
        response = HttpResponse(mimetype='text/plain')
        columns_order = ["date"]
        for cls_j in clss_j:
            columns_order.append(cls_j)
        for cls_y in clss_y:
            columns_order.append(cls_y)
        response.write(data_table.ToJSonResponse(columns_order=columns_order,order_by="date"))
    except Exception as inst:
        lock.release()
        print type(inst)
        print inst.args
        print inst
    finally:
        lock.release()
        return response




