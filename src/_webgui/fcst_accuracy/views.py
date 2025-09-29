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

###############################
#
#            Pages
#
###############################

def index(request):

    tmpl = loader.get_template('index.htm')
    cntx = Context({
           "": "",
    })
    return HttpResponse(tmpl.render(cntx))

    #tmpl = loader.get_template('index.htm')
    #cntx = Context({
    #       "": "",
    #})
    #return HttpResponse(tmpl.render(cntx))
  return HttpResponse('Yes!')

def test(request):

    tmpl = loader.get_template('test.htm')
    cntx = Context({
           "": "",
    })
    return HttpResponse(tmpl.render(cntx))

def main(request,orgn,dstn,fltnum):

    cls_j = get_avail_cls_for_fltnum_leg_cmp(orgn,dstn,fltnum,'J')
    cls_y = get_avail_cls_for_fltnum_leg_cmp(orgn,dstn,fltnum,'Y') 

    cls_j_tpl = {}
    cls_y_tpl = {}

    for cls in cls_j:
        cls_j_tpl[cls] = colors[cls]
    for cls in cls_y:
        cls_y_tpl[cls] = colors[cls] 

    tmpl = loader.get_template('fcst_accuracy.htm')
    cntx = Context({
           'orgn': orgn,
           'dstn': dstn,
           'fltnum': fltnum,
           'cls': '',
           'daysprior': '',
           'dfrom': '',
           'dto': '',
           'cls_j': cls_j_tpl,
           'cls_y': cls_y_tpl,
           'dfrom': '',
           'dto': '',
    })
    return HttpResponse(tmpl.render(cntx))

####################################
#
#        Chart data (csv)
#
####################################

def fa_fce_csv(orgn,dstn,fltnum,cls,daysprior,dfrom,dto):

    if dfrom != '' and dto != '':

        dfrom_l = dfrom.split('-')
        dto_l = dto.split('-')
        dfrom = date(int(dfrom_l[0]),int(dfrom_l[1]),int(dfrom_l[2]))
        dto = date(int(dto_l[0]),int(dto_l[1]),int(dto_l[2]))

    if len(cls) == 0 or dfrom == '' or dto == '' or daysprior == '':
        pass
    else:
        [fcst,obs,diff,dptdt] = get_fcsterr_by_dptdt_dflc_lvl('cons',orgn,dstn,fltnum,dfrom,dto,int(daysprior),e)
        dptdt_s = [e.strftime('%Y-%m-%d') for e in dptdt]
            

####################################
#
#        Chart data (flash)
#
####################################

def cd_cons_err_by_dptdt(request,err_type,orgn,dstn,fltnum,cls,daysprior,dfrom,dto):

    if dfrom != '' and dto != '':

        dfrom_l = dfrom.split('-')
        dto_l = dto.split('-')
        dfrom = date(int(dfrom_l[0]),int(dfrom_l[1]),int(dfrom_l[2]))
        dto = date(int(dto_l[0]),int(dto_l[1]),int(dto_l[2]))

    gr = graph()
    gr.title('CONSTRAINED FORECAST ERROR','{font-size: 18px; color: #777777; font-family: Georgia}')
   

    # FIXME: Re-write this mess below!!!!

    dptdt_l = []
    if len(cls) == 0 or dfrom == '' or dto == '' or daysprior == '':
        gr.set_data([])
        gr.set_x_labels([])
    else:
        dptdt = []
        for e in cls:
            [fcst,obs,diff,dptdt] = get_fcsterr_by_dptdt_dflc_lvl('cons',orgn,dstn,fltnum,dfrom,dto,int(daysprior),e)
            gr.set_data(diff)
            gr.line(2,'0x'+colors[e],e,14)
        dptdt_s = [e.strftime('%Y-%m-%d')+'  ' for e in dptdt]
        dptdt_len = len(dptdt_s)
        # we need 30 observations
        rt = dptdt_len/30
        if rt > 0:
            i = 0
            for e in dptdt_s:
                if i % rt == 0 and i != 0:
                    dptdt_l.append(e)
                else:
                    dptdt_l.append('')            
                i = i + 1
        else:
            dptdt_l = dptdt_s
        gr.set_x_labels(dptdt_l)

        # show horizontal zero line
        zero_line = [0] * len(dptdt_s)
        gr.set_data(zero_line)
        gr.line(1,'0x000000','',14)


    if err_type == 'ae':
        gr.set_y_min(-50)
        gr.set_y_max(50)
    elif err_type == 're':
        gr.set_y_min(-1)
        gr.set_y_max(1)
    else:
        pass

    gr.set_bg_colour('#FFFFFF')
    gr.set_x_label_style(12,'#852B00',2)
    gr.set_y_label_style(12,'#852B00')

    return HttpResponse(gr.render())

