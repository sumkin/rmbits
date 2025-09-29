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
    if len(sys.argv) != 2:
        exit('Wrong number of arguments')

    f = open(sys.argv[1],'r')
    curs = dbConnector.get_or_curs()
    line = f.readline()
    num = 0
    while line:
        #print line
        if line.strip() != '':
            curs.execute(line)
            pass
        num += 1
        line = f.readline()
        if num % 10000 == 0:
            print line
            print num
            print '10000 commited'
            dbConnector.get_or_conn().commit()
    dbConnector.get_or_conn().commit()    
    f.close()
    
