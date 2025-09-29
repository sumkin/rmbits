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

from flight import *

def index(request,orgn,dstn,fltnum):
    fl = flight(orgn,dstn,fltnum)
    tmpl = loader.get_template('route.htm')
    cntx = Context({
           'orgn': orgn,
           'dstn': dstn,
           'fltnum': fltnum,
           'curr_date': datetime.now().strftime('%Y-%m-%d'),
#           'db_stat_fdep': fl.get_first_dep_date(),
#           'db_stat_ldep': fl.get_last_dep_date(),
#           'db_stat_numdep': fl.get_num_deps(),
#           'db_stat_numflowndep': fl.get_num_flown_deps(),
#           'db_stat_numpastdep': fl.get_num_past_deps(),
    })
    return HttpResponse(tmpl.render(cntx))

def book(request,orgn,dstn,fltnum):
    tmpl = loader.get_template('route_book.htm')
    cntx = Context({ 'orgn': orgn,
                    'dstn': dstn,
                    'fltnum': fltnum,
    })
    return HttpResponse(tmpl.render(cntx))

def book_j(request,orgn,dstn,fltnum):
    tmpl = loader.get_template('route_book_j.htm')
    cntx = Context({ 'orgn': orgn,
                     'dstn': dstn,
                     'fltnum': fltnum,
    })
    return HttpResponse(tmpl.render(cntx))

def book_y(request,orgn,dstn,fltnum):
    tmpl = loader.get_template('route_book_y.htm')
    cntx = Context({ 'orgn': orgn,
                     'dstn': dstn,
                     'fltnum': fltnum,
    })
    return HttpResponse(tmpl.render(cntx))

def revenue(request,orgn,dstn,fltnum):
    tmpl = loader.get_template('route_revenue.htm')
    cntx = Context({ 'orgn': orgn,
                     'dstn': dstn,
                     'fltnum': fltnum,
    })
    return HttpResponse(tmpl.render(cntx))

def revenue_j(request,orgn,dstn,fltnum):
    tmpl = loader.get_template('route_revenue_j.htm')
    cntx = Context({ 'orgn': orgn,
                     'dstn': dstn,
                     'fltnum': fltnum,
    })
    return HttpResponse(tmpl.render(cntx))

def revenue_y(request,orgn,dstn,fltnum):
    tmpl = loader.get_template('route_revenue_y.htm')
    cntx = Context({ 'orgn': orgn,
                     'dstn': dstn,
                     'fltnum': fltnum,
    })
    return HttpResponse(tmpl.render(cntx))

def class_corr(request,orgn,dstn,fltnum):
    tmpl = loader.get_template('route_class_corr.htm')
    cntx = Context({})
    return HttpResponse(tmpl.render(cntx))

def db_stat(request,orgn,dstn,fltnum):
    fl = flight(orgn,dstn,fltnum)
    tmpl = loader.get_template('route_db_stat.htm')
    cntx = Context({ 'orgn': orgn,
                     'dstn': dstn,
                     'fltnum': fltnum,
                     'db_stat_fdep': fl.get_first_dep_date(),
                     'db_stat_ldep': fl.get_last_dep_date(),
                     'db_stat_numdep': fl.get_num_deps(),
                     'db_stat_numflowndep': fl.get_num_flown_deps(),
                     'db_stat_numpastdep': fl.get_num_past_deps(),
    })
    return HttpResponse(tmpl.render(cntx))

def forecast(request,orgn,dstn,fltnum):
    tmpl = loader.get_template('route_forecast.htm')
    cntx = Context({ 'orgn': orgn,
                     'dstn': dstn,
                     'fltnum': fltnum,
    })
    return HttpResponse(tmpl.render(cntx))   

def class_mix(request,orgn,dstn,fltnum):
    tmpl = loader.get_template('route_class_mix.htm')
    cntx = Context({ 'orgn': orgn,
                     'dstn': dstn,
                     'fltnum': fltnum,
    })
    return HttpResponse(tmpl.render(cntx))

def aircraft_change_seq_output(orgn,dstn,fltnum):
    fl = Flight(orgn,dstn,fltnum)
    deps = []
    num = 0
    dptdt = datetime.now().date()
    future_deps = fl.get_future_deps(dptdt,dptdt)
    tmpl = loader.get_template('route_aircraft_change.htm')
    cntx = Context({ 'orgn':   orgn,
                     'dstn':   dstn,
                     'fltnum': fltnum,
                     'num':    len(future_deps)
    }) 
    yield tmpl.render(cntx)

    for dep in future_deps:
        ret_dep = dep.get_return_dep()
        [best_ac,rev_est] = dep.get_aircraft_chng_est()
        sub_tmpl = loader.get_template('route_aircraft_change_departure.htm')
        sub_cntx = Context({ 'dep':     dep,
                             'ret_dep': ret_dep,
                             'best_ac': best_ac,
                             'rev_est': rev_est
        })
        yield sub_tmpl.render(sub_cntx)

def aircraft_change(request,orgn,dstn,fltnum):
    # date comes in format YYYY-MM-DD
    return HttpResponse(aircraft_change_seq_output(orgn,dstn,fltnum))

def yield_(request,orgn,dstn,fltnum):
    tmpl = loader.get_template('route_yield.htm')
    cntx = Context({ 'orgn': orgn,
                     'dstn': dstn,
                     'fltnum': fltnum,
    })
    return HttpResponse(tmpl.render(cntx))

def summary(request,orgn,dstn,fltnum):
    tmpl = loader.get_template('route_summary.htm')
    cntx = Context({ 'orgn': orgn,
                     'dstn': dstn,
                     'fltnum': fltnum,
    })
    return HttpResponse(tmpl.render(cntx))




