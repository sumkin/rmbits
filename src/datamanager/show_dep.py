from datetime import date
from matplotlib import pyplot as plt

from departure import *

if __name__ == '__main__':
  if len(sys.argv) != 5:
    assert False

  orgn = sys.argv[1]
  dstn = sys.argv[2]
  fltnum = sys.argv[3]
  dt = sys.argv[4]

  dts = dt.split('-')
  y = int(dts[0])
  m = int(dts[1])
  d = int(dts[2])
  dt = date(y,m,d)
  dep = Departure(orgn,dstn,fltnum,dt)

  au_curve = dep.get_au_curve()
  adjcap_curve = dep.get_adjcap_curve()
  booked_curve = dep.get_booked_curve()

  plt.plot([e[1] for e in au_curve],label='AU')
  plt.plot([e[1] for e in adjcap_curve],label='Cap')
  plt.plot([e[1] for e in booked_curve],label='Booked')

  plt.legend()
  plt.show()

