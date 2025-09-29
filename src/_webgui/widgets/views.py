import sys
import os
import ConfigParser

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from django.http import HttpResponse
from django.template import Context, loader
from datetime import date, datetime, timedelta

def consfnldmd_cmpt_ts(request,orgn,dstn,fltnum,cmpt):
    tmpl = loader.get_template('consfnldmd_cmpt_ts_widget.xml')
    cntx = Context({
           "orgn":   orgn,
           "dstn":   dstn,
           "fltnum": fltnum,
           "cmpt":   cmpt,
    })
    return HttpResponse(tmpl.render(cntx))
 
