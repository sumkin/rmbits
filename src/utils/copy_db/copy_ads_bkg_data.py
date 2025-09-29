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

    dfrom_s = sys.argv[1]
    dto_s = sys.argv[2]

    dfrom_l = dfrom_s.split('-')
    dto_l = dto_s.split('-')

    dfrom = date(int(dfrom_l[0]),int(dfrom_l[1]),int(dfrom_l[2]))
    dto = date(int(dto_l[0]),int(dto_l[1]),int(dto_l[2]))

    print 'Date range: ', dfrom.strftime('%Y-%m-%d'), dto.strftime('%Y-%m-%d')

    curs = dbConnector.get_ads_curs()
    q = "SELECT bkg_cre_dt_tm, bkg_tkt_id, coupon_id\
         FROM ads_bkg\
         WHERE bkg_cancel_dt_tm IS NULL AND\
               bkg_tkt_id IS NOT NULL AND\
               opr_carrier_id = 53 AND\
               opr_flt_dt >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
               opr_flt_dt <= DATE('" + dto.strftime('%Y-%m-%d') + "')"
    print q
    curs.execute(q)

    or_curs = dbConnector.get_or_curs()
    or_curs.execute('TRUNCATE TABLE ads_bkg')
    print 'ads_bkg table has been truncated...'

    num = 0
    row = curs.fetchone()
    while row is not None:

        num += 1
        bkg_cre_dt_tm = row[0]
        bkg_tkt_id = row[1]
        coupon_id = row[2]
        or_q = "INSERT INTO ads_bkg (bkg_cre_dt_tm,bkg_tkt_id,coupon_id)\
                VALUES (DATE('" + bkg_cre_dt_tm.strftime('%Y-%m-%d') + "'),\
                       " + str(bkg_tkt_id) + "," + str(coupon_id) + ")"
        or_curs.execute(or_q)
        if num % 100000 == 0:
            print '.',
            dbConnector.get_or_conn().commit()
        row = curs.fetchone()

    dbConnector.get_or_conn().commit()
    print '\n'
    print num, ' entries have been added'





















