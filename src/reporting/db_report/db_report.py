import os
import sys
import ConfigParser
from datetime import datetime,date,timedelta, time
from time import mktime
import matplotlib
from matplotlib import pyplot as plt
from pyvirtualdisplay import Display

from emailsender.email_sender import EmailSender
from marketowners.marketowners import *

from django.conf import settings
from django.template import Context, loader

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))
ob_data_path = config.get('PATHS','ob_data')

from crm_case import CRMCase
from dt_func import prev_weekday

abspath = os.path.abspath(__file__)
abspaths = abspath.split('/')
abspath = '/'.join(abspaths[:len(abspaths)-1])

#################
#
#  TEST VERSION
#
#################
IS_TEST = True

if IS_TEST:
  NUM_WEEKS_BACK = 60
else:
  NUM_WEEKS_BACK = 60

try:
  settings.configure(DEBUG=True,TEMPLATE_DEBUG=True,TEMPLATE_DIRS=[abspath])
except:
  pass

matplotlib.rcParams.update({'font.size':8})

if __name__ == '__main__':
  dtnow = datetime.now()

  res = {}

  # Find the date of last Sunday
  dto = prev_weekday(dtnow,7)
  dfrom = dto - timedelta(days=6)

  dfrom = datetime.combine(dfrom.date(),time(0,0,0))
  dto = datetime.combine(dto.date(),time(23,59,59))

  # Calculate weekly follow-up (60 weeks back)
  for i in range(NUM_WEEKS_BACK):
    print 'Week number: ',i
    year,weeknum,weekday = dto.isocalendar()
    k = str(year)+'/'+str(weeknum).zfill(2)
    tot_num,tot_amt,db_cases = CRMCase.get_db_cases(dfrom,dto)
    if i == 0:
      cur_dfrom = dfrom
      cur_dto = dto
      cur_tot_num = tot_num
      cur_tot_amt = tot_amt
      cur_db_cases = db_cases
    res[k] = [tot_num,tot_amt]
    dfrom = dfrom - timedelta(days=7)
    dto = dto - timedelta(days=7)

  keys = res.keys()
  keys.sort()

  tstamp = int(mktime(datetime.now().timetuple()))
  fname_prefix = '/home/rmpuser/rw.static/pic/'

  fname_db_pax = 'ob_report_pax_'+str(tstamp)+'.png'
  fname_db_comp = 'ob_report_comp_'+str(tstamp)+'.png'

  #disp = Display(visible=0)
  #disp.start()

  print res

  plt.figure(figsize=(9,4))
  plt.plot([res[e][0] for e in keys])
  plt.title('Number of DB passengers')
  plt.xticks(range(len(keys)),keys,rotation='vertical')
  plt.subplots_adjust(left=0.05,bottom=0.15)
  plt.savefig(fname_prefix+fname_db_pax)

  plt.figure(figsize=(9,4))
  plt.plot([res[e][1] for e in keys])
  plt.title('DB compensation amount')
  plt.xticks(range(len(keys)),keys,rotation='vertical')
  plt.subplots_adjust(left=0.05,bottom=0.15)
  plt.savefig(fname_prefix+fname_db_comp)

  #disp.stop() 
 
  tmpl_fname = 'db_report.html'
  tmpl = loader.get_template(tmpl_fname)
  cntx = Context({'db_cases': cur_db_cases,
                  'tot_num': cur_tot_num,
                  'tot_amt': cur_tot_amt,
                  'fname_db_pax': fname_db_pax,
                  'fname_db_comp': fname_db_comp,
                  'dfrom': cur_dfrom.strftime('%Y-%m-%d'),
                  'dto': cur_dto.strftime('%Y-%m-%d')})
  html = tmpl.render(cntx)

  imgs = [fname_prefix+fname_db_pax,fname_prefix+fname_db_comp]

  # Sending email
  es = EmailSender('157.200.13.44',25)
  sbj = 'DB cases '+cur_dfrom.strftime('%Y-%m-%d')+' --- '+cur_dto.strftime('%Y-%m-%d')
  
  if IS_TEST:
    es.send_html_images('fedor.nikitin@finnair.com','fedor.nikitin@finnair.com',subj=sbj,html=html,imgs=imgs)
  else:
    for owner in get_owners():
      es.send_html_images('fedor.nikitin@finnair.com',owner+'@finnair.com',subj=sbj,html=html,imgs=imgs)
    es.send_html_images('fedor.nikitin@finnair.com','fedor.nikitin@finnair.com',subj=sbj,html=html,imgs=imgs)
    es.send_html_images('fedor.nikitin@finnair.com','satu.savolainen@finnair.com',subj=sbj,html=html,imgs=imgs)


