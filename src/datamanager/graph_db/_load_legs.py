import sys
sys.path.append('/home/fnikitin/projects/RandomWalker/rw_src/src/datamanager')
from db_connector import dbConnector
from leg import *
from neo4jrestclient.client import GraphDatabase

gdb = GraphDatabase("http://localhost:7474/db/data/")
airport_ind = gdb.nodes.indexes.get('airport_ind') 
leg_ind = gdb.nodes.indexes.create('leg_ind')

for leg in leg.get_legs():

    print 'Leg: ' + str(leg)

    orgn   = leg[0]
    dstn   = leg[1]
    fltnum = leg[2]
    date   = leg[3]

    orgn_nodes = airport_ind.get("code",orgn)
    assert len(orgn_nodes) == 1
    dstn_nodes = airport_ind.get("code",dstn)
    assert len(dstn_nodes) == 1

    orgn_node = orgn_nodes[0]
    dstn_node = dstn_nodes[0]

    leg_node = gdb.nodes.create(type='leg',fltnum=fltnum,date=date)
    leg_ind.add("type","leg",leg_node)
    leg_ind.add("fltnum",fltnum,leg_node)
    leg_node.relationships.create('FROM',orgn_node)
    leg_node.relationships.create('TO',dstn_node)  






















