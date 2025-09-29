rev = lambda fs,ds,ps: reduce(lambda x,y: x+y,\
  map(lambda f,d,p: f*min(d,p),fs,ds,ps))

def sample_prots(cap,ncls,ps):
  while cap > 0:
    ind = np.random.randint(0,ncls)
    num = np.random.randint(0,cap+1,1)
    ps[ind] += num
    cap -= num

def simulate():
  revs = []
  for i in range(NRUNS):
    ds = [max(0,np.random.normal(mu,sd,1))\
      for mu,sd in zip(mus,sds)]
    ps = [0]*NCLS
    sample_prots(CAP,NCLS,ps)
    revs.append(float(rev(fs,ds,ps)))
  return revs

