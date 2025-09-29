# Initial load of continents, regions, countries,
# cities, airports to graph db.
# Data is taken from ADS DW.
# Do not use corresponding RW classes here, because
# RW code should be re-written with graph db backend.
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

gdb = GraphDatabase('http://localhost:7474/db/data/')

continent_ind = gdb.nodes.indexes.create('continent_ind')
region_ind    = gdb.nodes.indexes.create('region_ind')
country_ind   = gdb.nodes.indexes.create('country_ind')
city_ind      = gdb.nodes.indexes.create('city_ind')
airport_ind   = gdb.nodes.indexes.create('airport_ind')

if __name__ == '__main__':
    curs = dbConnector.get_ads_curs()
    q = "SELECT DISTINCT continent,region,country,city,airport_nm\
         FROM ads_airport\
         WHERE airport_nm IS NOT NULL AND\
               city IS NOT NULL AND\
               country IS NOT NULL AND\
               region IS NOT NULL AND\
               continent IS NOT NULL\
         ORDER BY continent,region,country,city,airport_nm DESC"
    curs.execute(q)
    row = curs.fetchone()
    while row is not None:
        continent = row[0].strip()
        region    = row[1].strip()
        country   = row[2].strip()
        city      = row[3].strip()
        airport   = row[4].strip()

        # Check and add continent if not exists
        if len(continent_ind['code'][continent][:]) == 0:
            continent_node = gdb.nodes.create(code=continent)
            continent_ind.add('code',continent,continent_node)
            print 'Continent',continent, ' added'
        else:
            continent_node = continent_ind['code'][continent][0]
            #print continent, ' is found'

        # Check and add region if not exists
        if len(region_ind['code'][region][:]) == 0:
            region_node = gdb.nodes.create(code=region)
            region_ind.add('code',region,region_node)
            print 'Region',region, ' added'
        else:
            region_node = region_ind['code'][region][0]
            #print region, ' is found'

        # Check and add country if not exists
        if len(country_ind['code'][country][:]) == 0:
            country_node = gdb.nodes.create(code=country)
            country_ind.add('code',country,country_node)
            print 'Country',country, ' added'
        else:
            country_node = country_ind['code'][country][0]
            #print country, ' is found'

        # Check and add cities if not exists
        if len(city_ind['code'][city][:]) == 0:
            city_node = gdb.nodes.create(code=city)
            city_ind.add('code',city,city_node)
            print 'City',city, ' added'
        else:
            city_node = city_ind['code'][city][0]
            #print city, ' is found'

        # Check and add airports if not exists
        if len(airport_ind['code'][airport][:]) == 0:
            airport_node = gdb.nodes.create(code=airport)
            airport_ind.add('code',airport,airport_node)
            print 'Airport',airport, ' added'
        else:
            airport_node = airport_ind['code'][airport][0]
            #print airport, ' is found'

        # Create relationships
        if len(airport_node.relationships.outgoing(['IS_IN'])[:]) == 0:
            airport_node.IS_IN(city_node)
            print airport,'IS_IN', city
        if len(city_node.relationships.outgoing(['IS_IN'])[:]) == 0:
            city_node.IS_IN(country_node)
            print city,'IS_IN',country
        if len(country_node.relationships.outgoing(['IS_IN'])[:]) == 0:
            country_node.IS_IN(region_node)
            print country,'IS_IN',region
        if len(region_node.relationships.outgoing(['IS_IN'])[:]) == 0:
            region_node.IS_IN(continent_node)
            print region,'IS_IN',continent

        sleep(1)

        print '--------------------------'
        row = curs.fetchone()



