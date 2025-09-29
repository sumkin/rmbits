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
    dto_s   = sys.argv[2]

    dfrom_l = dfrom_s.split('-')
    dto_l   = dto_s.split('-')

    dfrom = date(int(dfrom_l[0]),int(dfrom_l[1]),int(dfrom_l[2]))
    dto = date(int(dto_l[0]),int(dto_l[1]),int(dto_l[2]))

    print 'Date range: ', dfrom.strftime('%Y-%m-%d'), dto.strftime('%Y-%m-%d')

    curs = dbConnector.get_dwadm_curs()
    q = "SELECT fst_tkt,flightdate,depairport,arrairport,pax,bookingclass\
         FROM paras_used\
         WHERE flightdate <= DATE('" + dto.strftime('%Y-%m-%d') + "') AND\
               flightdate >= DATE('" + dfrom.strftime('%Y-%m-%d') + "')"
    curs.execute(q)

    or_curs = dbConnector.get_or_curs()
    or_curs.execute('TRUNCATE TABLE paras_used')
    print 'paras_used table has been truncated...'

    num = 0
    row = curs.fetchone()
    while row is not None:

        if row[0] is None or row[1] is None or row[2] is None or row[3] is None or row[4] is None or row[5] is None:
            row = curs.fetchone()
            continue

        num += 1
        fst_tkt      = row[0].strip()
        flightdate   = row[1]
        depairport   = row[2].strip()
        arrairport   = row[3].strip()
        pax          = int(row[4])
        bookingclass = row[5]

        or_q = "INSERT INTO paras_used (fst_tkt,flightdate,depairport,arrairport,pax,bookingclass)\
                VALUES ('"+fst_tkt+"',\
                        '"+flightdate.strftime('%Y-%m-%d')+"',\
                        '"+depairport+"',\
                        '"+arrairport+"',\
                         "+str(pax)+",\
                        '"+bookingclass+"')"
        or_curs.execute(or_q)
        if num % 100000 == 0:
            print '.',
            dbConnector.get_or_conn().commit()
        row = curs.fetchone()

    dbConnector.get_or_conn().commit()
    print '\n'
    print num, ' entries have been added'





