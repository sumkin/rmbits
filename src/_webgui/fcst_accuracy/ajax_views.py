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

from OpenFlashChart import *

from analyzer_if import get_avail_orgns
from analyzer_if import get_avail_dstns_for_orgn
from analyzer_if import get_avail_fltnum_for_leg
from analyzer_if import get_fcsterr_by_dptdt_dflc_lvl
from analyzer_if import get_booked_by_dptdt_dflc_lvl
from analyzer_if import get_avail_cmpt
from analyzer_if import get_avail_cls
from analyzer_if import get_avail_cmp_for_fltnum_leg
from analyzer_if import get_avail_cls_for_fltnum_leg_cmp
from analyzer_if import get_avail_daysprior_for_fltnum_leg
from analyzer_if import get_bias_var_by_daysprior_flc_lvl

from fcst_analyzer import get_fcsterr_mse
from fcst_analyzer import get_ljung_box_pval
from fcst_analyzer import get_fcsterr_trend_pol2

colors = {'C': 'CD5C5C',
          'D': '22AD12',
          'F': 'BB75A3',
          'I': 'FF0000',
          'J': '708090',
          'U': 'DEB887',
          'A': 'FF4500',
          'B': '800080',
          'E': '7CFC00',
          'G': 'BDB76B',
          'H': '008000',
          'K': '696969',
          'L': 'FFC0CB',
          'M': '4682B4',
          'N': '808000',
          'O': '2F4F4F',
          'P': 'C00000',
          'Q': '00BFFF',
          'R': '9370BB',
          'S': '00FFFF',
          'T': '2E8B57',
          'V': 'FFD700',
          'W': 'DC143C',
          'X': '008080',
          'Y': 'FF69B4',
          'Z': 'FFA387' }

def orgn(request):

    dto = datetime.now()
    dlt = timedelta(days=320)
    dfrom = dto - dlt

    term = request.GET['term']

    orgn_l = get_avail_orgns(dfrom, dto,term)
    return HttpResponse(json.dumps(orgn_l))

def dstn(request,orgn):

    dto = datetime.now()
    dlt = timedelta(days=320)
    dfrom = dto - dlt

    term = request.GET['term']

    dstn_l = get_avail_dstns_for_orgn(dfrom,dto,orgn,term)
    return HttpResponse(json.dumps(dstn_l))

def fltnum(request,orgn,dstn,fltnum):

    dto = datetime.now()
    dlt = timedelta(days=320)
    dfrom = dto - dlt

    fltnum_l = get_avail_fltnum_for_leg(orgn,dstn,dfrom,dto)

    tmpl = loader.get_template('fltnum_option_list.htm')
    cntx = Context({ 'fltnum_l': fltnum_l,
                     'curr_fltnum': fltnum })
    return HttpResponse(tmpl.render(cntx))

def cmpt(request):

    cmpt_l = get_avail_cmpt()
    return HttpResponse(json.dumps(cmpt_l))  

def cls(request,cmpt):

    cls_l = get_avail_cls(cmpt)
    return HttpResponse(json.dumps(cls_l))

def cls_stats(request,orgn,dstn,fltnum,dfrom,dto,cls,daysprior):

    tmpl = loader.get_template('cls_stats.htm')

    cntx = Context({ 'cls': cls,
                     'orgn': orgn,
                     'dstn': dstn,
                     'fltnum': fltnum,
                     'dfrom': dfrom,
                     'dto': dto,
                     'daysprior': daysprior
                   })

    return HttpResponse(tmpl.render(cntx))

def cls_stat_cnt(request,type,orgn,dstn,fltnum,dfrom,dto,daysprior,cls):

    dfrom_l = dfrom.split('-')
    dfrom = date(int(dfrom_l[0]),int(dfrom_l[1]),int(dfrom_l[2]))
    dto_l = dto.split('-')
    dto = date(int(dto_l[0]),int(dto_l[1]),int(dto_l[2]))

    mse = get_fcsterr_mse(type,orgn,dstn,fltnum,dfrom,dto,daysprior,cls)
    lb_pval = get_ljung_box_pval(type,orgn,dstn,fltnum,dfrom,dto,daysprior,cls)
    trend_pol2 = get_fcsterr_trend_pol2(type,orgn,dstn,fltnum,dfrom,dto,daysprior,cls)

    tmpl = loader.get_template('cls_stat_cnt.htm')
    cntx = Context({ 'mse' : mse,
                     'lb_pval': lb_pval,
                     'trend_pol2': trend_pol2,
                   })

    return HttpResponse(tmpl.render(cntx))