def cd_uncons_err_by_dptdt(request,err_type,orgn,dstn,fltnum,cls,daysprior,dfrom,dto):

    if dfrom != '' and dto != '':

        dfrom_l = dfrom.split('-')
        dto_l = dto.split('-')
        dfrom = date(int(dfrom_l[0]),int(dfrom_l[1]),int(dfrom_l[2]))
        dto = date(int(dto_l[0]),int(dto_l[1]),int(dto_l[2]))

    gr = graph()
    gr.title('UNCONSTRAINED FORECAST ERROR','{font-size: 18px; color: #777777; font-family: Georgia}')
   

    # FIXME: Re-write this mess below!!!!

    dptdt_l = []
    if len(cls) == 0 or dfrom == '' or dto == '' or daysprior == '':
        gr.set_data([])
        gr.set_x_labels([])
    else:
        dptdt = []
        for e in cls:
            [fcst,obs,diff,dptdt] = get_fcsterr_by_dptdt_dflc_lvl('uncons',orgn,dstn,fltnum,dfrom,dto,int(daysprior),e)
            gr.set_data(diff)
            gr.line(2,'0x'+colors[e],e,14)
        dptdt_s = [e.strftime('%Y-%m-%d')+'  ' for e in dptdt]
        i = 0
        dptdt_len = len(dptdt_s)
        # we need 30 observations
        rt = dptdt_len/30
        for e in dptdt_s:
            if i % rt == 0 and i != 0:
                dptdt_l.append(e)
            else:
                dptdt_l.append('')            
            i = i + 1
        gr.set_x_labels(dptdt_l)

        # show horizontal zero line
        zero_line = [0] * len(dptdt_l)
        gr.set_data(zero_line)
        gr.line(1,'0x000000','',14)

    if err_type == 'ae':
        gr.set_y_min(-50)
        gr.set_y_max(50)
    elif err_type == 're':
        gr.set_y_min(-1)
        gr.set_y_max(1)
    else:
        pass

    gr.set_bg_colour('#FFFFFF')
    gr.set_x_label_style(12,'#852B00',2)
    gr.set_y_label_style(12,'#852B00')

    return HttpResponse(gr.render())

def cd_cons_err_by_daysprior(request,err_type,orgn,dstn,fltnum,cls,daysprior,dfrom='',dto=''):

    if dfrom != '' and dto != '':
        
        dfrom_l = dfrom.split('-')
        dto_l = dto.split('-')
        dfrom = date(int(dfrom_l[0]),int(dfrom_l[1]),int(dfrom_l[2]))
        dto = date(int(dto_l[0]),int(dto_l[1]),int(dto_l[2]))

    gr = graph()
    gr.title('MEAN OF CONSTRAINED ERROR','{font-size: 18px; color: #777777; font-family: Georgia}')

    if len(cls) == 0 or dfrom == '' or dto == '' or daysprior == '':
        gr.set_data([])
        gr.set_x_labels([])
    else:
        daysprior_l = []
        for e in cls:
            [bias,se,daysprior_l] = get_bias_var_by_daysprior_flc_lvl(type,orgn,dstn,fltnum,dfrom,dto,e)
            bias_minus = []
            bias_plus = []
            for i in range(0,len(bias)):
                bias_minus.append(bias[i] - se[i])
                bias_plus.append(bias[i] + se[i])
            gr.set_data(bias)
            gr.line(4,'0x'+colors[e],'Mean '+e,14)
            gr.set_data(bias_minus)
            gr.line(1,'0x'+colors[e],'',14)
            gr.set_data(bias_plus)
            gr.line(1,'0x'+colors[e],'',14)
        gr.set_x_labels(daysprior_l)

    if err_type == 'ae':
        gr.set_y_min(-25)
        gr.set_y_max(25)
    elif err_type == 're':
        gr.set_y_min(-1)
        gr.set_y_max(1)
    else:
        pass

    gr.set_bg_colour('#FFFFFF')
    gr.set_x_label_style(12,'#852B00',2)
    gr.set_y_label_style(12,'#852B00')

    return HttpResponse(gr.render())

