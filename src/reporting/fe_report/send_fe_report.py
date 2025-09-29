import os
import sys
import csv
import scipy
from math import sqrt
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import legend
import numpy as np
from math import sqrt

import ConfigParser
from datetime import datetime,timedelta
from django.conf import settings
from django.template import Context, loader

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

from marketowners import marketowners as mo

sys.path.append(config.get('PATHS','datamanager'))
sys.path.append(config.get('PATHS','emailui'))

DATA_PATH = config.get('PATHS','fe_data')

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

DATA_PATH = config.get('PATHS','fe_data')

def val_err_avg(orgn,dstn,dfrom,dto):
  pu_curs = dbConnector.get_prosuser_curs()

  q = "SELECT cmpsym,AVG(consfnldmd),AVG(achfnldmd),AVG(acherrfnl)\
       FROM segment_compartment\
       WHERE (orgn,dstn,fltnum,dptdt,cmpsym,daysprior) IN\
       ( SELECT orgn,dstn,fltnum,dptdt,cmpsym,MAX(daysprior) as daysprior\
         FROM segment_compartment\
         WHERE ( ( orgn='"+orgn+"' AND dstn='"+dstn+"') OR (orgn='"+dstn+"' AND dstn='"+orgn+"') ) AND\
                   dptdt >= TO_DATE('"+dfrom+"','yyyy-mm-dd') AND dptdt < TO_DATE('"+dto+"','yyyy-mm-dd')\
         GROUP BY orgn,dstn,fltnum,dptdt,cmpsym )\
       GROUP BY cmpsym"
  pu_curs.execute(q)
  ret = {}
  results = pu_curs.fetchall()
  for result in results:
    cmpsym = result[0]
    cons_dmd = int(result[1])
    ach_dmd = int(result[2])
    err = int(result[3])
    ret[cmpsym] = [cons_dmd,ach_dmd,err]
  return ret

def val_err_sum(orgn,dstn,dfrom,dto):
  pu_curs = dbConnector.get_prosuser_curs()

  q = "SELECT cmpsym,SUM(consfnldmd),SUM(achfnldmd),SUM(acherrfnl)\
       FROM segment_compartment\
       WHERE (orgn,dstn,fltnum,dptdt,cmpsym,daysprior) IN\
       ( SELECT orgn,dstn,fltnum,dptdt,cmpsym,MAX(daysprior) as daysprior\
         FROM segment_compartment\
         WHERE ( ( orgn='"+orgn+"' AND dstn='"+dstn+"') OR (orgn='"+dstn+"' AND dstn='"+orgn+"') ) AND\
                   dptdt >= TO_DATE('"+dfrom+"','yyyy-mm-dd') AND dptdt < TO_DATE('"+dto+"','yyyy-mm-dd')\
         GROUP BY orgn,dstn,fltnum,dptdt,cmpsym )\
       GROUP BY cmpsym"
  pu_curs.execute(q)
  ret = {}
  results = pu_curs.fetchall()
  for result in results:
    cmpsym = result[0]
    cons_dmd = int(result[1])
    ach_dmd = int(result[2])
    err = int(result[3])
    ret[cmpsym] = [cons_dmd,ach_dmd,err]
  return ret  
  
def generate_pdf(months,data):
  tmpl_fname = 'fe_report.tmpl'

  dt = datetime.now()
  dt_s = dt.strftime('%Y-%m-%d %H:%M')

  fname = 'fe_report_'+dt.strftime('%Y-%m-%d')
  full_fname = DATA_PATH + '/' + fname

  tmpl = loader.get_template(tmpl_fname)
  cntx = Context({'months': months,'data': data,'dt': dt_s})
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

def generate_csv(months,data):

  dt = datetime.now()
  
  fname = 'fe_report_'+dt.strftime('%Y-%m-%d')
  full_fname = DATA_PATH + '/' + fname

  csv_fname = full_fname + '.csv'
  f = csv.writer(open(csv_fname,'w'))
  
  firstline = ['','','']
  for month in months:
    firstline.append(month)
    firstline.append(month)
  f.writerow(firstline)

  for dat in data:
    orgn = dat[0]
    dstn = dat[1]
    d = dat[2]

    line1 = []
    line1.append(orgn)
    line1.append(dstn)
    line1.append('C')

    line2 = []
    line2.append(orgn)
    line2.append(dstn)
    line2.append('U')
    
    for e in d:
      line1.append(e[0])
      line1.append(e[2])
      line2.append(e[1])
      line2.append(e[2])

    f.writerow(line1)
    f.writerow(line2)
    
  return csv_fname

def get_text(market):
  txt  = "Monthly RMP forecast follow-up report is attached.\n\n"
  txt += "Two files: printable version (PDF) and data (CSV).\n\n\n"
  txt += "Regards,\nFedor"
  return txt

def send_fe_report():
  # Generating report
  curr_month = datetime.now().month
  curr_year = datetime.now().year

  month = curr_month
  year = curr_year

  data = []
  months = []

  for owner in mo.get_owners():
    for market in mo.get_markets(owner=owner):

      from_month = curr_month
      from_year = curr_year

      if market.strip() == '':
        continue

      dat = []

      orgn = 'HEL'
      dstn = market

      dat.append(orgn)
      dat.append(dstn)

      da = []
      for i in range(1,13):

        from_month += 1
        if from_month == 13:
          from_month = 1
          from_year += 1

        to_month = from_month + 1
        to_year = from_year
      
        if to_month == 13:
          to_month = 1
          to_year += 1

        # FIXME: shit coding detected!
        if len(months) < 12:
          dfrom_m_s = str(from_year)+'-'+str(from_month).zfill(2)
          months.append(dfrom_m_s)
      
        dfrom_s = str(from_year)+'-'+str(from_month).zfill(2)+'-'+str(1).zfill(2)
        dto_s = str(to_year)+'-'+str(to_month).zfill(2)+'-'+str(1).zfill(2)

        ret = val_err_avg(orgn,dstn,dfrom_s,dto_s)
        ks = ret.keys()

        cons_dmd = []
        ach_dmd = []
        err = []
        for k in ks:
          cons_dmd.append(ret[k][0])
          ach_dmd.append(ret[k][1])
          err.append(ret[k][2])

        cons_dmd = sum(cons_dmd) #int(np.mean(dmd))
        ach_dmd = sum(ach_dmd)
        err2 = [e**2 for e in err]
        err = int(sqrt(sum(err2)))

        da.append([cons_dmd,ach_dmd,err])
      
      dat.append(da)
      data.append(dat)

  # Generate pdf
  pdf_file = generate_pdf(months,data)
  csv_file = generate_csv(months,data)

  # Sending email
  es = EmailSender('157.200.13.44',25)
  sbj = 'RMP forecast follow-up'
  txt = get_text(market)

  es.send_multipart('fedor.nikitin@finnair.com','thien.le@finnair.com',subj=sbj,text=txt,files=[pdf_file,csv_file])
  es.send_multipart('fedor.nikitin@finnair.com','fedor.nikitin@finnair.com',subj=sbj,text=txt,files=[pdf_file,csv_file])

if __name__ == '__main__':
  send_fe_report()


