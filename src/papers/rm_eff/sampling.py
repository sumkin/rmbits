import numpy as np

def sample(n,cap):
  smpl = [int(np.random.uniform(0,cap,1)) for e in range(n)]
  sm = sum(smpl)
  return [ int(round((float(e) * cap)/sm)) for e in smpl]

if __name__ == '__main__':
  res = sample(26,100) 
  print res
  print 'len:',len(res)
  print 'sum:',sum(res)
