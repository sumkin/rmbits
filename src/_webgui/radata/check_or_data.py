from or_data_updater import OrDataUpdater

if __name__ == '__main__':
  fname = 'foo'
  ou = OrDataUpdater(fname)
  print 'Checking missing data...'
  ou.check_missing_daily()
  print 'Checking and deleting duplicates...'
  ou.check_and_delete_duplicates_daily()
