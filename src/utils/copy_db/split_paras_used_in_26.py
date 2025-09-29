import os
import sys
from datetime import date
import ConfigParser

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)
sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector
from cls import *

if __name__ == '__main__':

    curs = dbConnector.get_or_curs()

    for cls in get_clss_():

        if cls is None:
            continue
        
        fname = 'cls_' + cls + '.sql'
        f = open(fname,'w')

        # Copy entries for one class
        q = "SELECT fst_tkt,\
                    flightdate,\
                    depairport,\
                    arrairport,\
                    carrier,\
                    pax,\
                    bkg_cre_dt_tm,\
                    bookingclass\
             FROM paras_used\
             WHERE bookingclass = '" + cls + "'"
        curs.execute(q)
        row = curs.fetchone()
        while row is not None:
            fst_tkt       = row[0]
            flightdate    = row[1].strftime('%Y-%m-%d')
            depairport    = row[2]
            arrairport    = row[3]
            carrier       = 'AY'
            pax           = row[5]
            if row[6] is None:
                bkg_cre_dt_tm = '1970-01-01'
            else:
                bkg_cre_dt_tm = row[6].strftime('%Y-%m-%d')
            if bkg_cre_dt_tm is None:
                bkg_cre_dt_tm = '1970-01-01'
            bookingclass  = row[7]
            line = fst_tkt + \
                   flightdate + "," + \
                   depairport + "," + \
                   arrairport + "," + \
                   carrier + "," + \
                   str(pax) + "," + \
                   str(bkg_cre_dt_tm) + "," + \
                   str(bookingclass)
        
            sub_q = "INSERT INTO paras_used_" + cls.lower() + "\
                     (fst_tkt,flightdate,depairport,arrairport,\
                      carrier,pax,bkg_cre_dt_tm,bookingclass)\
                      VALUES\
                      ('" + fst_tkt + "',\
                       DATE('" + flightdate + "'),\
                       '" + depairport + "',\
                       '" + arrairport + "',\
                       '" + carrier + "',\
                        " + str(pax) + ",\
                       DATE('" + str(bkg_cre_dt_tm) + "'),\
                       '" + str(bookingclass) + "')"
            f.write(sub_q + '\n')
            row = curs.fetchone()
        f.close()
        

        
