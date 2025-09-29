import os
import sys
import shlex
import ConfigParser

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector

class Aircraft:

    def __init__(self,code,cfg_code):
        self.code    = code.strip()
        self.cfg_code = cfg_code.strip()

    def get_cap(self):
        or_curs = dbConnector.get_or_curs()
        q = "SELECT bcap,ecap FROM aircraft_cfg\
             WHERE aircraft_code = '" + self.code + "' AND\
                   cfg_code = '" + self.cfg_code + "'"
        or_curs.execute(q)
        row = or_curs.fetchone()
        return [row[0],row[1]]
    
    @property
    def code(self):
        return self.code

    @property
    def cfg_code(self):
        return self.cfg_code

    @staticmethod
    def get_all_aircrafts(mrkt):
        # Return all possible aircraft configurations
        # for route. Notice the code below is very
        # specific for SVX route!!! It should be
        # fixed to catch all of generality.

        if mrkt == 'SVX':
            # first go through Embraer
            or_curs = dbConnector.get_or_curs()
            q = "SELECT code FROM aircraft\
                 WHERE code LIKE '90%'"
            or_curs.execute(q)
            rows = or_curs.fetchall()
            for row in rows:
                code = row[0]
                sub_q = "SELECT cfg_code\
                         FROM aircraft_cfg\
                         WHERE aircraft_code = '" + code + "'"
                or_curs.execute(sub_q)
                sub_rows = or_curs.fetchall()
                for sub_row in sub_rows:
                    cfg_code = sub_row[0] 
                    ret = aircraft(code,cfg_code) 
                    yield ret
            # second go through Airbus
            or_curs = dbConnector.get_or_curs()
            q = "SELECT code FROM aircraft\
                 WHERE code LIKE '19%'"
            or_curs.execute(q)
            rows = or_curs.fetchall()
            for row in rows:
                code = row[0]
                sub_q = "SELECT cfg_code\
                         FROM aircraft_cfg\
                         WHERE aircraft_code = '" + code + "'"
                or_curs.execute(sub_q)
                sub_rows = or_curs.fetchall()
                for sub_row in sub_rows:
                    cfg_code = sub_row[0]
                    ret = aircraft(code,cfg_code)
                    yield ret 

    @staticmethod
    def parse_pros_file(filename):
        or_curs = dbConnector.get_or_curs()
        f = open(filename,'r')
        s = f.readline()
        while s != '':
            parts = shlex.split(s)
            parts = [e.strip().strip('"') for e in parts]
            if parts[0] == 'RLA':
                aircraft_code   = parts[1]
                aircraft_descr  = parts[2]
                aircraft_maxcap = int(parts[3])  

                # insert row in aircraft table
                q = "INSERT INTO aircraft (code,descr,maxcap)\
                     VALUES ('" + aircraft_code + "',\
                             '" + aircraft_descr + "',\
                              " + str(aircraft_maxcap) + ")"
                or_curs.execute(q)
            elif parts[0] == 'RLS':
                air_cfg_key = parts[1]                
                air_cfg_code = parts[2]
                air_cfg_bcap = int(parts[3])
                air_cfg_ecap = int(parts[4])

                # insert row in aircraft config table
                q = "INSERT INTO aircraft_cfg (aircraft_code,cfg_key,cfg_code,bcap,ecap)\
                     VALUES ('" + aircraft_code + "', '" + air_cfg_key + "', '" + air_cfg_code +\
                             "'," + str(air_cfg_bcap) + "," + str(air_cfg_ecap)+")"
                or_curs.execute(q)
            s = f.readline()



