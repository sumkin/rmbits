import os
import sys
from datetime import date, timedelta
from matplotlib import pyplot as plt
from matplotlib import cm as cm
from matplotlib import mlab as ml
import numpy as np

import ConfigParser

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from daysprior import get_dayspriors
from analyzer_if import *

dfrom = date(2012,2,1)
dto = date(2013,2,1)

m =(dto - dfrom).days

z = []

for daysprior in get_dayspriors():
  ts = get_fcsterr_by_dptdt_dflc_lvl('cons','HEL','JFK','00005',dfrom,dto,daysprior,'Z')
  ts = ts[2]
  print len(ts),(dto-dfrom).days
  if len(ts) != 348:
    continue
  z.append(ts)

'''
z = np.array(z)

n,m = z.shape

y = np.array(range(n))
x = np.array(range(m))

x = x.ravel()
y = y.ravel()
z = z.ravel()

xmin = x.min()
xmax = x.max()
ymin = y.min()
ymax = y.max()

X,Y = np.meshgrid(x,y)
x = X.ravel()
y = Y.ravel()
'''

#gridsize = 25
#fig = plt.figure(figsize=(20,7))
#ax = plt.subplot(111)
#plt.subplots_adjust(hspace=2.0)
#plt.xticks(range(0,m,4),[(dfrom + timedelta(days=i)).strftime('%d.%m') for i in range(0,m,4)],rotation='vertical')
#plt.hexbin(x,y,C=z,cmap=cm.jet,bins=None,mincnt=1)
#plt.axis([x.min(),x.max(),y.min(),y.max()])

fig = plt.figure(figsize=(20,7))
ax = fig.add_subplot(111)
img = ax.imshow(z,aspect=5)
plt.xticks(range(0,m,4),[(dfrom + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(0,m,4)],rotation='vertical')
plt.colorbar(img)
#cb.set_label('RMSE')
plt.show()


