import os
import smtplib
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders
import ConfigParser

class EmailSender:

    def send_quick(self,subj,text):
        msg = MIMEText(text)
        msg['Subject'] = subj
        msg['From'] = 'rerouting@finnair.com'
        msg['To'] = 'fedor.nikitin@finnair.com'
        
        s = smtplib.SMTP(self.server,self.port)
        s.sendmail('rerouting@finnair.com','fedor.nikitin@finnair.com',msg.as_string())  

    def __init__(self):
        config = ConfigParser.RawConfigParser()
        path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
        path_to_config = os.path.normpath(path_to_config)
        config.read(path_to_config)

        self.prot = 'SMTP'
        self.server = config.get('SMTP','server')
        self.port = config.get('SMTP','port')
        self.text = ''
        self.subject = ''

    def compose(self,typ,info,obj = None):

        # FIXME: use template system for reply messgages
        # FIXME: compose of messages should be not in this class (?)

        if typ == 'ESP':
            self.text = 'Number of observations: ' + str(info[1][0]) + '\n'
            self.text = self.text + 'Smoothing constant: ' + str(info[1][1]) + '\n'   
            self.text = self.text + '\n\n'
            self.text = self.text + '################# Your message #####################\n\n'
            self.text = self.text + str(info[0])
            self.subject = 'Re: ESP'

        elif typ == 'ESP ERR':
            self.text = 'The following line is not validated:\n\n'
            self.text = self.text + str(info[1])
            self.text = self.text + '\n\n'
            self.text = self.text + '################# Your message #####################\n\n'
            self.text = self.text + str(info[0])
            self.subject = 'Re: ESP'

        elif typ == 'DEP':
            self.text =             'J compartment\n'
            self.text = self.text + '-------------\n'
            self.text = self.text + '# of bookings: ' + \
                                      str(obj.get_num_booked('J')) + '\n'
            self.text = self.text + '# of confirmed bookings: ' + \
                                      str(obj.get_num_conf_booked('J')) + '\n'
            self.text = self.text + '# of unconfirmed bookings: ' + \
                                      str(obj.get_num_unconf_booked('J')) + '\n'
            self.text = self.text + '# of confirmed survived bookings: ' + \
                                      str(obj.get_num_conf_surv_booked('J')) + '\n'
            self.text = self.text + '# of unconfirmed survived bookings: ' + \
                                      str(obj.get_num_unconf_surv_booked('J')) + '\n'
            self.text = self.text + '# of confirmed survived checked-in bookings: ' + \
                                      str(obj.get_num_conf_surv_checkin_booked('J')) + '\n'
            self.text = self.text + '# of unconfirmed survived checked-in bookings: ' + \
                                      str(obj.get_num_unconf_surv_checkin_booked('J')) + '\n'
            self.text = self.text + '# of confirmed survived checked-in boarded bookings: ' + \
                                      str(obj.get_num_conf_surv_checkin_brd_booked('J')) + '\n'
            self.text = self.text + '# of unconfirmed survived checked-in boarded bookings: ' + \
                                      str(obj.get_num_unconf_surv_checkin_brd_booked('J')) + '\n'
            self.text = self.text + 'PROS booked: ' + \
                                      str(obj.get_pros_booked('J')) + '\n'
            self.text = self.text + 'PROS out: ' + \
                                      str(obj.get_pros_out('J')) + '\n'
            self.text = self.text + 'PROS noshow: ' + \
                                      str(obj.get_pros_noshow('J')) + '\n'
            self.text = self.text + 'PROS upgrade in: ' + \
                                      str(obj.get_pros_upgrade('J')) + '\n'
            self.text = self.text + 'PROS weighted avg fare: ' + \
                                      str(obj.get_weighted_avg_fare('J')) + '\n'

            self.text = self.text + '\n\n'

            self.text = self.text + 'Y compartment\n'
            self.text = self.text + '-------------\n'
            self.text = self.text + '# of bookings: ' + \
                                      str(obj.get_num_booked('Y')) + '\n'
            self.text = self.text + '# of confirmed bookings: ' + \
                                      str(obj.get_num_conf_booked('Y')) + '\n'
            self.text = self.text + '# of unconfirmed bookings: ' + \
                                      str(obj.get_num_unconf_booked('Y')) + '\n'
            self.text = self.text + '# of confirmed survived bookings: ' + \
                                      str(obj.get_num_conf_surv_booked('Y')) + '\n'
            self.text = self.text + '# of unconfirmed survived bookings: ' + \
                                      str(obj.get_num_unconf_surv_booked('Y')) + '\n'
            self.text = self.text + '# of confirmed survived checked-in bookings: ' + \
                                      str(obj.get_num_conf_surv_checkin_booked('Y')) + '\n'
            self.text = self.text + '# of unconfirmed survived checked-in bookings: ' + \
                                      str(obj.get_num_unconf_surv_checkin_booked('Y')) + '\n'
            self.text = self.text + '# of confirmed survived checked-in boarded bookings: ' + \
                                      str(obj.get_num_conf_surv_checkin_brd_booked('Y')) + '\n'
            self.text = self.text + '# of unconfirmed survived checked-in boarded bookings: ' + \
                                      str(obj.get_num_unconf_surv_checkin_brd_booked('Y')) + '\n'
            self.text = self.text + 'PROS booked: ' + \
                                      str(obj.get_pros_booked('Y')) + '\n'
            self.text = self.text + 'PROS out: ' + \
                                      str(obj.get_pros_out('Y')) + '\n'
            self.text = self.text + 'PROS noshow: ' + \
                                      str(obj.get_pros_noshow('Y')) + '\n'
            self.text = self.text + 'PROS upgrade out: ' + \
                                      str(obj.get_pros_upgrade('Y')) + '\n'
            self.text = self.text + 'PROS weighted avg fare: ' + \
                                      str(obj.get_weighted_avg_fare('Y')) + '\n'

            self.text = self.text + '\n\n'
            self.text = self.text + '################### Your message #####################\n\n'
            self.text = self.text + str(info[0])

            self.subject = 'Re: DEP'

        elif typ == 'DEP ERR':
            self.text = 'The following line is not validate:\n\n'
            self.text = self.text + str(info[1])
            self.text = self.text + '\n\n'
            self.text = self.text + '################# Your message #####################\n\n'
            self.text = self.text + str(info[0])
            self.subject = 'Re: DEP'

        elif typ == 'DBC':
            avg_yield_j = obj.get_avg_yield('J')
            avg_prime_yield_j = obj.get_avg_prime_yield('J')
            if avg_prime_yield_j == 0:
                cost_factor_spoilage_j = 'NA'
            else:
                cost_factor_spoilage_j = float(avg_yield_j)/avg_prime_yield_j
            db_costs_j = obj.get_mrgnl_db_costs('J')
            db_cost_factor_j = obj.get_db_cost_factor('J')

            self.text =             'J compartment\n' 
            self.text = self.text + '-------------\n'
            self.text = self.text + 'Average yield: ' + str(avg_yield_j) + '\n'
            self.text = self.text + 'Average prime yield: ' + str(avg_prime_yield_j) + '\n'
            self.text = self.text + 'Spoilage cost factor: ' + str(cost_factor_spoilage_j) + '\n'
            self.text = self.text + 'Denied boarding costs: ' + str(db_costs_j) + '\n'
            self.text = self.text + 'DB cost factor: ' + str(db_cost_factor_j) + '\n'

            self.text = self.text + '\n\n'

            avg_yield_y = obj.get_avg_yield('Y')
            avg_prime_yield_y = obj.get_avg_prime_yield('Y')
            if avg_prime_yield_y == 0:
                cost_factor_spoilage_y = 'NA'
            else:
                cost_factor_spoilage_y = float(avg_yield_y)/avg_prime_yield_y
            db_costs_y = obj.get_mrgnl_db_costs('Y')
            db_cost_factor_y = obj.get_db_cost_factor('Y')

            self.text = self.text + 'Y compartment\n'
            self.text = self.text + '-------------\n'
            self.text = self.text + 'Average yield: ' + str(avg_yield_y) + '\n'
            self.text = self.text + 'Average prime yield: ' + str(avg_prime_yield_y) + '\n'
            self.text = self.text + 'Spoilage cost factor: ' + str(cost_factor_spoilage_y) + '\n'
            self.text = self.text + 'Denied boarding costs: ' + str(db_costs_y) + '\n'
            self.text = self.text + 'DB cost factor: ' + str(db_cost_factor_y) + '\n'

            self.text = self.text + '\n\n'

            self.text = self.text + '################# Your message #####################\n\n'
            self.text = self.text + str(info[0])

            self.subject = 'Re: DBC'       

        elif typ == 'DBC ERR':
            self.text = 'The following line is not validate:\n\n'
            self.text = self.text + str(info[1])
            self.text = self.text + '\n\n'
            self.text = self.text + '################# Your message #####################\n\n'
            self.text = self.text + str(info[0])

            self.subject = 'Re: DBC'

        elif typ == 'SBJCT ERR':
            self.txt = 'Unknown subjct'
            self.subject = 'SBJCT ERR'
        else:
            pass

    def send_multipart(self,to,files):
        frm = 'fedor.nikitin@finnair.com'

        msg = MIMEMultipart()
        msg['From'] = frm
        msg['To'] = to
        msg['Subject'] = 'AY prices'
        #msg['CC'] = 'fedor.nikitin@finnair.com'

        msg.attach(MIMEText('This is the test version...'))
        for f in files:
            part = MIMEBase('application','octet-stream')
            part.set_payload(open(f,'rb').read())
            Encoders.encode_base64(part)       
            part.add_header("Content-Disposition","attachment; filename=%s" % os.path.basename(f))
            msg.attach(part)
 
        s = smtplib.SMTP(self.server,self.port)
        s.ehlo()
        s.starttls()
        s.ehlo
        s.login('u96.002@gmail.com','10ltymgj[jlf')
        s.sendmail(frm,to,msg.as_string()) 
        s.close()

    def send(self,to):

        to_l = to.split('@')

        if len(to_l) > 1:
            if to_l[1].strip().strip('>').lower() != 'finnair.com':
           
                return 1 
        else:
           to = 'fedor.nikitin@finnair.com'

        frm = 'rerouting@finnair.com'

        msg = MIMEText(self.text)
        msg['Subject'] = self.subject
        msg['From'] = frm
        msg['To'] = to
        msg['CC'] = 'fedor.nikitin@finnair.com'  

        s = smtplib.SMTP(self.server,self.port)
        s.sendmail(frm,to,msg.as_string())

        return 0 
