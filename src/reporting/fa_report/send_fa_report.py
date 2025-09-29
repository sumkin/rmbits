import os
import sys
import scipy
from math import sqrt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import legend
from matplotlib.ticker import FuncFormatter
import numpy as np

import ConfigParser
from datetime import datetime,timedelta
from django.conf import settings
from django.template import Context, loader

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))
sys.path.append(config.get('PATHS','emailui'))

from cls import get_cmpt

DATA_PATH = config.get('PATHS','fa_data')

try:
  abs_path = os.path.realpath(__file__)
  abs_paths = abs_path.split('/')
  dir_path = '/'.join(abs_paths[:len(abs_paths)-1])
  settings.configure(DEBUG=True,TEMPLATE_DEBUG=True,TEMPLATE_DIRS=[dir_path+'/',dir_path+'/'])
except:
  pass

from db_connector import dbConnector
from cls import get_clss_
from daysprior import get_dayspriors_short
from emailsender.email_sender import EmailSender
from copy_data import copy_data
from marketowners import marketowners as mo

def frmt_percent(y,pos=0):
  return '%1.0f%%' % (100*y)

def abs_fe_ts_fl(orgn,dstn,daysprior):
  or_curs = dbConnector.get_or_curs()
  q = "SELECT fa1.consfnldmd - fa2.consfnldmd,fa1.booked,fa2.booked,fa2.consfnldmd\
       FROM (SELECT SUM(consfnldmd) AS consfnldmd,SUM(booked) AS booked,fltnum,dptdt,orgn,dstn,daysprior\
             FROM forecast_accuracy_fl\
             WHERE (orgn='"+orgn+"' AND dstn='"+dstn+"') OR\
                   (orgn='"+dstn+"' AND dstn='"+orgn+"')\
             GROUP BY fltnum,dptdt,orgn,dstn,daysprior) fa1,\
            (SELECT SUM(consfnldmd) AS consfnldmd,SUM(booked) AS booked,fltnum,dptdt,orgn,dstn,daysprior\
             FROM forecast_accuracy_fl\
             WHERE (orgn='"+orgn+"' AND dstn='"+dstn+"') OR\
                   (orgn='"+dstn+"' AND dstn='"+orgn+"')\
             GROUP BY fltnum,dptdt,orgn,dstn,daysprior) fa2\
       WHERE fa1.fltnum = fa2.fltnum AND\
             fa1.dptdt = fa2.dptdt AND\
             fa1.orgn = fa2.orgn AND\
             fa1.dstn = fa2.dstn AND\
             fa2.daysprior = -1 AND\
             fa1.daysprior = "+str(daysprior)+";"

  or_curs.execute(q)
  rows = or_curs.fetchall()
  
  res = [float(e[0]) for e in rows]
  ressq = [e**2 for e in res]
  rmse = sqrt(scipy.mean(ressq))
  mn = scipy.mean(res)
  sd = scipy.std(res)

  cur_bkd = scipy.mean([float(e[1]) for e in rows])
  fnl_bkd = scipy.mean([float(e[2]) for e in rows])

  fnl_dmd_mn = scipy.mean([float(e[3]) for e in rows])
  fnl_dmd_sd = scipy.std([float(e[3]) for e in rows])

  if np.isnan(rmse):
    rmse = 0
  if np.isnan(mn):
    mn = 0
  if np.isnan(sd):
    sd = 0
  if np.isnan(cur_bkd):
    cur_bkd = 0
  if np.isnan(fnl_bkd):
    fnl_bkd = 0
  if np.isnan(fnl_dmd_mn):
    fnl_dmd_mn = 0
  if np.isnan(fnl_dmd_sd):
    fnl_dmd_sd = 0

  return round(rmse,1),round(mn,1),round(sd,1),round(cur_bkd,0),round(fnl_bkd,0),round(fnl_dmd_mn,0),round(fnl_dmd_sd,0)

