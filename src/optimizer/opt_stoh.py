import numpy as np

f = [100,10]
d = [[10,5],[100,70]]
cap = 150

def upper_greedy_rev(fs,ds,cap):
  cap_rest = cap
  r = 0
  ind = 0
  for e in ds:
    b = min(cap_rest,e)  # How much could we book
    r += fs[ind] * b
    cap_rest = cap_rest - b
    ind += 1
  return r

def lower_greedy_rev(fs,ds,cap):
  fs.reverse()
  ds.reverse()
  r = upper_greedy_rev(fs,ds,cap)
  fs.reverse()
  ds.reverse()
  return r

def eff(fs,ds,ps,cap):
  upper_g_rev = upper_greedy_rev(f,[e[0] for e in d],cap)
  lower_g_rev = lower_greedy_rev(f,[e[0] for e in d],cap)
  r = rev(fs,ds,ps)
  return (float(r) - float(lower_g_rev)) / (float(upper_g_rev) - lower_g_rev) 

def rev(fs,ds,ps):
  '''
  fs = [f1,f2] - fares
  ds = [d1,d2] - demand, sample values
  ps = [p1,p2] - protections
  '''
  r = 0
  ind = 0
  for f in fs:
    r += f * min(ds[ind],ps[ind])
    ind += 1
  return r       

def sim(fs,ds,ps):
  '''
  fs = [f1,f2] - fares
  ds = [[m1,sd1],[m2,sd2]] - mean and sd of demand
  ps = [ps1,ps2] - protection limits
  '''
  revs = []
  effs = []
  for i in range(5000):
    ss = [int(np.random.normal(e[0],e[1],1)) for e in ds]   
    ss = [max(0,e) for e in ss]
    revs.append(rev(fs,ss,ps))
    effs.append(eff(fs,ss,ps,cap))
  return np.mean(revs),np.std(revs),np.mean(effs),np.std(effs)

def rev_greedy(f,d,cap):
  hprot = d[0][0]
  lprot = cap - hprot
  r,r_sd,e,e_sd = sim(f,d,[hprot,lprot])
  return r,r_sd,e,e_sd

def opt_rev_bf(f,d,cap):
  '''
  Find optimal solution (broute force).
  '''
  opt = [0,0]
  opt_r = 0
  opt_r_sd = 0
  opt_e = 0
  opt_e_sd = 0
  for i in range(cap+1):
    hprot = i
    lprot = cap - i
    r,r_sd,e,e_sd = sim(f,d,[hprot,lprot])
    if r > opt_r:
      opt = [hprot,lprot]
      opt_r = r
      opt_r_sd = r_sd
      opt_e = e
      opt_e_sd = e_sd
  return opt,opt_r,opt_r_sd,opt_e,opt_e_sd

if __name__ == '__main__':

  f = [100,10]
  d = [[10,1],[100,100]]
  cap = 100 

  vals = []
  for sd1 in range(1,100,20):
    v = []
    for sd2 in range(1,100,10):
      d[0][1] = sd1
      d[1][1] = sd2
      v.append(int(opt_rev_bf(f,d,cap)[1]))
    vals.append(v)
    print v

  from matplotlib import pyplot as plt

  plt.title('Optimal (broute force)')
  plt.imshow(vals)
  plt.show()

  '''
  print 'Greedy (upper)'
  print '--------------'
  r = upper_greedy_rev(f,[e[0] for e in d],cap)
  print 'Revenue: ',r
  print 
  print 'Greedy (lower)'
  print '--------------'
  r = lower_greedy_rev(f,[e[0] for e in d],cap)
  print 'Revenue: ',r
  print 
  print 'Optimal revenue (broute force)' 
  print '----------------------'
  print opt_rev_bf(f,d,cap) 
<<<<<<< HEAD
  '''
  print
  print 'Revenue (greedy)'
  print '----------------------'
  print rev_greedy(f,d,cap)

 

    
