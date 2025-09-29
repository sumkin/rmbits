from matplotlib import pyplot as plt
from datetime import datetime,date,timedelta
from calc import get_rem2

if __name__ == '__main__':
  orgn = 'HEL'
  dstn = 'JFK'
  fltnum = '00005'
  dto = datetime.now().date() - timedelta(days=1)
  dfrom = dto - timedelta(days=60)

  dt = dfrom
  res = []
  while dt <= dto:
    res.append(get_rem2(orgn,dstn,fltnum,dt))
    dt = dt + timedelta(days=1)
    print dt
  plt.plot(res)
  plt.show()    


  