def cd_uncons_err_by_daysprior(request,err_type,orgn,dstn,fltnum,cls,daysprior,dfrom='',dto=''):

    if dfrom != '' and dto != '':
        
        dfrom_l = dfrom.split('-')
        dto_l = dto.split('-')
        dfrom = date(int(dfrom_l[0]),int(dfrom_l[1]),int(dfrom_l[2]))
        dto = date(int(dto_l[0]),int(dto_l[1]),int(dto_l[2]))

    gr = graph()
    gr.title('MEAN OF UNCONSTRAINED ERROR','{font-size: 18px; color: #777777; font-family: Georgia}')

    if len(cls) == 0 or dfrom == '' or dto == '' or daysprior == '':
        gr.set_data([])
        gr.set_x_labels([])
    else:
        daysprior_l = []
        for e in cls:
            [bias,se,daysprior_l] = get_bias_var_by_daysprior_flc_lvl(type,orgn,dstn,fltnum,dfrom,dto,e)
            bias_minus = []
            bias_plus = []
            for i in range(0,len(bias)):
                bias_minus.append(bias[i] - se[i])
                bias_plus.append(bias[i] + se[i])
            gr.set_data(bias)
            gr.line(4,'0x'+colors[e],'Mean '+e,14)
            gr.set_data(bias_minus)
            gr.line(1,'0x'+colors[e],'',14)
            gr.set_data(bias_plus)
            gr.line(1,'0x'+colors[e],'',14)
        gr.set_x_labels(daysprior_l)

    if err_type == 'ae':
        gr.set_y_min(-25)
        gr.set_y_max(25)
    elif err_type == 're':
        gr.set_y_min(-1)
        gr.set_y_max(1)
    else:
        pass

    gr.set_bg_colour('#FFFFFF')
    gr.set_x_label_style(12,'#852B00',2)
    gr.set_y_label_style(12,'#852B00')

    return HttpResponse(gr.render())

def cd_cons_aval_by_dptdt(request,orgn,dstn,fltnum,cls,daysprior,dfrom,dto):

    if dfrom != '' and dto != '':

        dfrom_l = dfrom.split('-')
        dto_l = dto.split('-')
        dfrom = date(int(dfrom_l[0]),int(dfrom_l[1]),int(dfrom_l[2]))
        dto = date(int(dto_l[0]),int(dto_l[1]),int(dto_l[2]))

    gr = graph()
    gr.title('ACTUAL CONSTRAINED VALUES', '{font-size: 18px; color: #777777; font-family: Georgia}')

    if len(cls) == 0 or dfrom == '' or dto == '' or daysprior == '':
        gr.set_data([])
        gr.set_x_labels([])
    else:
        dptdt = []
        for e in cls:
            [fcst,obs,diff,dptdt] = get_fcsterr_by_dptdt_dflc_lvl('cons',orgn,dstn,fltnum,dfrom,dto,int(daysprior),e)
            gr.set_data(obs)
            gr.line(2,'0x'+colors[e],e,14)
        dptdt_l = []
        dptdt_s = [e.strftime('%Y-%m-%d')+' ' for e in dptdt]
        i = 0
        dptdt_len = len(dptdt_s)
        rt = dptdt_len/30
        for e in dptdt_s:
            if i % rt == 0 and i != 0:
                dptdt_l.append(e)
            else:
                dptdt_l.append('')
            i = i + 1
        gr.set_x_labels(dptdt_l)

    gr.set_y_min(0)
    gr.set_y_max(100)
    gr.set_bg_colour('#FFFFFF')
    gr.set_x_label_style(12,'#852B00',2)
    gr.set_y_label_style(12,'#852B00')

    return HttpResponse(gr.render())

