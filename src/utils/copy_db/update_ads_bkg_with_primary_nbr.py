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

    curs = dbConnector.get_or_curs()
    q = "SELECT tkt_id,primary_nbr FROM ads_tkt"
    curs.execute(q)

    num = 0
    rows = curs.fetchall()
    for row in rows:
        tkt_id = row[0]
        primary_nbr = row[1]
        q = "UPDATE ads_bkg\
             SET primary_nbr = '" + primary_nbr + "'\
             WHERE bkg_tkt_id = " + str(tkt_id)
        curs.execute(q)
        num += 1
        print num
        if num % 100000 == 0:
            print '.',
            dbConnector.get_or_conn().commit()
        
    dbConnector.get_or_conn().commit()
    print '\n'
    print num, ' entries have been added'





















