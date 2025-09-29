from neo4jrestclient.client import GraphDatabase

gdb = GraphDatabase("http://localhost:7474/db/data/")

for i in range(0,1000000):

    node = gdb.nodes.create(name = str(i) + ' node')
    print 'Node ' + str(i) + ' inserted.'

