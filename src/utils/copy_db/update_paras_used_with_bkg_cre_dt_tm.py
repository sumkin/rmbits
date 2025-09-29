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

if __name__ == '__main__':

    num_per_fetch = 10000
    fetch_num = 0
    num = 0
    curs = dbConnector.get_or_curs()

    while True:
        q = "SELECT bkg_cre_dt_tm,primary_nbr\
             FROM ads_bkg WHERE primary_nbr IS NOT NULL AND bkg_cre_dt_tm IS NOT NULL\
             LIMIT " + str(fetch_num * num_per_fetch) + "," + str(num_per_fetch)
        #print q
        curs.execute(q)
        rows = curs.fetchall()
        if len(rows) == 0:
            break
        for row in rows:
            bkg_cre_dt_tm = row[0]
            primary_nbr = row[1]
            q = "UPDATE paras_used\
                 SET bkg_cre_dt_tm = DATE('"+bkg_cre_dt_tm.strftime('%Y-%m-%d')+"')\
                 WHERE fst_tkt = '" + primary_nbr + "'"
            curs.execute(q)
            num += 1
        print 'Fetch number: ', fetch_num, ' (', num, ')'
        dbConnector.get_or_conn().commit()
        fetch_num += 1
        
    print '\n'
    print num, ' entries have been added'





















