from neo4j_updater import Neo4jUpdater

if __name__ == '__main__':
  fname = 'foo'
  nu = Neo4jUpdater(fname)
  print 'Checking missing data...'
  nu.check_missing_daily()
  print 'Checking and deleting duplicates...'
  nu.check_and_delete_duplicates_daily() 