def abs_fe_ts_cmp(orgn,dstn,cmp,daysprior):
  or_curs = dbConnector.get_or_curs()
  q = "SELECT fa1.consfnldmd - fa2.consfnldmd,fa1.booked,fa2.booked,fa2.consfnldmd\
       FROM (SELECT SUM(consfnldmd) as consfnldmd,SUM(booked) AS booked,fltnum,dptdt,orgn,dstn,cmp,daysprior\
             FROM forecast_accuracy_cmp\
             WHERE (orgn='"+orgn+"' AND dstn='"+dstn+"') OR\
                   (orgn='"+dstn+"' AND dstn='"+orgn+"')\
             GROUP BY fltnum,cmp,dptdt,orgn,dstn,daysprior) fa1,\
            (SELECT SUM(consfnldmd) as consfnldmd,SUM(booked) AS booked,fltnum,dptdt,orgn,dstn,cmp,daysprior\
             FROM forecast_accuracy_cmp\
             WHERE (orgn='"+orgn+"' AND dstn='"+dstn+"') OR\
                   (orgn='"+dstn+"' AND dstn='"+orgn+"')\
             GROUP BY fltnum,cmp,dptdt,orgn,dstn,daysprior) fa2\
       WHERE fa1.fltnum = fa2.fltnum AND\
             fa1.dptdt = fa2.dptdt AND\
             fa1.cmp = fa2.cmp AND fa1.cmp = '"+cmp+"' AND\
             fa1.orgn = fa2.orgn AND\
             fa1.dstn = fa2.dstn AND\
             fa2.daysprior = -1 AND\
             fa1.daysprior = "+str(daysprior)+";"

  or_curs.execute(q)
  rows = or_curs.fetchall()
  
  res = [float(e[0]) for e in rows]
  ressq = [e**2 for e in res]
  rmse = sqrt(scipy.mean(ressq))
  mn = scipy.mean(res)
  sd = scipy.std(res)

  cur_bkd = scipy.mean([float(e[1]) for e in rows])
  fnl_bkd = scipy.mean([float(e[2]) for e in rows])

  fnl_dmd_mn = scipy.mean([float(e[3]) for e in rows])
  fnl_dmd_sd = scipy.std([float(e[3]) for e in rows])

  if np.isnan(rmse):
    rmse = 0
  if np.isnan(mn):
    mn = 0
  if np.isnan(sd):
    sd = 0
  if np.isnan(cur_bkd):
    cur_bkd = 0
  if np.isnan(fnl_bkd):
    fnl_bkd = 0
  if np.isnan(fnl_dmd_mn):
    fnl_dmd_mn = 0
  if np.isnan(fnl_dmd_sd):
    fnl_dmd_sd = 0

  return round(rmse,1),round(mn,1),round(sd,1),round(cur_bkd,0),round(fnl_bkd,0),round(fnl_dmd_mn,0),round(fnl_dmd_sd,0)

def abs_fe_ts_cls(orgn,dstn,cls,daysprior):
  or_curs = dbConnector.get_or_curs()
  q = "SELECT fa1.consfnldmd - fa2.consfnldmd,fa1.booked,fa2.booked,fa2.consfnldmd\
       FROM (SELECT consfnldmd,booked,fltnum,dptdt,orgn,dstn,daysprior,cls\
             FROM forecast_accuracy_cls\
             WHERE (orgn='"+orgn+"' AND dstn='"+dstn+"') OR (orgn='"+dstn+"' AND dstn='"+orgn+"')) fa1,\
            (SELECT consfnldmd,booked,fltnum,dptdt,orgn,dstn,daysprior,cls\
             FROM forecast_accuracy_cls\
             WHERE (orgn='"+orgn+"' AND dstn='"+dstn+"') OR (orgn='"+dstn+"' AND dstn='"+orgn+"')) fa2\
       WHERE fa1.fltnum = fa2.fltnum AND\
             fa1.dptdt = fa2.dptdt AND\
             fa1.orgn = fa2.orgn AND\
             fa1.dstn = fa2.dstn AND\
             fa1.cls = fa2.cls AND fa1.cls = '"+cls+"' AND\
             fa2.daysprior = -1 AND\
             fa1.daysprior = "+str(daysprior)+";"
  or_curs.execute(q)
  rows = or_curs.fetchall()
  res = [float(e[0]) for e in rows]
  ressq = [e**2 for e in res]
  rmse = sqrt(scipy.mean(ressq))
  mn = scipy.mean(res)
  sd = scipy.std(res)

  cur_bkd = scipy.mean([float(e[1]) for e in rows])
  fnl_bkd = scipy.mean([float(e[2]) for e in rows])

  fnl_dmd_mn = scipy.mean([float(e[3]) for e in rows])
  fnl_dmd_sd = scipy.std([float(e[3]) for e in rows])

  if np.isnan(rmse):
    rmse = 0
  if np.isnan(mn):
    mn = 0
  if np.isnan(sd):
    sd = 0
  if np.isnan(cur_bkd):
    cur_bkd = 0
  if np.isnan(fnl_bkd):
    fnl_bkd = 0
  if np.isnan(fnl_dmd_mn):
    fnl_dmd_mn = 0
  if np.isnan(fnl_dmd_sd):
    fnl_dmd_sd = 0

  return round(rmse,1),round(mn,1),round(sd,1),round(cur_bkd,0),round(fnl_bkd,0),round(fnl_dmd_mn,0),round(fnl_dmd_sd,0)

