import os
import sys
import pickle
import ConfigParser
import numpy as np
from matplotlib import pyplot as plt
from datetime import date

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))
sys.path.append(config.get('PATHS','emailui'))

from leg import Leg

TOO_LESS_OB_FLIGHTS = -1
INCREASE_OB_LVL = 0.1

def make_analysis(leg,data,dfrom,dto):
  """Make overbooking analysis.
     Returns picture file name,
     optimal overbooking level and
     actual historical overbooking 
     level.

     Data comes in the following format:
     ['YYYY-MM-DD': [ob_actual,ob_allowed,costs,gains],..."""
  data1 = [e for e in data if e[1][0] is not None and e[1][0] > 0.0]
  data2 = [e[1] for e in data1 if e[0] >= dfrom.strftime('%Y-%m-%d') and e[0] < dto.strftime('%Y-%m-%d')]
  data3 = [[e[0],e[2]-e[3]] for e in data2]
 
  if len(data3) < 1:
    return None,TOO_LESS_OB_FLIGHTS,None 

  # Observations
  x = np.array([e[0] for e in data3])
  y = np.array([e[1] for e in data3])

  # Fit polynomial
  z = np.polyfit(x,y,2)
  p = np.poly1d(z)
  xp = np.linspace(0.0,0.1,100)

  # Calculate optimal overbooking and current
  act_ob_lvl = np.mean(x)

  prev_e = None
  for e in xp:
    if prev_e is None:
      pass
    elif p(e) >= p(prev_e):
      pass
    else:
      break
    prev_e = e

  opt_ob_lvl = prev_e
  
  if opt_ob_lvl == xp[len(xp)-1]:
    opt_ob_lvl = INCREASE_OB_LVL # Indicates that OB level should be increased

  # Draw figures
  fig = plt.figure()
  plt.plot(x,y,'.',label='Observations')
  plt.plot(xp,p(xp),'-',label='Fitted')
  label_act = 'Current OB ('+str(round(act_ob_lvl,3))+")"
  label_opt = 'Optimal OB ('+(str(round(opt_ob_lvl,3)) if opt_ob_lvl != INCREASE_OB_LVL else 'Undef')+")"
  plt.vlines([act_ob_lvl],plt.axis()[2],plt.axis()[3],colors='k',label=label_act,linestyle='dashed')
  plt.vlines([opt_ob_lvl],plt.axis()[2],plt.axis()[3],colors='r',label=label_opt,linestyle='dashed')
  plt.title(leg.orgn+'-'+leg.dstn)
  plt.legend()
  pic_fname = leg.orgn+'-'+leg.dstn+'.png'
  fig.savefig(config.get('PATHS','ob_data')+'/'+pic_fname)

  return pic_fname,act_ob_lvl,opt_ob_lvl

def send_ob_report(dfrom,dto,leg=None):
  legs = Leg.get_managed_legs()
  for leg in legs:
    # FIXME: Now reading from files,
    # but should take this from DB.
    fname = config.get('PATHS','ob_data')+'/'+leg.orgn+'-'+leg.dstn+'.pkl'
    try:
      data = pickle.load(open(fname,'rb'))
      pic_fname,act_ob_lvl,opt_ob_lvl = make_analysis(leg,data,dfrom,dto)

    except Exception as e:
      print e
      # No data
      pass

if __name__ == '__main__':
  if len(sys.argv) != 3:
    exit('Usage: python send_ob_report.py YYYY-MM-DD YYYY-MM-DD')

  dfrom = sys.argv[1]
  dto = sys.argv[2]

  dfrom_y,dfrom_m,dfrom_d = [int(e) for e in dfrom.split('-')]
  dto_y,dto_m,dto_d = [int(e) for e in dto.split('-')]

  dfrom = date(dfrom_y,dfrom_m,dfrom_d)
  dto = date(dto_y,dto_m,dto_d)

  send_ob_report(dfrom,dto)


