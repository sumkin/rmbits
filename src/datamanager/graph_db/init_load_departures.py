# Initial load of departures
# Data is taken from ADS DW.
# Do not use corresponding RW classes here, because
# RW code should be re-written with graph db backend.
#
# It is assumed that continents,regions,countries,cities
# are already loaded.
#
# Written by Fedor Nikitin, 2012

import os
import sys
import ConfigParser

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)
sys.path.append(config.get('PATHS','datamanager'))

from time import sleep
from db_connector import dbConnector
from neo4jrestclient.client import GraphDatabase

DATE_FROM = '2011-05-29'
DATE_TO = '2012-05-29'


gdb = GraphDatabase('http://localhost:7474/db/data/')

departure_ind = gdb.nodes.indexes.create('departure_ind')
airport_ind = gdb.nodes.indexes.get('airport_ind')

if __name__ == '__main__':
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT DISTINCT fltnum,orgn,dstn,dptdt\
         FROM hleg\
         WHERE dptdt >= DATE('"+DATE_FROM+"') AND\
               dptdt <= DATE('"+DATE_TO+"') AND fltnum > '00499'"
    curs.execute(q)
    num = 0
    row = curs.fetchone()
    while row is not None:
        fltnum = row[0].strip()
        orgn    = row[1].strip()
        dstn   = row[2].strip()
        dptdt = row[3]
        num += 1

        added = False

        full_ind = orgn+'-'+dstn+'-'+fltnum+'-'+dptdt.strftime('%Y-%m-%d')

        # Check that departure was not processed
        if len(departure_ind['full'][full_ind][:]) == 0:
            departure_node = gdb.nodes.create(fltnum=fltnum,
                                              orgn=orgn,
                                              dstn=dstn,
                                              dptdt=dptdt.strftime('%Y-%m-%d'))
            departure_ind.add('full',full_ind,departure_node)
            departure_ind.add('fltnum',fltnum,departure_node)
            departure_ind.add('orgn',orgn,departure_node)
            departure_ind.add('dstn',dstn,departure_node)
            departure_ind.add('dptdt',dptdt.strftime('%Y-%m-%d'),departure_node)
        else:
            departure_node = departure_ind['full'][full_ind][0]
            added = True

        # Add relationships
        from_airport_node = airport_ind['code'][orgn][0]
        to_airport_node = airport_ind['code'][dstn][0]

        if len(departure_node.relationships.outgoing(['FROM'])[:]) == 0:
            departure_node.FROM(from_airport_node)
            print full_ind,'FROM',orgn
        if len(departure_node.relationships.outgoing(['TO'])[:]) == 0:
            departure_node.TO(to_airport_node)
            print full_ind,'TO',dstn
        
        print '-------------------------- (',num,')'
        row = curs.fetchone()

        sleep(0.5)