def generate_pdf(orgn,dstn,dfroms,dtos,clss,dayspriors,data_cls,data_cmp,data_fl,imgs_cls,imgs_cmp,imgs_fl):
  tmpl_fname = 'fa_report.tmpl'
  fname = orgn + '_' + dstn + '_fa_report'
  full_fname = DATA_PATH + '/' + fname

  tmpl = loader.get_template(tmpl_fname)
  cntx = Context({'orgn': orgn,
                  'dstn': dstn,
                  'dfrom': dfroms,
                  'dto': dtos,
                  'clss': clss,
                  'dayspriors': dayspriors,
                  'data_cls': data_cls,
                  'data_cmp': data_cmp,
                  'data_fl': data_fl,
                  'imgs_cls': imgs_cls,
                  'imgs_cmp': imgs_cmp,
                  'imgs_fl': imgs_fl})
  tex_fname = full_fname + '.tex'
  f = open(tex_fname,'w')
  f.write(tmpl.render(cntx))
  f.close()

  # Generate PDF
  curr_path = os.getcwd()
  os.chdir(DATA_PATH)

  pdf_fname = full_fname + '.pdf'
  cmd = "pdflatex " + fname + ".tex" 

  os.system(cmd)
  os.chdir(curr_path)

  return pdf_fname

def get_text(market):
  or_curs = dbConnector.get_or_curs()
  q = "SELECT DISTINCT orgn,dstn,fltnum\
       FROM forecast_accuracy_cmp\
       WHERE orgn = '"+market+"' OR\
             dstn = '"+market+"'"
  or_curs.execute(q)
  rows = or_curs.fetchall()

  links = []
  for row in rows:
    orgn = row[0]
    dstn = row[1]
    fltnum = row[2]
    link = "http://157.200.170.110/route_forecast/"+orgn+"/"+dstn+"/"+fltnum
    links.append(link)

  txt  = "Monthly route forecast report for "+market+" is attached.\n\n"
  txt += "To check the current forecasts on flight number level use the links below.\n\n"
  for link in links:
    txt += link + "\n"
  txt += "\n"
  txt += "IMPORTANT: to view forecasts please use Firefox or Chrome browser. IE is not supported.\n\n"
  txt += "Regards,\nFedor"
  return txt