def tab_content(request,tab_name,orgn,dstn,fltnum,dfrom,dto,cls,daysprior):

    graph_obj = graph_object()

    if tab_name == 'bydptdt':

        fl_obj_htm_cons_err = graph_obj.render('bydptdt_cons_err', '100%25','100%25',\
                                               '/fa/cd/cons_err/bydptdt/ae/'+orgn+'/'+dstn+'/'+fltnum+'/'+\
                                               cls+'/'+daysprior+'/'+dfrom+'/'+dto, '/media/')
        fl_obj_htm_uncons_err = graph_obj.render('bydptdt_uncons_err', '100%25','100%25',\
                                                 '/fa/cd/uncons_err/bydptdt/ae/'+orgn+'/'+dstn+'/'+fltnum+'/'+\
                                                 cls+'/'+daysprior+'/'+dfrom+'/'+dto, '/media/')
        fl_obj_htm_cons_aval = graph_obj.render('bydptdt_cons_aval','100%25','100%25',\
                                                '/fa/cd/cons_aval/bydptdt/'+orgn+'/'+dstn+'/'+fltnum+'/'+\
                                                cls+'/'+daysprior+'/'+dfrom+'/'+dto, '/media/')
        fl_obj_htm_uncons_aval = graph_obj.render('bydptdt_uncons_aval','100%25','100%25',\
                                                  '/fa/cd/uncons_aval/bydptdt/'+orgn+'/'+dstn+'/'+fltnum+'/'+\
                                                  cls+'/'+daysprior+'/'+dfrom+'/'+dto, '/media/')
        fl_obj_htm_cons_fval = graph_obj.render('bydptdt_cons_fval','100%25','100%25',\
                                                '/fa/cd/cons_fval/bydptdt/'+orgn+'/'+dstn+'/'+fltnum+'/'+\
                                                cls+'/'+daysprior+'/'+dfrom+'/'+dto, '/media/')
        fl_obj_htm_uncons_fval = graph_obj.render('bydptdt_uncons_fval','100%25','100%25',\
                                                  '/fa/cd/uncons_fval/bydptdt/'+orgn+'/'+dstn+'/'+fltnum+'/'+\
                                                  cls+'/'+daysprior+'/'+dfrom+'/'+dto, '/media/')
        fl_obj_htm_cons_booked = graph_obj.render('bydptdt_cons_booked', '100%25', '100%25',\
                                                  '/fa/cd/cons_booked/bydptdt/'+orgn+'/'+dstn+'/'+fltnum+'/'+\
                                                  cls+'/'+daysprior+'/'+dfrom+'/'+dto, '/media/')
        fl_obj_htm_uncons_booked = graph_obj.render('bydptdt_uncons_booked', '100%25', '100%25',\
                                                    '/fa/cd/uncons_booked/bydptdt/'+orgn+'/'+dstn+'/'+fltnum+'/'+\
                                                    cls+'/'+daysprior+'/'+dfrom+'/'+dto, '/media/')

        tmpl = loader.get_template('tab_content_bydptdt.htm')
        cntx = Context({ 'fl_obj_htm_cons_err':      fl_obj_htm_cons_err,
                         'fl_obj_htm_uncons_err':    fl_obj_htm_uncons_err,
                         'fl_obj_htm_cons_aval':     fl_obj_htm_cons_aval,
                         'fl_obj_htm_uncons_aval':   fl_obj_htm_uncons_aval,
                         'fl_obj_htm_cons_fval':     fl_obj_htm_cons_fval,
                         'fl_obj_htm_uncons_fval':   fl_obj_htm_uncons_fval,
                         'fl_obj_htm_cons_booked':   fl_obj_htm_cons_booked,
                         'fl_obj_htm_uncons_booked': fl_obj_htm_uncons_booked })

    elif tab_name == 'bydaysprior':

        fl_obj_htm_cons_err = graph_obj.render('bydaysprior_cons_err','100%25','100%25',\
                                               '/fa/cd/cons_err/bydaysprior/ae/'+orgn+'/'+dstn+'/'+fltnum+'/'+\
                                               cls+'/'+daysprior+'/'+dfrom+'/'+dto,'/media/')
        fl_obj_htm_cons_lbpval = graph_obj.render('bydaysprior_cons_lbpval','100%25','100%25',\
                                                  '/fa/cd/cons_lbpval/ae/'+orgn+'/'+dstn+'/'+fltnum+'/'+\
                                                  cls+'/'+daysprior+'/'+dfrom+'/'+dto,'/media/') 
        tmpl = loader.get_template('tab_content_bydaysprior.htm')
        cntx = Context({ 'fl_obj_htm_cons_err': fl_obj_htm_cons_err,
                         'fl_obj_htm_cons_lbpval': fl_obj_htm_cons_lbpval })
    elif tab_name == 'outliers':
        tmpl = loader.get_template('tab_content_outliers.htm')
        cntx = Context({ '': None }) 
    else:
        print 'tab_name: ' + tab_name
        assert(0)

    return HttpResponse(tmpl.render(cntx))

def default(request):

    return HttpResponse('')