def cd_uncons_aval_by_dptdt(request,orgn,dstn,fltnum,cls,daysprior,dfrom,dto):

    if dfrom != '' and dto != '':

        dfrom_l = dfrom.split('-')
        dto_l = dto.split('-')
        dfrom = date(int(dfrom_l[0]),int(dfrom_l[1]),int(dfrom_l[2]))
        dto = date(int(dto_l[0]),int(dto_l[1]),int(dto_l[2]))

    gr = graph()
    gr.title('ACTUAL UNCONSTRAINED VALUES', '{font-size: 18px; color: #777777; font-family: Georgia}')

    if len(cls) == 0 or dfrom == '' or dto == '' or daysprior == '':
        gr.set_data([])
        gr.set_x_labels([])
    else:
        dptdt = []
        for e in cls:
            [fcst,obs,diff,dptdt] = get_fcsterr_by_dptdt_dflc_lvl('uncons',orgn,dstn,fltnum,dfrom,dto,int(daysprior),e)
            gr.set_data(obs)
            gr.line(2,'0x'+colors[e],e,14)
        dptdt_l = []
        dptdt_s = [e.strftime('%Y-%m-%d')+' ' for e in dptdt]
        i = 0
        dptdt_len = len(dptdt_s)
        rt = dptdt_len/30
        for e in dptdt_s:
            if i % rt == 0 and i != 0:
                dptdt_l.append(e)
            else:
                dptdt_l.append('')
            i = i + 1
        gr.set_x_labels(dptdt_l)

    gr.set_y_min(0)
    gr.set_y_max(100)
    gr.set_bg_colour('#FFFFFF')
    gr.set_x_label_style(12,'#852B00',2)
    gr.set_y_label_style(12,'#852B00')

    return HttpResponse(gr.render())

def cd_cons_fval_by_dptdt(request,orgn,dstn,fltnum,cls,daysprior,dfrom,dto):

    if dfrom != '' and dto != '':

        dfrom_l = dfrom.split('-')
        dto_l = dto.split('-')
        dfrom = date(int(dfrom_l[0]),int(dfrom_l[1]),int(dfrom_l[2]))
        dto = date(int(dto_l[0]),int(dto_l[1]),int(dto_l[2]))

    gr = graph()
    gr.title('FORECASTED CONSTRAINED VALUES', '{font-size: 18px; color: #777777; font-family: Georgia}')

    if len(cls) == 0 or dfrom == '' or dto == '' or daysprior == '':
        gr.set_data([])
        gr.set_x_labels([])
    else:
        dptdt = []
        for e in cls:
            [fcst,obs,diff,dptdt] = get_fcsterr_by_dptdt_dflc_lvl('cons',orgn,dstn,fltnum,dfrom,dto,int(daysprior),e)
            gr.set_data(fcst)
            gr.line(2,'0x'+colors[e],e,14)
        dptdt_l = []
        dptdt_s = [e.strftime('%Y-%m-%d')+' ' for e in dptdt]
        i = 0
        dptdt_len = len(dptdt_s)
        rt = dptdt_len/30
        for e in dptdt_s:
            if i % rt == 0 and i != 0:
                dptdt_l.append(e)
            else:
                dptdt_l.append('')
            i = i + 1
        gr.set_x_labels(dptdt_l)

    gr.set_y_min(0)
    gr.set_y_max(100)
    gr.set_bg_colour('#FFFFFF')
    gr.set_x_label_style(12,'#852B00',2)
    gr.set_y_label_style(12,'#852B00')

    return HttpResponse(gr.render())


def cd_uncons_fval_by_dptdt(request,orgn,dstn,fltnum,cls,daysprior,dfrom,dto):

    # convert classes to upper-case
    cls = [e.upper() for e in cls]

    if dfrom != '' and dto != '':

        dfrom_l = dfrom.split('-')
        dto_l = dto.split('-')
        dfrom = date(int(dfrom_l[0]),int(dfrom_l[1]),int(dfrom_l[2]))
        dto = date(int(dto_l[0]),int(dto_l[1]),int(dto_l[2]))

    gr = graph()
    gr.title('FORECASTED UNCONSTRAINED VALUES', '{font-size: 18px; color: #777777; font-family: Georgia}')

    if len(cls) == 0 or dfrom == '' or dto == '' or daysprior == '':
        gr.set_data([])
        gr.set_x_labels([])
    else:
        dptdt = []
        for e in cls:
            [fcst,obs,diff,dptdt] = get_fcsterr_by_dptdt_dflc_lvl('uncons',orgn,dstn,fltnum,dfrom,dto,int(daysprior),e)
            gr.set_data(fcst)
            gr.line(2,'0x'+colors[e],e,14)
        dptdt_l = []
        dptdt_s = [e.strftime('%Y-%m-%d')+' ' for e in dptdt]
        i = 0
        dptdt_len = len(dptdt_s)
        rt = dptdt_len/30
        for e in dptdt_s:
            if i % rt == 0 and i != 0:
                dptdt_l.append(e)
            else:
                dptdt_l.append('')
            i = i + 1
        gr.set_x_labels(dptdt_l)

    gr.set_y_min(0)
    gr.set_y_max(100)
    gr.set_bg_colour('#FFFFFF')
    gr.set_x_label_style(12,'#852B00',2)
    gr.set_y_label_style(12,'#852B00')

    return HttpResponse(gr.render())

