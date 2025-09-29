import os
#from lambda_packages import psycopg2
import configparser
import pandas_redshift as pr

#from neo4jrestclient.client import GraphDatabase

config = configparser.ConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'rmbits.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

dw_conn          = None
siebel_conn      = None
or_conn          = None
val_conn         = None
loc_sqlite_conn  = None
rs_conn, rs_curs = None, None


class DBConnector:

    pros_dw_curs    = None
    ads_dw_curs     = None
    nrm_dw_curs     = None
    siebel_curs     = None
    or_curs         = None
    dwadm_dw_curs   = None
    val_curs        = None
    loc_sqlite_curs = None
    neo4j_conn      = None

    '''
    @staticmethod
    def get_prosuser_curs():
        global dw_conn
        if DBConnector.pros_dw_curs is None:
            server = config.get('PROS_DW_DB','server')
            port = config.get('PROS_DW_DB','port')
            user = config.get('PROS_DW_DB','user')
            pwd = config.get('PROS_DW_DB','pass')
            name = config.get('PROS_DW_DB','name')
            service_name = config.get('PROS_DW_DB','service_name')
            dw_conn = cx_Oracle.connect(user+'/'+pwd+'@'+server+'/'+service_name)
            dw_conn.current_schema = name
            DBConnector.pros_dw_curs = dw_conn.cursor()
        return DBConnector.pros_dw_curs
    '''

    @staticmethod
    def get_neo4j_conn():
        global neo4j_conn
        if DBConnector.neo4j_conn is None:
            return GraphDatabase('http://localhost:7474/db/data/')
        return DBConnector.neo4j_conn

    '''
    @staticmethod
    def get_ads_curs():
        global dw_conn
        if DBConnector.ads_dw_curs is None:
            server = config.get('ADS_DW_DB','server')
            port = config.get('ADS_DW_DB','port')
            user = config.get('ADS_DW_DB','user')
            pwd = config.get('ADS_DW_DB','pass')
            name = config.get('ADS_DW_DB','name')
            service_name = config.get('ADS_DW_DB','service_name')
            connline = user+'/'+pwd+'@'+server+'/'+service_name
            print('connline = ', connline)
            dw_conn = cx_Oracle.connect(connline)
            dw_conn.current_schema = name
            DBConnector.ads_dw_curs = dw_conn.cursor()
        return DBConnector.ads_dw_curs
    '''

    '''
    @staticmethod
    def get_nrm_curs():
        global dw_conn
        if DBConnector.nrm_dw_curs is None:
            server = config.get('NRM_DW_DB', 'server')
            port = config.get('NRM_DW_DB', 'port')
            user = config.get('NRM_DW_DB', 'user')
            pwd = config.get('NRM_DW_DB', 'pass')
            name = config.get('NRM_DW_DB', 'name')
            service_name = config.get('NRM_DW_DB', 'service_name')
            conn_str = user+'/'+pwd+'@'+server+':'+port+'/'+service_name
            dw_conn = cx_Oracle.connect(conn_str)
            dw_conn.current_schema = name
            DBConnector.nrm_dw_curs = dw_conn.cursor()
        return DBConnector.nrm_dw_curs
    '''

    '''
    @staticmethod
    def get_siebel_curs():
        global siebel_conn
        if DBConnector.siebel_curs is None:
            server = config.get('SIEBEL_DB','server')
            port = config.get('SIEBEL_DB','port')
            user = config.get('SIEBEL_DB','user')
            pwd  = config.get('SIEBEL_DB','pass')
            service_name   = config.get('SIEBEL_DB','service_name')

            conn_s = "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST="+server+")(PORT="+port+"))\
                      (CONNECT_DATA = (SERVER=DEDICATED)\
                      (SERVICE_NAME = "+service_name+")))"
            siebel_conn = cx_Oracle.connect(user+'/'+pwd+'@'+conn_s)
            siebel_conn.current_schema = 'OLAPADM'
            DBConnector.siebel_curs = siebel_conn.cursor()
        return DBConnector.siebel_curs
    '''

    @staticmethod
    def get_or_conn():
        return or_conn


    @staticmethod
    def get_or_curs():
        global or_conn
        if DBConnector.or_curs is None:
            server = config.get('OR_DB','server')
            port   = config.get('OR_DB','port')
            user   = config.get('OR_DB','user')
            pwd    = config.get('OR_DB','pass')
            name   = config.get('OR_DB','name')

            or_conn = MySQLdb.connect(host = server, user = user, passwd = pwd, db = name)
            DBConnector.or_curs = or_conn.cursor()
        return DBConnector.or_curs

    '''
    @staticmethod
    def get_rs_curs():
        global rs_conn, rs_curs
        if rs_curs is None:
            dbname = config.get('RedShift', 'dbname')
            user   = config.get('RedShift', 'user')
            pwd    = config.get('RedShift', 'pwd')
            host   = config.get('RedShift', 'host')
            port   = config.get('RedShift', 'port')
            rs_conn = psycopg2.connect("dbname=" + dbname +\
                                       " user=" + user +\
                                       " password=" + pwd +\
                                       " host=" + host +\
                                       " port=" + port) 
            rs_curs = rs_conn.cursor()
            return rs_curs
    '''

    @staticmethod
    def pr_conn():
        dbname = config.get('RedShift', 'dbname')
        user   = config.get('RedShift', 'user')
        pwd    = config.get('RedShift', 'pwd')
        host   = config.get('RedShift', 'host')
        port   = config.get('RedShift', 'port')
        pr.connect_to_redshift(dbname = dbname.strip("\'"),\
                               host = host.strip("\'"),\
                               port = int(port.strip("\'")),\
                               user = user.strip("\'"),\
                               password = pwd.strip("\'"))        
    

    '''
    @staticmethod
    def get_new_rs_conn():
        dbname = config.get('RedShift', 'dbname')
        user   = config.get('RedShift', 'user')
        pwd    = config.get('RedShift', 'pwd')
        host   = config.get('RedShift', 'host')
        port   = config.get('RedShift', 'port')
        rs_conn = psycopg2.connect("dbname=" + dbname +\
                                   " user=" + user +\
                                   " password=" + pwd +\
                                   " host=" + host +\
                                   " port=" + port)
        return rs_conn
    '''


if __name__ == "__main__":
    rs_curs = DBConnector.get_rs_curs()
    print('rs_curs = ', rs_curs)

    

