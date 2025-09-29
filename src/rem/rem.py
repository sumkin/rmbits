import sys
import os
from matplotlib import pyplot as plt
import numpy as np
import ConfigParser

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','optimizer'))

from emsr import *

CAP = 100
NCLS = 26     
NRUNS = 10000

mus = [10 + i*10 for i in range(NCLS)]
mus = np.array(mus)
#print 'mus:',mus

#stds = [28 - i for i in range(NCLS)]
stds = [1] * NCLS
stds = np.array(stds)
#print 'stds:',stds

fs = [5000 - 50*i for i in range(NCLS)]
fs = np.array(fs)
#print 'fs:',fs

rev = lambda fs,ds,ps: reduce(lambda x,y: x+y,map(lambda f,d,p: f*min(d,p),fs,ds,ps)) 

def sample_prots(cap,ncls):
  '''
  Sample protection levels.
  
  @arg cap   Capacity 
  @arg ncls  Number of classes
  @arg ps    Returned protection levels
  ''' 
  ps = np.array([0]*ncls)   
  while cap > 0:
    ind = np.random.randint(0,ncls)
    num = np.random.randint(0,cap+1,1)
    ps[ind] += 1
    cap -= 1
  return ps

def simulate(fs,mus,stds,cap,nruns):
  '''
  Simulates revenue.

  @arg fs     List of fares
  @arg mus    List of means of demand
  @arg stds   List of standart deviations of demand
  @arg cap    Capacity 
  @arg nruns  Number of runs in simulation

  @return   Return list of simulated revenues 
            and corresponding protection levels.
  ''' 
  assert len(fs) == len(mus) == len(stds) 
  ncls = len(fs)
  revs = []
  prots = []
  for i in range(nruns):
    sds = [float(max(0,np.random.normal(mu,std,1))) for mu,std in zip(mus,stds)] # Static demand
    dds = mus # Deterministic demand
    ps = sample_prots(cap,ncls) # Protection limits
    revs.append([])
    revs[i].append(float(rev(fs,sds,ps)))
    revs[i].append(float(rev(fs,dds,ps))) 
    prots.append(ps)
  return revs,prots

def simulate_const(fs,mus,stds,cap,ps,nruns):
  '''
  Simulate revenue with fixed protection limits.

  @arg fs     List of fares
  @arg mus    List of means of demand
  @arg stds   List of standart deviations of demand
  @arg cap    Capacity
  @arg nruns  Number of runs in simulation

  @return   Return list of simulated revenues
            and corresponding protection levels.
  '''
  assert len(fs) == len(mus) == len(stds)
  ncls = len(fs)
  revs = []
  for i in range(nruns):
    sds = [float(max(0,np.random.normal(mu,std,1))) for mu,std in zip(mus,stds)]     
    revs.append(float(rev(fs,sds,ps)))
  return revs

if __name__ == '__main__':

  # Simulate with random protection limits
  revs, prots = simulate(fs,mus,stds,CAP,NRUNS)
  print 'random protections mean:',np.mean(revs)
  print 'random protection std:',np.std(revs)

  # Simulate with EMSRb protection limits
  emsrb_prots = emsrb_prots_cap(fs,mus,stds,CAP)
  print 'emsrb protections:',emsrb_prots
  revs = simulate_const(fs,mus,stds,CAP,emsrb_prots,NRUNS)
  print 'emsrb protections mean:',np.mean(revs)
  print 'emsrb protections std:',np.std(revs)

















  