def cd_cons_lbpval_by_daysprior(request,err_type,orgn,dstn,fltnum,cls,daysprior,dfrom,dto):
    #
    # FIXME: daysprior parameter isn't needed here
    # 
    if dfrom != '' and dto != '':
    
        dfrom_l = dfrom.split('-')
        dto_l = dto.split('-')
        dfrom = date(int(dfrom_l[0]),int(dfrom_l[1]),int(dfrom_l[2]))
        dto = date(int(dto_l[0]),int(dto_l[1]),int(dto_l[2]))

    gr = graph()
    gr.title('LJUNG-BOX P-VALUE', '{font-size: 18px; color: #777777; font-family: Georgia}')

    if len(cls) == 0 or dfrom == '' or dto == '' or daysprior == '':
        gr.set_data([])
        gr.set_x_labels([])
    else:
        dayspriors = get_avail_daysprior_for_fltnum_leg(orgn,dstn,fltnum,dfrom,dto)
        for e in cls:
            pvals = []
            for daysprior in dayspriors:
                pval = get_ljung_box_pval(err_type,orgn,dstn,fltnum,dfrom,dto,daysprior,e)
                pvals.append(pval)
            gr.set_data(pvals)
            gr.line(2,'0x'+colors[e],e,14)
            gr.set_x_labels(dayspriors)

    thrshld_line = [0.05] * len(dayspriors)
    gr.set_data(thrshld_line)
    gr.line(2,'0xBBBBBB','',14) 
   
    gr.set_y_min(0)
    gr.set_y_max(1)
    gr.set_bg_colour('#FFFFFF')      
    gr.set_x_label_style(12,'#852B00',2)
    gr.set_y_label_style(12,'#852B00')

    return HttpResponse(gr.render()) 
 
def cd_uncons_lbpval_by_daysprior(request,err_type,orgn,dstn,fltnum,cls,daysprior,dfrom,dto):
    #
    # FIXME: daysprior parameter isn't needed here
    # 
    if dfrom != '' and dto != '':
    
        dfrom_l = dfrom.split('-')
        dto_l = dto.split('-')
        dfrom = date(int(dfrom_l[0]),int(dfrom_l[1]),int(dfrom_l[2]))
        dto = date(int(dto_l[0]),int(dto_l[1]),int(dto_l[2]))

    gr = graph()
    gr.title('LJUNG-BOX P-VALUE', '{font-size: 18px; color: #777777; font-family: Georgia}')

    if len(cls) == 0 or dfrom == '' or dto == '' or daysprior == '':
        gr.set_data([])
        gr.set_x_labels([])
    else:
        dayspriors = get_avail_daysprior_for_fltnum_leg(orgn,dstn,fltnum,dfrom,dto)
        for e in cls:
            print 'cls: ' + e
            pvals = []
            for daysprior in dayspriors:
                print '\t' + str(daysprior)
                pval = get_ljung_box_pval(err_type,orgn,dstn,fltnum,dfrom,dto,daysprior,e)
                pvals.append(pval)
            gr.set_data(pvals)
            gr.line(2,'0x'+colors[e],e,14)
            gr.set_x_labels(dayspriors)

    thrshld_line = [0.05] * len(dayspriors)
    gr.set_data(thrshld_line)
    gr.line(2,'0xBBBBBB','',14) 
   
    gr.set_y_min(0)
    gr.set_y_max(1)
    gr.set_bg_colour('#FFFFFF')      
    gr.set_x_label_style(12,'#852B00',2)
    gr.set_y_label_style(12,'#852B00')

    return HttpResponse(gr.render()) 
 
