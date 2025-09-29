# Initial load of departures
# Data is taken from ADS DW.
# Do not use corresponding RW classes here, because
# RW code should be re-written with graph db backend.
#
# It is assumed that continents,regions,countries,cities
# are already loaded.
#
# (!c) sumkin, 2012

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
from datetime import date
from py2neo import neo4j, cypher

gdb = GraphDatabase('http://localhost:7474/db/data/')
gdb_srv = neo4j.GraphDatabaseService('http://localhost:7474/db/data/')

booking_ind = gdb.nodes.indexes.create('booking_ind')
departure_ind = gdb.nodes.indexes.get('departure_ind')

FROM = 'JFK'
TO = 'HEL'

if __name__ == '__main__':
    curs = dbConnector.get_or_curs()
    q = "SELECT fst_tkt, flightdate, depairport, arrairport,\
                pax, bkg_cre_dt_tm, bookingclass\
         FROM paras_used LIMIT 1000000 OFFSET 0"
    curs.execute(q)
    row = curs.fetchone()
    num = 0
    while row is not None:
        fst_tkt       = row[0].strip()
        flightdate    = row[1]
        depairport    = row[2].strip()
        arrairport    = row[3].strip()
        pax           = row[4]
        if row[5] is None:
            print 'skipped'
            row = curs.fetchone()
            continue
        bkg_cre_dt    = date(row[5].year,row[5].month,row[5].day)
        bookingclass  = row[6].strip()

        # Check that departure was not processed
        if len(booking_ind['fst_tkt'][fst_tkt][:]) == 0:
            booking_node = gdb.nodes.create(fst_tkt = fst_tkt,
                                            num_pax = pax,
                                            cre_dt = bkg_cre_dt.strftime('%Y-%m-%d'),
                                            cls = bookingclass)
            booking_ind.add('fst_tkt',fst_tkt,booking_node)
        else:
            booking_node = booking_ind['fst_tkt'][fst_tkt][0]

        # Define flight number because it is missed in paras_used
        cypher_q = "START orgn = node:airport_ind(code='"+depairport+"'),\
                          dstn = node:airport_ind(code='"+arrairport+"')\
                    MATCH (orgn)<-[:FROM]-(d)-[:TO]->(dstn)\
                    WHERE d.dptdt = '"+flightdate.strftime('%Y-%m-%d')+"'\
                    RETURN d"
        data,metadata = cypher.execute(gdb_srv,cypher_q)
        # FIXME: two different flight numbers could exist
        # for the same origin-destination.
        # Take the first one!
        if len(data) == 0:
            # skip flight was not found
            print 'skipped'
            row = curs.fetchone()
            continue
        if len(data[0]) != 1:
            print data[0]
            assert 0
        fltnum = data[0][0]['fltnum']

        # Add relationships
        dep_full_ind = depairport+'-'+arrairport+'-'+fltnum+'-'+\
                       flightdate.strftime('%Y-%m-%d')
        if len(departure_ind['full'][dep_full_ind]) != 0:
            dep_node = departure_ind['full'][dep_full_ind][0]
        else:
            print dep_full_ind, len(departure_ind['full'][dep_full_ind])
            assert 0
        if len(booking_node.relationships.outgoing(['FOR'])) == 0:
            booking_node.FOR(dep_node)
            
        num += 1
        print depairport,arrairport,fltnum,'-------------------------- (',num,')'
        row = curs.fetchone()

        #if num % 50 == 0:
        sleep(0.5)
    print 'DONE!'



