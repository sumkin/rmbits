import sys
import os
import logging
import ConfigParser

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','forecaster'))
sys.path.append(config.get('PATHS','datamanager'))
LOG_PATH  = config.get('PATHS','logs')
DATA_PATH = config.get('PATHS','data')

from email_receiver import *
from email_sender import *
from email_msg import *
from email_esp_msg import *
from email_departure_msg import *
from email_dbc_msg import *

from esp_model import *
from departure import departure
from flight import flight

# init logging
logger = logging.getLogger()
hdlr = logging.FileHandler(LOG_PATH + '/email_handler.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

file_lock_name = DATA_PATH+'/email_handler.lock'
if os.path.exists(file_lock_name):
  logger.info('Processing going on...')
  exit()
else:
  f = open(file_lock_name,'w')
  f.write('lock')
  f.close()

#########################################################
#
#                   MAIN FUNCTION
#
#########################################################

try:
  er = EmailReceiver()
  if not er.login():
    logger.info('Failed to login email server')
except:
  es = EmailSender()
  es.send_quick('login IMAP error', str(sys.exc_info()))
  os.remove(file_lock_name)
  exit()

logger.info('Login in IMAP')

for email_str in er.get_unseen_mails():

    if emailMsg.get_type(email_str) == 'ESP':

        eem = emailESPMsg(email_str)
        logger.info('ESP msg from ' + eem.get_sender() + ' is received')

        try:
          res_valid = eem.validate()
        except:
          es = EmailSender()
          es.send_quick('email validation error', str(sys.exc_info()))
          os.remove(file_lock_name)
          exit()

        if res_valid[0]:

            logger.info('Msg valid, get esp params')
            try:
              lag,alpha = get_esp_params(eem.get_flights(),\
                                         eem.get_dows(),\
                                         eem.get_split_history(),
                                         eem.get_pool_ids(),
                                         eem.get_clss()) 
            except:
              es = EmailSender()
              es.send_quick('Get ESP param error', str(sys.exc_info()))
              os.remove(file_lock_name)
              exit()

            info = [eem.get_content(),[lag,alpha]]

            try:
              es = EmailSender()
              es.compose('ESP',info)
              logger.info('Reply is composed')
              if es.send(eem.get_sender()) == 0:
                logger.info('Reply is sent')
              else:
                logger.info('Reply is not sent (not finnair email)')        
            except:
              es = EmailSender()
              es.send_quick('Sending reply error', str(sys.exc_info()))
              os.remove(file_lock_name)
              exit()
        else:

            try:
              logger.info('Msg is not valid')
              info = [eem.get_content(),[res_valid[1]]]
              es = EmailSender()
              es.compose('ESP ERR',info)
              logger.info('Reply is composed')
              if es.send(eem.get_sender()) == 0:
                logger.info('Reply is sent')
              else:
                logger.info('Reply is not sent (not finnair email)')
            except:
              es = EmailSender()
              es.send_quick('Sending reply error', str(sys.exc_info()))
              os.remove(file_lock_name)
              exit()

    elif emailMsg.get_type(email_str) == 'DEP':

        edm = emailDepartureMsg(email_str)
        logger.info('DEP msg from ' + edm.get_sender() + ' is received')
        res_valid = edm.validate()

        if res_valid[0]:

            logger.info('Msg valid, get departure')
            flight_s = edm.get_flight()
            info = [edm.get_content(),[]]
            dep = departure(flight_s[0],flight_s[1],flight_s[2],edm.get_date())
            es = EmailSender()
            es.compose('DEP',info,dep)
            logger.info('Reply is composed')
            if  es.send(edm.get_sender()) == 0:
                logger.info('Reply is sent') 
            else:
                logger.info('Reply is not sent (not finnair email)')
        else:

            logger.info('Msg is not valid')
            flight_s = edm.get_flight()
            info = [edm.get_content(),[res_valid[1]]]
            es = EmailSender()
            dep = departure(flight_s[0],flight_s[1],flight_s[2],edm.get_date())
            es.compose('DEP ERR',info,dep)
            logger.info('Msg is composed')
            if es.send(edm.get_sender()) == 0:
                logger.info('Msg is sent')
            else:
                logger.info('Reply is not sent (not finnair email)')
    
    elif emailMsg.get_type(email_str) == 'DBC':

        edbm = emailDBCMsg(email_str)   
        logger.info('DBC msg from ' + edbm.get_sender() + ' is received')
        res_valid = edbm.validate()

        if res_valid[0]:

            logger.info('Msg valid')
            flight_s = edbm.get_flight()
            info = [edbm.get_content(),[]]
            fl = flight(flight_s[0],flight_s[1],flight_s[2],edbm.get_dfrom(),edbm.get_dto())
            es = EmailSender()
            es.compose('DBC',info,fl)
            logger.info('Reply is composed')
            if es.send(edbm.get_sender()) == 0:
                logger.info('Reply is sent')
            else:
                logger.info('Reply is not sent (not finnair email)')

        else:

            logger.info('Msg is not valid')
            flight_s = edbm.get_flight()
            info = [edbm.get_content(),[res_valid[1]]]
            es = EmailSender()
            es.compose('DBC ERR',info,None)
            logger.info('Reply is composed')
            if es.send(edbm.get_sender()) == 0:
                logger.info('Reply is sent')
            else:
                logger.info('Reply is not sent (not finnair email)')

    else:

        es = EmailSender()
        es.compose('SBJCT ERR',None,None)
        logger.info('Reply is composed')
        if es.send('') == 0:
            logger.info('Unknown subject: ' + emailMsg.get_type(email_str))
        else:
            logger.info('Reply is not sent (not finnair email)')

    # FIXME: some memory leaks occur that is why we exit here
    # hoping that other emails will be processed on the next
    # run    
    break

try:
  logger.info('\n\n')
  os.remove(file_lock_name)
except:
  es = EmailSender()
  es.send_quick('File lock removal error', str(sys.exc_info()))
  exit()







