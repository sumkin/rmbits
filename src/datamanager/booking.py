import os
import sys
import ConfigParser

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector

class Booking:

    def __init__(self,fst_tkt,cls=None):
        # cls is added to speed up query
        # if it is give search in corresponding
        # class booking table
        self.fst_tkt = fst_tkt
        self.cls = cls

    def num_legs(self):
        curs = dbConnector.get_or_curs()
        if self.cls is None:
            q = "SELECT count(*) FROM paras_used\
                 WHERE fst_tkt = '" + self.fst_tkt + "'"
        else:
            q = "SELECT count(*) FROM paras_used_" + self.cls + "\
                 WHERE fst_tkt = '" + self.fst_tkt + "'"
        curs.execute(q)
        row = curs.fetchone()
        return row[0]

    def get_legs(self):
        res = []
        curs = dbConnector.get_or_curs()
        if self.cls is None:
            q = "SELECT flightdate,depairport,arrairport,pax,bkg_cre_dt_tm\
                 FROM paras_used\
                 WHERE fst_tkt = '" + self.fst_tkt + "' ORDER BY flightdate" 
        else:
            q = "SELECT flightdate,depairport,arrairport,pax,bkg_cre_dt_tm\
                 FROM paras_used_" + self.cls + "\
                 WHERE fst_tkt = '" + self.fst_tkt + "' ORDER BY flightdate"
        curs.execute(q)
        row = curs.fetchone()
        while row is not None:
            res.append({'flightdate': row[0],
                        'depairport': row[1].strip(),
                        'arrairport': row[2].strip(),
                        'pax': row[3],
                        'bkg_cre_dt_tm': row[4]})
            row = curs.fetchone()
        return res

    def get_path(self):
        legs = self.get_legs()
        

            
    
