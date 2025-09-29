import sys
import os
import ConfigParser

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from time import sleep
from django.http import HttpResponse
from django.template import Context, loader
from datetime import date, datetime, timedelta

def demand_shift_form(request):
    return HttpResponse()
