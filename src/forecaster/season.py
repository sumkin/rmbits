import os
import sys
import ConfigParser

from datetime import datetime, date, timedelta
from rpy2 import robjects
from matplotlib import pyplot as plt

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(__file__,'../../../rw.cfg')
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from leg import *
from cls import *

r = robjects.r
r.source('season.R')

WEEK_NUM_BACK = 78
WEEK_NUM = 156

def get_coeffs(leg,dfrom,dto,clss):
  data = leg.get_booked_weekly(dfrom,dto,clss)
  vals = [float(e[1]) for e in data]
  vals_r = robjects.FloatVector(vals)
  res_r = r.season(vals_r)
  x     = None
  trend = None
  seas  = None
  rem   = None
  for item_r in res_r.iteritems():
    if item_r[0] == 'x':
      x = list(robjects.default_ri2py(item_r[1]))
    elif item_r[0] == 'trend':
      trend = list(robjects.default_ri2py(item_r[1]))
    elif item_r[0] == 'seasonal':
      seas = list(robjects.default_ri2py(item_r[1]))
    elif item_r[0] == 'random':
      rem = list(robjects.default_ri2py(item_r[1]))
    else:
      pass 

  dates = [e[0] for e in data]

  return dates,x,trend,seas,rem

def show_decompose(leg,dfrom,dto,clss):
  print 'dfrom:',dfrom.isocalendar()
  print 'dto:',dto.isocalendar()
  print 'focus_week:',(dto - timedelta(weeks=WEEK_NUM_BACK)).isocalendar()
  data = leg.get_booked_weekly(dfrom,dto,clss)
  vals = [float(e[1]) for e in data]
  vals_r = robjects.FloatVector(vals)
  res_r = r.show_decompose(vals_r)
  res = robjects.default_ri2py(res_r)
  res = list(res)
  assert len(data) == len(res)
  for i in range(len(data)):
    print data[i][0],data[i][1],res[i] 
  raw_input()

fname_p5 = None
fname_csv = None

def get_p5_fname():
  global fname_p5
  if fname_p5 is None:
    path = config.get('PATHS','seas.data')
    name = path + '/seasonality_'+datetime.now().date().strftime('%Y%m%d')
    fname_p5 = name+'.seas'
  return fname_p5

def get_csv_fname():
  global fname_csv
  if fname_csv is None:
    path = config.get('PATHS','seas.data')
    name = path + '/seasonality_'+datetime.now().date().strftime('%Y%m%d')
    fname_csv = name + '.csv'
  return fname_csv

def write_header_files():
  p5_fname = get_p5_fname()
  p5_f = open(p5_fname,'a')
  p5_w = p5_f.write

  p5_w('FORMATVERSION 1.0\n')
  p5_w('REM <SNG> <Id> <Influence name> <Focus date>\n')
  p5_w('REM <SND> <Index>\n')

  csv_fname = get_csv_fname()
  csv_f = open(csv_fname,'a')
  csv_w = csv_f.write

  csv_w('ORGN,DSTN,CLSS,WEEK,COEFF\n')

dt = datetime.now().date()
Id = 4000

def write_files(leg,clss,focus_date,dates,seas):
  global Id
  Id += 1
  name = leg.orgn+'_'+leg.dstn+'_'+''.join(clss)+'_'+datetime.now().date().strftime('%Y%m%d')

  p5_fname = get_p5_fname()
  csv_fname = get_csv_fname()

  p5_f = open(p5_fname,'a')
  csv_f = open(csv_fname,'a')

  p5_w = p5_f.write
  csv_w = csv_f.write

  p5_w('SNG '+str(Id)+' "'+name+'" '+focus_date.strftime('%y%m%d')+'\n') 
  
  dt = focus_date
  i = 0
  while i < WEEK_NUM:
    coeff = None
    j = 0
    while j < 4:
      wk_id = str(dt.year-j) + '-' + str(dt.isocalendar()[1]).zfill(2)
      try:
        ind = dates.index(wk_id)
        c = int(100*seas[ind])
        if c < 10:
          c = 10
        coeff = str(c).zfill(3) 
        break
      except:
        pass
      j += 1
    
    if coeff is None:
      coeff = '100' 

    cur_wk = str(dt.year) + '-' + str(dt.isocalendar()[1]).zfill(2)

    p5_w('SND ' + coeff + '\n')
    csv_w(leg.orgn+','+leg.dstn+','+''.join(clss)+','+cur_wk+','+coeff+'\n')

    dt += timedelta(days=7)
    i += 1

  p5_f.close()
  csv_f.close()

if __name__ == '__main__':
  if sys.argv[1] == 'calc':
    write_header_files()
    dto = datetime.now().date()
    dfrom = date(dto.year-5,dto.month,dto.day)
    cur_wn = dto.isocalendar()[1]
    focus_date = dto - timedelta(weeks=WEEK_NUM_BACK)

    prods = get_products()
    for leg in Leg.get_managed_legs():
      for prod in prods.keys():
        clss = prods[prod]
        try:
          dates,x,trend,seas,rem = get_coeffs(leg,dfrom,dto,clss)
          write_files(leg,clss,focus_date,dates,seas)
        except Exception as e:
          print e
  elif sys.argv[1] == 'show':
    orgn = sys.argv[2]
    dstn = sys.argv[3]
    cls = sys.argv[4]
    dt = sys.argv[5]

    dto = date(int(dt[:4]),int(dt[4:6]),int(dt[6:]))
    dfrom = date(dto.year-5,dto.month,dto.day)
    leg = Leg(orgn,dstn)
    clss = list(cls)

    show_decompose(leg,dfrom,dto,clss)
  else:
    pass
  

    
