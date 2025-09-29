import sys
import os
import ConfigParser
from matplotlib import pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from pylab import *

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector

if __name__ == '__main__':
  or_curs = dbConnector.get_or_curs()
  q = "SELECT dptdt,bp,bv,mv,rev,eff FROM rem\
       WHERE orgn='HEL' AND dstn='BKK' AND fltnum='00089'\
       ORDER BY dptdt ASC"
  or_curs.execute(q)
  rows = or_curs.fetchall()

  dates = [row[0] for row in rows]
  bps = [row[1] for row in rows]
  bvs = [row[2] for row in rows]
  mvs = [row[3] for row in rows]
  revs = [row[4] for row in rows]
  effs = [row[5] for row in rows]

  # Draw plots
  fig = plt.figure()

  plt.suptitle('HEL-BKK-00089')

  ax1 = plt.subplot(311)
  ax1.plot(dates,bps,label='Blind revenue')
  ax1.plot(dates,revs,label='Revenue')
  ax1.legend()
  setp(ax1.get_xticklabels(), visible=False)

  ax2 = plt.subplot(312,sharex=ax1)
  ax2.plot(dates,effs,label='Efficiency')
  ax2.legend()
  setp(ax2.get_xticklabels(), visible=False)

  ax3 = plt.subplot(313,sharex=ax1)
  ax3.plot(dates,mvs,label='Market volatility')
  ax3.legend()
  setp(ax3.get_xticklabels(), fontsize=8)

  ax1.xaxis.set_major_locator(mticker.MaxNLocator(40))
  ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

  for label in ax1.xaxis.get_ticklabels():
    label.set_rotation(30)
  for label in ax2.xaxis.get_ticklabels():
    label.set_rotation(30)
  for label in ax3.xaxis.get_ticklabels():
    label.set_rotation(30)

  plt.subplots_adjust(hspace=0.1,bottom=0.15)

  plt.show()
           




