import sys
import os
import csv
import sqlite3
from sqlite3 import OperationalError
import ConfigParser
from datetime import datetime

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

csv_file = 'airports.csv'

sqlite_fldr = config.get('PATHS','common_sqlite')
fname = os.path.normpath(sqlite_fldr+'/airports.db')
conn = sqlite3.connect(fname)
c = conn.cursor()

try:
    c.execute("SELECT * FROM airports")
except OperationalError:
    c.execute("CREATE TABLE airports \
               (airport text, city text, country text, region text, continent text, city_name text)")

csv_reader = csv.reader(open(csv_file,'rb'))
num = 0
for row in csv_reader:
    airport   = row[0]
    city      = row[1]
    country   = row[2]
    region    = row[3]
    continent = row[4]
    try:
      city_name = row[5]
    except:
      city_name = ''
    c.execute("INSERT INTO airports VALUES\
               ('"+airport+"','"+city+"','"+country+"','"+region+"','"+continent+"','"+city_name+"')")
    conn.commit()
    num += 1
print num






