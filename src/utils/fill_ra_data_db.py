import os
import re
import glob
import sys
import csv
import shlex
import ConfigParser

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)
sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector
from dt_func import date_str_to_date
from datetime import date,timedelta

def get_modulo_diff(dfrom_dow,dow):
    for diff in range(7):
        if (dfrom_dow + diff)%7 == dow:
            return diff

if __name__ == '__main__':

    path = 'ra_data/'
    curs = dbConnector.get_or_curs()
    conn = dbConnector.get_or_conn()
    
    for infile in glob.glob(os.path.join(path,'*.txt')):
        print 'file: ', infile
        from_s,to_s = re.findall('\d+',infile)
        dfrom = date_str_to_date(from_s.strip())
        dto = date_str_to_date(to_s.strip())
        
        csv_reader = csv.reader(open(infile,'rb'))
        i = 0
        for row in csv_reader:
            if len(row) == 0:
                continue
            els = shlex.split(row[0])

            i += 1

            if len(els) != 23:
                print i 
                continue        

            code                   = els[0]
            trip_orgn              = els[1]
            trip_dstn              = els[2]
            cls                    = els[3]
            poc                    = els[4]
            pos                    = els[5]
            in_out                 = els[6]
            fare_basis_group       = els[7]
            fare_basis_code        = els[8]
            market_fare_ind        = els[9]
            total_fare             = els[10]
            total_net_net_fare     = els[11]
            pax_cnt                = els[12]
            cur_code               = els[13]
            online_orgn            = els[14]
            online_dstn            = els[15]
            tot_client_rev         = els[16]
            tot_client_net_net_rev = els[17]
            oac                    = els[18]
            flag                   = els[19]
            path                   = els[20]
            dow                    = els[21]
            dep_time               = els[22]
            dep_date               = 'XXXX-MM-DD'

            dfrom_dow = date.weekday(dfrom)
            dto_dow   = date.weekday(dto)

            dep_date = dfrom + timedelta(days=get_modulo_diff(dfrom_dow,int(dow)))

            #print dfrom,dto
            #print dow,dfrom_dow,dto_dow,':',dep_date
            #print '--------------------'

            q = "INSERT INTO ra_data_ds_old\
                 (code,trip_orgn,trip_dstn,cls,poc,pos,in_out,\
                  fare_basis_group,fare_basis_code,market_fare_ind,\
                  total_fare,total_net_net_fare,pax_cnt,cur_code,\
                  online_orgn,online_dstn,tot_client_rev,\
                  tot_client_net_net_rev,oac,flag,path,dow,dep_time,\
                  dep_date) VALUES (\
                  '" + code + "',\
                  '" + trip_orgn + "',\
                  '" + trip_dstn + "',\
                  '" + cls + "',\
                  '" + poc + "',\
                  '" + pos + "',\
                  '" + in_out + "',\
                  '" + fare_basis_group + "',\
                  '" + fare_basis_code + "',\
                  '" + market_fare_ind + "',\
                   " + total_fare + ",\
                   " + total_net_net_fare + ",\
                   " + pax_cnt + ",\
                  '" + cur_code + "',\
                  '" + online_orgn + "',\
                  '" + online_dstn + "',\
                   " + tot_client_rev + ",\
                   " + tot_client_net_net_rev + ",\
                  '" + oac + "',\
                  '" + flag + "',\
                  '" + path + "',\
                  '" + dow + "',\
                  '" + dep_time + "',\
                  '" + dep_date.strftime('%Y-%m-%d') + "')"

            #print q
            curs.execute(q)
            
        conn.commit()





