import sys
import os
import ConfigParser

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from time import sleep
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import Context, RequestContext, loader
from datetime import date, datetime, timedelta

from od import *
from competition_form import *

def stats(request,hop1,hop2,hop3,cls=None):
    dto = datetime.now()
    delta = timedelta(days=365)
    dfrom = dto - delta
    print hop1, hop2, hop3, cls
    print dfrom, dto
    #od = OD([hop1,hop2,hop3],dfrom,dto)
    #stay_length_stats = od.get_stay_length_stats()
    stay_length_stats = [1,2,3]

    tmpl = loader.get_template('od_stats.htm')
    cntx = Context({
           'dfrom': '2011-01-01',
           'dto': '2012-01-01',
    })
    return HttpResponse(tmpl.render(cntx))

'''
def competition(request):
    if request.method == 'POST':
        form = CompetitionForm(request.POST)
        if form.is_valid():

            airlines = []
            if 'finnair' in request.POST:
                airlines.append('Finnair')
            if 'aeroflot' in request.POST:
                airlines.append('Aeroflot')
            if 'rossiay' in request.POST:   
                airlines.append('Rossiya')
            if 'airbaltic' in request.POST:
                airlines.append('AirBaltic')
            dows = []
            if 'monday' in request.POST:
                dows.append('Monday')
            if 'tuesday' in request.POST:
                dows.append('Tuesday')
            if 'wednesday' in request.POST:
                dows.append('Wednesday')
            if 'thursday' in request.POST:
                dows.append('Thursday')
            if 'friday' in request.POST:
                dows.append('Friday')
            if 'saturday' in request.POST:
                dows.append('Saturday')
            if 'sunday' in request.POST:
                dows.append('Sunday')
            cntx = Context({'od_to':    request.POST['od_to'],
                            'od_from':  request.POST['od_from'],
                            'dep_to':   request.POST['dep_to'],
                            'dep_from': request.POST['dep_from'],
                            'airlines': airlines,
                            'dows':     dows,
                            'sl_days':  request.POST['sl_days'],
                            'csv_file': csv_file })
            tmpl = loader.get_template('od_competition_results.htm')
            return HttpResponse(tmpl.render(cntx))
        print 'No it is not valid'
    else:
        form = CompetitionForm()

    return render_to_response('od_competition_form.htm', {'form': form},
                              context_instance=RequestContext(request))
'''




