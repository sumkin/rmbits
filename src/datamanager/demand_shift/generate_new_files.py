import os
import sys
import csv
import glob
import ConfigParser

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from dt_func import date_str_to_date
from db_connector import *

ra_data_fldr = config.get('PATHS','ra_data')
new_ra_data_fldr = config.get('PATHS','new_ra_data')

if __name__ == '__main__':

    curs = dbConnector.get_or_curs()
    
    for infile in glob.glob(ra_data_fldr + '/*'):
        fname_parts = infile.split('\\')
        fname = fname_parts[len(fname_parts)-1]
        fname_parts = fname.split('.')
        dates = fname_parts[2]
        dfrom_s,dto_s = dates.split('-')

        dfrom = date_str_to_date(dfrom_s)
        dto = date_str_to_date(dto_s)

        print dfrom.strftime('%d.%m.%Y'),dto.strftime('%d.%m.%Y')
        
        writer = open(new_ra_data_fldr+'\\'+fname,'wb')
        writer.write('CRG '+dfrom_s+' '+dto_s+' '+dto_s+'\n')
        writer.write('\n')

        q = "SELECT code,trip_orgn,trip_dstn,cls,\
                    poc,in_out,fare_basis_group,\
                    market_fare_ind,total_fare,\
                    total_net_net_fare,SUM(pax_cnt),\
                    cur_code,online_orgn,online_dstn,\
                    tot_client_rev,tot_client_net_net_rev,\
                    oac,flag,path,dow,dep_time,\
                    dep_date,fare_basis_code,pos\
             FROM ra_data_ds_new\
             WHERE dep_date >= '"+dfrom.strftime('%Y-%m-%d')+"' AND\
                   dep_date <= '"+dto.strftime('%Y-%m-%d')+"'\
             GROUP BY code,trip_orgn,trip_dstn,cls,\
                      poc,in_out,fare_basis_group,\
                      market_fare_ind,total_fare,\
                      total_net_net_fare,\
                      cur_code,online_orgn,online_dstn,\
                      tot_client_rev,tot_client_net_net_rev,\
                      oac,flag,path,dow,dep_time,\
                      dep_date,fare_basis_code,pos"
        curs.execute(q)
        row = curs.fetchone()
        while row is not None:
            code                   = row[0]
            trip_orgn              = row[1]
            trip_dstn              = row[2]
            cls                    = row[3]
            poc                    = row[4]
            in_out                 = row[5]
            fare_basis_group       = row[6]
            market_fare_ind        = row[7]
            total_fare             = '%.2f' % row[8] 
            total_net_net_fare     = '%.2f' % row[9]
            pax_cnt                = row[10]
            cur_code               = row[11]
            online_orgn            = row[12]
            online_dstn            = row[13]
            tot_client_rev         = '%.2f' % row[14]
            tot_client_net_net_rev = '%.2f' % row[15]
            oac                    = row[16]
            flag                   = row[17]
            path                   = row[18]
            dow                    = row[19]
            dep_time               = row[20]
            dep_date               = row[21]
            fare_basis_code        = row[22]
            pos                    = row[23]

            if path.find("\"") == -1:
                path = "\"" + path.strip() + "\""
            
            line = code+' '+trip_orgn+' '+trip_dstn+' '+cls+' '+poc+' '+pos+' '+\
                   in_out+' '+fare_basis_group+' '+fare_basis_code+' '+market_fare_ind+' '+\
                   total_fare+' '+total_net_net_fare+' '+str(pax_cnt)+' '+\
                   cur_code+' '+online_orgn+' '+online_dstn+' '+\
                   tot_client_rev+' '+tot_client_net_net_rev+' '+\
                   oac+' '+flag+' '+path+' '+str(dow)+' '+dep_time
            
            writer.write(line+'\n')
            
            row = curs.fetchone()

    




