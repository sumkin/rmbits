import os
import sys
import ConfigParser
import pickle
from time import sleep
import random

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from cls import get_clss_

from db_connector import dbConnector
from demand_shift_estimate import print_demand_shift_matrix

if __name__ == '__main__':
    curs = dbConnector.get_or_curs()
    conn = dbConnector.get_or_conn()

    NUM = 10000
    
    finnished = False
    num = 0
    while not finnished:
        q = "SELECT code,trip_orgn,trip_dstn,cls,\
                    poc,in_out,fare_basis_group,\
                    market_fare_ind,total_fare,\
                    total_net_net_fare,pax_cnt,\
                    cur_code,online_orgn,online_dstn,\
                    tot_client_rev,tot_client_net_net_rev,\
                    oac,flag,path,dow,dep_time,\
                    dep_date,fare_basis_code,pos\
             FROM ra_data_ds_old LIMIT " + str(num * NUM) + "," + str(NUM) + ";"
        curs.execute(q)
        if int(curs.rowcount) == 0:
            finnished = True
        num += 1
        rows = curs.fetchall()
        for row in rows:
            code                   = row[0]
            trip_orgn              = row[1]
            trip_dstn              = row[2]
            cls                    = row[3]
            poc                    = row[4]
            in_out                 = row[5]
            fare_basis_group       = row[6]
            market_fare_ind        = row[7]
            total_fare             = row[8]
            total_net_net_fare     = row[9]
            pax_cnt                = row[10]
            cur_code               = row[11]
            online_orgn            = row[12]
            online_dstn            = row[13]
            tot_client_rev         = row[14]
            tot_client_net_net_rev = row[15]
            oac                    = row[16]
            flag                   = row[17]
            path                   = row[18]
            dow                    = row[19]
            dep_time               = row[20]
            dep_date               = row[21]
            fare_basis_code        = row[22]
            pos                    = row[23]
            legs = path.split(' ')

            if len(legs) == 1:
                hops = legs[0].split('-')
                fname = hops[0] + '-' + hops[1] + '.pkl'
            elif len(legs) == 2:
                hops1 = legs[0].split('-')
                hops2 = legs[1].split('-')
                if hops1[1] == hops2[0]:
                    fname = hops1[0] + '-' + hops2[0] + '-' + hops2[1] + '.pkl'
            else:
                fname = None

            shift_cls = cls
            if fname is not None:
                pax_cnt_remained = pax_cnt
                try:
                    f = open('output/'+fname,'rb')
                    dsm = pickle.load(f)
                    for i in range(pax_cnt+1):
                        rv = random.uniform(0,1)
                        sum_val = 0
                        for sub_cls in get_clss_():
                            dsm_val = float(dsm[cls][sub_cls])
                            if dsm_val != 0.0:
                                if sum_val <= rv and rv <= sum_val+dsm_val:
                                    shift_cls = sub_cls
                                    break
                            sum_val += dsm_val

                        # Add entry to
                        q = "INSERT INTO ra_data_ds_new\
                        (code,trip_orgn,trip_dstn,cls,poc,pos,in_out,\
                        fare_basis_group,fare_basis_code,market_fare_ind,\
                        total_fare,total_net_net_fare,pax_cnt,cur_code,\
                        online_orgn,online_dstn,tot_client_rev,\
                        tot_client_net_net_rev,oac,flag,path,dow,dep_time,\
                        dep_date) VALUES (\
                        '" + code + "',\
                        '" + trip_orgn + "',\
                        '" + trip_dstn + "',\
                        '" + shift_cls + "',\
                        '" + poc + "',\
                        '" + pos + "',\
                        '" + in_out + "',\
                        '" + shift_cls + "',\
                        '" + fare_basis_code + "',\
                        '" + market_fare_ind + "',\
                        " + str(total_fare) + ",\
                        " + str(total_net_net_fare) + ",\
                        " + str(1) + ",\
                        '" + cur_code + "',\
                        '" + online_orgn + "',\
                        '" + online_dstn + "',\
                        " + str(tot_client_rev) + ",\
                        " + str(tot_client_net_net_rev) + ",\
                        '" + oac + "',\
                        '" + flag + "',\
                        '" + path + "',\
                        '" + str(dow) + "',\
                        '" + dep_time + "',\
                        '" + dep_date + "')"
                        curs.execute(q)
                        pax_cnt_remained -= 1
                        if pax_cnt_remained == 0:
                            break
                except:
                    print str(sys.exc_info())
                    # Add entry to
                    q = "INSERT INTO ra_data_ds_new\
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
                    " + str(total_fare) + ",\
                    " + str(total_net_net_fare) + ",\
                    " + str(pax_cnt_remained) + ",\
                    '" + cur_code + "',\
                    '" + online_orgn + "',\
                    '" + online_dstn + "',\
                    " + str(tot_client_rev) + ",\
                    " + str(tot_client_net_net_rev) + ",\
                    '" + oac + "',\
                    '" + flag + "',\
                    '" + path + "',\
                    '" + str(dow) + "',\
                    '" + dep_time + "',\
                    '" + dep_date + "')"
                    curs.execute(q)
            else:
                # entry should not be updated
                q = "INSERT INTO ra_data_ds_new\
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
                " + str(total_fare) + ",\
                " + str(total_net_net_fare) + ",\
                " + str(pax_cnt) + ",\
                '" + cur_code + "',\
                '" + online_orgn + "',\
                '" + online_dstn + "',\
                " + str(tot_client_rev) + ",\
                " + str(tot_client_net_net_rev) + ",\
                '" + oac + "',\
                '" + flag + "',\
                '" + path + "',\
                '" + str(dow) + "',\
                '" + dep_time + "',\
                '" + dep_date + "')"
                curs.execute(q)

        conn.commit()      
        print num,'x',NUM,' = ',int(num*NUM)
        
               
