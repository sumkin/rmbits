import sys
import os
import ConfigParser

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

import json
from django.http import HttpResponse
from django.template import Context, loader

from market import Market

def fa_markets(request):

    ret = Market.get_fa_markets()
    return HttpResponse(json.dumps(ret))
