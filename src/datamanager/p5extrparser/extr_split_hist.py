import sys
import os
import re
import ConfigParser
from datetime import date

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from db_connector import *

FILE_IN = os.path.normpath(os.path.realpath('./files/reference_split_history_20111010.out'))
#overwrite_split_history_tables(FILE_IN)


def overwrite_split_history_tables(file_in):

    cursor = dbConnector.get_or_curs()
    f = open(file_in,'r')
    curr_gr_id = ''

    q = "TRUNCATE TABLE split_history_group"
    cursor.execute(q)

    q = "TRUNCATE TABLE split_history_range"
    cursor.execute(q)
    
    for line in f:
        if re.search('^FORMATVERSION',line) is not None:
            pass
        elif re.search('^REM',line) is not None:
            # Skip remark
            pass
        elif re.search('^RAG',line) is not None:
            line_l = line.split(' ')
            line_l = [e.strip() for e in line_l]
            idd = line_l[1]
            name = ' '.join(line_l[2:]).strip("\"")
            curr_gr_id = idd

            # add split history group to db
            q = "INSERT INTO split_history_group (name,id)\
                 VALUES ('"+name+"','"+idd+"')"
            cursor.execute(q)
        elif re.search('^RAH',line) is not None:
            line_l = line.split(' ')
            line_l = [e.strip() for e in line_l]
            year = line_l[1]
            pool_id = line_l[2]
            md_from = line_l[3]
            md_to = line_l[4]
            dfrom = date(int(year),int(md_from[:2]),int(md_from[2:]))
            dto = date(int(year),int(md_to[:2]),int(md_to[2:]))

            # add split history period
            q = "INSERT INTO split_history_range (pool_id,group_id,dfrom,dto)\
                 VALUES ("+pool_id+",'"+curr_gr_id+"',\
                        '"+dfrom.strftime('%Y-%m-%d')+"',\
                        '"+dto.strftime('%Y-%m-%d')+"')"
            cursor.execute(q)
        else:
            print 'Unrecognized line tag'
            assert 0

    q = 'commit;'
    cursor.execute(q)

if __name__ == "__main__":

    overwrite_split_history_tables(FILE_IN)

