import MySQLdb
from datetime import date
from date_range import *

from db_connector import dbConnector

cursor = dbConnector.get_or_curs()

# FIXME: change class name according to PEP8 recommendation

class splitHistory:

    def __init__(self,id_):

        self.id_ = id_

    def get_name(self):
 
        q = "SELECT name FROM split_history_group\
             WHERE id='" + str(self.id_) + "';"
        cursor.execute(q)
        row = cursor.fetchone()
        return row[0]

    def get_pool_ids(self):

        q = "SELECT DISTINCT pool_id FROM split_history_range\
             WHERE group_id = " + str(self.id_) + ";"
        cursor.execute(q)
        rows = cursor.fetchall()
        ret = [e[0] for e in rows]
        return ret

    def get_date_ranges(self,pool_id):

        q = "SELECT dfrom,dto FROM split_history_range\
             WHERE group_id = " + str(self.id_) + " AND\
                   pool_id = " + str(pool_id) + ";"
        cursor.execute(q)
        rows = cursor.fetchall()
        for e in rows:
            yield dateRange(e[0],e[1])