def cd_cons_booked_by_dptdt(request,orgn,dstn,fltnum,cls,daysprior,dfrom,dto):

    if dfrom != '' and dto != '':
    
        dfrom_l = dfrom.split('-')
        dto_l = dto.split('-')
        dfrom = date(int(dfrom_l[0]),int(dfrom_l[1]),int(dfrom_l[2]))
        dto = date(int(dto_l[0]),int(dto_l[1]),int(dto_l[2]))

    gr = graph()
    gr.title('CONSTRAINED BOOKED VALUES', '{font-size: 18px; color: #777777; font-family: Georgia}')

    if len(cls) == 0 or dfrom == '' or dto == '' or daysprior == '':
        gr.set_data([3,4,5])
        gr.set_x_labels([])
    else:
        for e in cls:
            [bookeds,dptdts] = get_booked_by_dptdt_dflc_lvl('cons',orgn,dstn,fltnum,dfrom,dto,int(daysprior),e)
            gr.set_data(bookeds)
            gr.line(2,'0x'+colors[e],e,14)
        dptdt_s = [e.strftime('%Y-%m-%d')+' ' for e in dptdts]
        i = 0
        dptdt_l = []
        dptdt_len = len(dptdt_s)
        rt = dptdt_len/30
        for e in dptdt_s:
            if i % rt == 0 and i != 0:
                dptdt_l.append(e)
            else:
                dptdt_l.append('')
            i = i + 1
        gr.set_x_labels(dptdt_l)

    gr.set_y_min(0)
    gr.set_y_max(100)
    gr.set_bg_colour('#FFFFFF')
    gr.set_x_label_style(12,'#852B00',2) 
    gr.set_y_label_style(12,'#852B00')

    return HttpResponse(gr.render())

def cd_uncons_booked_by_dptdt(request,orgn,dstn,fltnum,cls,daysprior,dfrom,dto):

    if dfrom != '' and dto != '':
    
        dfrom_l = dfrom.split('-')
        dto_l = dto.split('-')
        dfrom = date(int(dfrom_l[0]),int(dfrom_l[1]),int(dfrom_l[2]))
        dto = date(int(dto_l[0]),int(dto_l[1]),int(dto_l[2]))

    gr = graph()
    gr.title('UNCONSTRAINED BOOKED VALUES', '{font-size: 18px; color: #777777; font-family: Georgia}')

    if len(cls) == 0 or dfrom == '' or dto == '' or daysprior == '':
        gr.set_data([])
        gr.set_x_labels([])
    else:
        for e in cls:
            [bookeds,dptdts] = get_booked_by_dptdt_dflc_lvl('uncons',orgn,dstn,fltnum,dfrom,dto,int(daysprior),e)
            gr.set_data(bookeds)
            gr.line(2,'0x'+colors[e],e,14)
        dptdt_s = [e.strftime('%Y-%m-%d')+' ' for e in dptdts]
        i = 0
        dptdt_l = []
        dptdt_len = len(dptdt_s)
        rt = dptdt_len/30
        for e in dptdt_s:
            if i % rt == 0 and i != 0:
                dptdt_l.append(e)
            else:
                dptdt_l.append('')
            i = i + 1
        gr.set_x_labels(dptdt_l)

    gr.set_y_min(0)
    gr.set_y_max(100)
    gr.set_bg_colour('#FFFFFF')
    gr.set_x_label_style(12,'#852B00',2) 
    gr.set_y_label_style(12,'#852B00')

    return HttpResponse(gr.render())



###################################
#
#           Ajax content
#
###################################

def ajax_orgn(request):

    dto = datetime.now()
    dlt = timedelta(days=320)
    dfrom = dto - dlt

    term = request.GET['term']

    orgn_l = get_avail_orgns(dfrom, dto,term)
    return HttpResponse(json.dumps(orgn_l))

def ajax_dstn(request,orgn):

    dto = datetime.now()
    dlt = timedelta(days=320)
    dfrom = dto - dlt

    term = request.GET['term']

    dstn_l = get_avail_dstns_for_orgn(dfrom,dto,orgn,term)
    return HttpResponse(json.dumps(dstn_l))

def ajax_fltnum(request,orgn,dstn,fltnum):

    dto = datetime.now()
    dlt = timedelta(days=320)
    dfrom = dto - dlt

    fltnum_l = get_avail_fltnum_for_leg(orgn,dstn,dfrom,dto)

    tmpl = loader.get_template('fltnum_option_list.htm')
    cntx = Context({ 'fltnum_l': fltnum_l,
                     'curr_fltnum': fltnum })
    return HttpResponse(tmpl.render(cntx))

def ajax_cmpt(request):

    cmpt_l = get_avail_cmpt()
    return HttpResponse(json.dumps(cmpt_l))  

def ajax_cls_stats(request,orgn,dstn,fltnum,dfrom,dto,cls,daysprior):

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

def ajax_cls_stat_cnt(request,type,orgn,dstn,fltnum,dfrom,dto,daysprior,cls):

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

def ajax_tab_content(request,tab_name,orgn,dstn,fltnum,dfrom,dto,cls,daysprior):

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
<<<<<<< HEAD

=======
'''
>>>>>>> e26fbb5c6681b03a3826951a69c2f124c52f9a9e











