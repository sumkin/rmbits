import sys
import os
import logging
import ConfigParser
from datetime import datetime,timedelta
import smtplib
from email.mime.text import MIMEText

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','forecaster'))
sys.path.append(config.get('PATHS','datamanager'))
LOG_PATH  = config.get('PATHS','logs')
DATA_PATH = config.get('PATHS','data')

from flight import *

from flight import *

flights = flight.get_managed_flights()

#flights = [['HEL','HKG','00069'],['HKG','HEL','00070']]

dto   = datetime.now()
dfrom = dto - timedelta(days=100)

txt = ""
for e in flights:
  try:
    orgn = e[0]
    dstn = e[1]
    flnbr = e[2]
    print orgn,dstn,flnbr
    fl = flight(orgn,dstn,flnbr,dfrom,dto)

    try:
      avg_yield_j = fl.get_avg_yield('J')
      avg_prime_yield_j = fl.get_avg_prime_yield('J')
    except:
      continue
    if avg_prime_yield_j == 0:
        cost_factor_spoilage_j = 'NA'
    else:
        cost_factor_spoilage_j = float(avg_yield_j)/avg_prime_yield_j
    db_costs_j = fl.get_mrgnl_db_costs('J')
    db_cost_factor_j = fl.get_db_cost_factor('J')

    txt += orgn+"-"+dstn+"-"+flnbr+"\n"
    txt += "#############\n"
    txt += "J compartment\n"
    txt += "-------------\n"
    txt += "Average yield: "+str(avg_yield_j)+"\n"
    txt += "Average prime yield: "+str(avg_prime_yield_j)+"\n"
    txt += "Spoilage cost factor: "+str(cost_factor_spoilage_j)+"\n"
    txt += "Denied boarding costs: "+str(db_costs_j)+"\n"
    txt += "DB cost factor: "+str(db_cost_factor_j)+"\n"
    
    txt += "\n\n"

    avg_yield_y = fl.get_avg_yield('Y')
    avg_prime_yield_y = fl.get_avg_prime_yield('Y')
    if avg_prime_yield_y == 0:
        cost_factor_spoilage_y = 'NA'
    else:
        cost_factor_spoilage_y = float(avg_yield_y)/avg_prime_yield_y
    db_costs_y = fl.get_mrgnl_db_costs('Y')
    db_cost_factor_y = fl.get_db_cost_factor('Y')

    txt += "Y compartment\n"
    txt += "--------------\n"
    txt += "Average yield: "+str(avg_yield_y)+"\n"
    txt += "Average prime yield: "+str(avg_prime_yield_y)+"\n"
    txt += "Spoilage cost factor: "+str(cost_factor_spoilage_y)+"\n"
    txt += "Denied boarding costs: "+str(db_costs_y)+"\n"
    txt += "DB cost factor: "+str(db_cost_factor_y)+"\n"
    txt += "\n\n"
  except:
    pass
print txt

smtp_server = config.get('SMTP','server')
smtp_port = config.get('SMTP','port')

frm = 'fedor.nikitin@finnair.com'
to = 'fedor.nikitin@finnair.com'
msg = MIMEText(txt)
msg['Subject'] = 'Denied boarding costs'
msg['From'] = frm
msg['To'] = 'fedor.nikitin@finnair.com'

s = smtplib.SMTP(smtp_server,smtp_port)
s.sendmail(frm,to,msg.as_string())












    









    
        