def send_fa_report():
  
  # Copy data from DW
  print 'Copying data from DW to local database...'
  
  dfroms,dtos = copy_data()

  # Generating report
  print 'Generating reports...'

  for owner in mo.get_owners():
    for market in mo.get_markets(owner=owner): 
      orgn = 'HEL'
      dstn = market
      clss = get_clss_()
      cmps = ['J','Y']
      dayspriors = get_dayspriors_short()
      data_cls = []
      data_cmp = []
      data_fl = []
      imgs_cls = []
      imgs_cmp = []
      imgs_fl = []

      # Flight figures
      d = []
      for dp in dayspriors:
        rmse,mn,sd,cur_bkd,fnl_bkd,dmd_mn,dmd_sd = abs_fe_ts_fl(orgn,dstn,dp)
        if int(fnl_bkd) != 0:
          d.append([round(float(rmse)/fnl_bkd,2),round(float(mn)/fnl_bkd,2),round(float(sd)/fnl_bkd,2),round(float(cur_bkd)/fnl_bkd,2)])
        else:
          d.append([0,0,0,0])
      dmd = [dmd_mn,dmd_sd]
      data_fl.append([d,dmd])
      fl_dmd_mn = dmd_mn

      ds = dayspriors

      fname = DATA_PATH + '/' + orgn+'_'+dstn+'_fl.png'
      matplotlib.rcParams.update({'font.size':8})
      fig = plt.gcf()
      fig.set_size_inches(8,2)
      plt.xticks(range(0,len(ds)),ds)
      p1 = plt.plot([e[0] for e in d],label='RMSE')
      p2 = plt.plot([e[1] for e in d],label='Mean')
      p3 = plt.plot([e[2] for e in d],label='SD')
      p4 = plt.plot([e[3] for e in d],label='Booking curve')
      plt.legend(['RMSE','Mean','SD','Booking curve'],prop={'size':8},bbox_to_anchor=(0.,1.,1.,.08),loc=3,ncol=4,mode='expand',borderaxespad=0)
      plt.grid(b=True,color='grey')
      ay = plt.gca().yaxis
      ay.set_major_formatter(FuncFormatter(frmt_percent))
      plt.savefig(fname)
      plt.close()
      imgs_fl.append([fname])
 
      # Compartment figures
      for cmp in cmps:
        d = []
        for dp in dayspriors:
          rmse,mn,sd,cur_bkd,fnl_bkd,dmd_mn,dmd_sd = abs_fe_ts_cmp(orgn,dstn,cmp,dp)
          if int(fnl_bkd) != 0:
            d.append([round(float(rmse)/fnl_bkd,2),round(float(mn)/fnl_bkd,2),round(float(sd)/fnl_bkd,2),round(float(cur_bkd)/fnl_bkd,2)])
          else:
            d.append([0,0,0,0])
        dmd = [dmd_mn,dmd_sd]
        data_cmp.append([cmp,d,dmd]) # FIXME: ask demand many times...

        ds = dayspriors

        fname = DATA_PATH + '/' + orgn+'_'+dstn+'_'+cmp+'_cmp.png'

        matplotlib.rcParams.update({'font.size':8})
        fig = plt.gcf()
        fig.set_size_inches(8,2)
        plt.xticks(range(0,len(ds)),ds)
        p1 = plt.plot([e[0] for e in d],label='RMSE')
        p2 = plt.plot([e[1] for e in d],label='Mean')
        p3 = plt.plot([e[2] for e in d],label='SD')
        p4 = plt.plot([e[3] for e in d],label='Booking curve')
        plt.legend(['RMSE','Mean','SD','Booking curve'],prop={'size':8},bbox_to_anchor=(0.,1.,1.,.08),loc=3,ncol=4,mode='expand',borderaxespad=0)
        plt.grid(b=True,color='grey')
        ay = plt.gca().yaxis
        ay.set_major_formatter(FuncFormatter(frmt_percent))
        plt.savefig(fname)
        plt.close()
        imgs_cmp.append([cmp,fname])

      # Class figures 
      for cls in clss:
        d = []
        for dp in dayspriors:
          rmse,mn,sd,cur_bkd,fnl_bkd,dmd_mn,dmd_sd = abs_fe_ts_cls(orgn,dstn,cls,dp)
          if int(fnl_bkd) != 0:
            d.append([round(float(rmse)/fnl_bkd,2),round(float(mn)/fnl_bkd,2),round(float(sd)/fnl_bkd,2),round(float(cur_bkd)/fnl_bkd,2)])
          else:
            d.append([0,0,0,0])
        dmd = [dmd_mn,dmd_sd]
        data_cls.append([cls,d,dmd]) # FIXME: ask demand for each daysprior

        ds = dayspriors

        fname = DATA_PATH + '/' + orgn+'_'+dstn+'_'+cls+'_cls.png'

        matplotlib.rcParams.update({'font.size':8})
        fig = plt.figure()
        fig.set_size_inches(8,2)
        plt.xticks(range(0,len(ds)),ds)
        p1 = plt.plot([e[0] for e in d],label='RMSE')
        p2 = plt.plot([e[1] for e in d],label='Mean')
        p3 = plt.plot([e[2] for e in d],label='SD')
        p4 = plt.plot([e[3] for e in d],label='Booking curve')
        try:
          dmd_ratio = float(dmd_mn)/float(fl_dmd_mn)
        except:
          dmd_ratio = 0.0
        p5 = plt.plot([dmd_ratio]*len(d),label='Demand')

        # Draw demand figures
        cmpt = get_cmpt(cls)
        for dc in data_cmp:
          if dc[0] == cmpt:
            cmpt_dmd = dc[2][0]
            break

        if int(cmpt_dmd) == 0:
          dmd_perc = [0]*len(d)
        else:
          dmd_perc = [round(dmd[0]/cmpt_dmd,2)]*len(d)

        plt.legend(['RMSE','Mean','SD','Booking curve','Demand'],prop={'size':8},bbox_to_anchor=(0.,1.,1.,.08),loc=3,ncol=5,mode='expand',borderaxespad=0)
        plt.grid(b=True,color='grey')
        ay = plt.gca().yaxis
        ay.set_major_formatter(FuncFormatter(frmt_percent))
        plt.savefig(fname)
        plt.close()
        imgs_cls.append([cls,fname])

      pdf_file = generate_pdf(orgn,dstn,dfroms,dtos,clss,dayspriors,data_cls,data_cmp,data_fl,imgs_cls,imgs_cmp,imgs_fl)

      # Sending email
      es = EmailSender('157.200.13.44',25)
      sbj = orgn + '-' + dstn + ' forecast accuracy'
      txt = get_text(market)
      #owner = 'fedor.nikitin'
      es.send_multipart('fedor.nikitin@finnair.com',
                        owner+'@finnair.com',sbj,txt,[pdf_file])

if __name__ == '__main__':
  send_fa_report()

