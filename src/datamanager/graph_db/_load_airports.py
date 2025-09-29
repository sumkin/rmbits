import sys
sys.path.append('/home/fnikitin/projects/RandomWalker/rw_src/src/datamanager')
from db_connector import dbConnector
from airport import *
from neo4jrestclient.client import GraphDatabase

gdb = GraphDatabase("http://localhost:7474/db/data/")

country_ind   = gdb.nodes.indexes.create("country_ind")
city_ind      = gdb.nodes.indexes.create("city_ind")
airport_ind   = gdb.nodes.indexes.create("airport_ind")

for country in airport.get_countries():

    print 'Country: ' + country
    country_node = gdb.nodes.create(type='country', code = country)
    country_ind.add("type", "country", country_node)
    country_ind.add("code", country, country_node)

    for city in airport.get_cities_in_country(country):

        print '\tCity: ' + city
        city_node = gdb.nodes.create(type='city', code = city)
        city_node.relationships.create('IS_IN',country_node)
        city_ind.add("type", "city", city_node)
        city_ind.add("code", city, city_node)
  
        for arprt in airport.get_airports_in_city(city):

            print '\t\tAirport: ' + arprt
            airport_node = gdb.nodes.create(type='airport', code = arprt)
            airport_node.relationships.create('IS_IN',city_node)
            airport_ind.add("type", "airport", airport_node)
            airport_ind.add("code", arprt, airport_node)
