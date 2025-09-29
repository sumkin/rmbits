import sys
sys.path.append('/home/fnikitin/projects/RandomWalker/rw_src/src/datamanager')
from db_connector import dbConnector
from segment import *
from neo4jrestclient.client import GraphDatabase

gdb = GraphDatabase("http://localhost:7474/db/data/")

from segment in segment.get_segments():


