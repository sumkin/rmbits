import numpy as np

class Demand:
  def __init__(self,t0,T,n):
    self.t0 = t0
    self.T = T
    self.n = n

  def get(self):
    res = []
    for i in range(self.n):
      res.append(lambda x: x + self.n)
    return res

if __name__ == '__main__':
  D = Demand(0,365,3).get()
  print D[0](50)
  print D[1](60)
  print D[2](70)  
    



