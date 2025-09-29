import os
import sys
import ConfigParser
from apscheduler.scheduler import Scheduler
from time import sleep
from fe_report.send_fe_report import send_fe_report
from fa_report.send_fa_report import send_fa_report

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','emailui'))

from email_sender import EmailSender

# Start the scheduler
sched = Scheduler()
sched.start()

def run_fa_report():
  
  # Inform that reporting started
  es = EmailSender()
  sbj = 'Forecast accuracy report for RRMs started'
  txt = ''
  es.send_multipart('fedor.nikitin@finnair.com',[],text=txt,subject=sbj)
  
  send_fa_report()

  # Inform that reporting ended
  es = EmailSender()
  sbj = 'Forecast accuracy report for RRMs ended'
  txt = ''
  es.send_multipart('fedor.nikitin@finnair.com',[],text=txt,subject=sbj)
  
def run_fe_report():

  # Inform forecast accuracy report for RM
  es = EmailSender()
  sbj = 'Forecast accuracy report for RM started'
  txt = ''
  es.send_multipart('fedor.nikitin@finnair.com',[],text=txt,subject=sbj)
  
  send_fe_report()

  # Inform forecast accuracy report for RM
  es = EmailSender()
  sbj = 'Forecast accuracy report for RM ended'
  txt = ''
  es.send_multipart('fedor.nikitin@finnair.com',[],text=txt,subject=sbj)
  
if __name__ == '__main__':
  run_fe_report()
#  run_fa_report()
  
#sched.add_cron_job(run_fa_report,day='1',hour='11',minute='00')
#sched.add_cron_job(run_fe_report,day='2',hour='11',minute='00')

while True:
  sleep(1)
    
