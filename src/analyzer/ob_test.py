##
# This script was written just to 
# to test how change of overbooking
# setting affected authorization level
#
import sys
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read('../../../rw.cfg')
sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector
from datetime import date, timedelta

pros_curs = dbConnector.get_prosuser_curs()

#
# Test HEL-ARN 00637 first
#

begin_date = date(2011,11,15)
end_date = date(2011,12,10)

days_num = end_date - begin_date

print 'HEL-ARN-00637'
print '-------------'

for i in range(0,days_num.days):

  old_daysprior = i + 1
  new_daysprior = i
  dep_date = begin_date + timedelta(days=i)

  q = "SELECT obsts FROM hleg_compartment\
       WHERE orgn = 'HEL' AND dstn = 'ARN' AND fltnum = '00637' AND\
             dptdt = DATE('" + dep_date.strftime('%Y-%m-%d') + "') AND cmpsym='Y' AND\
             daysprior = " + str(old_daysprior)
  pros_curs.execute(q)
  row = pros_curs.fetchone()
  if row is None:
    continue
  old_obsts= row[0]

  q = "SELECT obsts FROM hleg_compartment\
       WHERE orgn = 'HEL' AND dstn = 'ARN' AND fltnum = '00637' AND\
             dptdt = DATE('" + dep_date.strftime('%Y-%m-%d') + "') AND cmpsym='Y' AND\
             daysprior = " + str(new_daysprior)
  pros_curs.execute(q)
  row = pros_curs.fetchone()
  if row is None:
    continue
  new_obsts = row[0]

  print dep_date.strftime('%Y-%m-%d')
  print '\t Old: ' + str(old_obsts) + '   New: ' + str(new_obsts)

#
# Test HEL-GOT 00677 first
#

print 'HEL-GOT-00677'
print '-------------'

for i in range(0,days_num.days):

  old_daysprior = i + 1
  new_daysprior = i
  dep_date = begin_date + timedelta(days=i)

  q = "SELECT obsts FROM hleg_compartment\
       WHERE orgn = 'HEL' AND dstn = 'GOT' AND fltnum = '00677' AND\
             dptdt = DATE('" + dep_date.strftime('%Y-%m-%d') + "') AND cmpsym='Y' AND\
             daysprior = " + str(old_daysprior)
  pros_curs.execute(q)
  row = pros_curs.fetchone()
  if row is None:
    continue
  old_obsts = row[0]

  q = "SELECT obsts FROM hleg_compartment\
       WHERE orgn = 'HEL' AND dstn = 'GOT' AND fltnum = '00677' AND\
             dptdt = DATE('" + dep_date.strftime('%Y-%m-%d') + "') AND cmpsym='Y' AND\
             daysprior = " + str(new_daysprior)
  pros_curs.execute(q)
  row = pros_curs.fetchone()
  if row is None:
    continue
  new_obsts = row[0]

  print dep_date.strftime('%Y-%m-%d')
  print '\t Old: ' + str(old_obsts) + '   New: ' + str(new_obsts)


