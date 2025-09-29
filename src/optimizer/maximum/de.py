import numpy as np
from demand import Demand

class DE:
  def __init__(self,A,p,K,c,D):
    self.A = A  # product matrix with n rows, m columns
    self.p = p  # price vector with m elements
    self.K = K  # overbooking penalty vector with n elements
    self.c = c  # capacity vector with n elements 
    self.D = D  # demand functions vector with n elements

  def step(self,x,psi,u,t):
    D = np.array([f(t) for f in self.D])
    xc = x[1:] - self.c
    exc = np.exp(xc)
    Kexc = self.K * exc 
    Kexcd = np.diag(Kexc)
    P = self.p - self.A.transpose().dot(Kexc)      
    psim = (-A.transpose().dot(Kexcd)).transpose()
    
    m = np.vstack([P,A,psim,p - psi[:-1].dot(A)])
    x = x + np.asarray(m.dot(u*D)).reshape(-1)[:x.shape[0]]
    psi = psi + np.asarray(m.dot(u*D)).reshape(-1)[x.shape[0]:]    

    return x,psi

if __name__ == '__main__':
  A = np.matrix([[1,0,1],[0,1,1]])
  p = np.array([200,400,500])
  K = np.array([400,600])
  c = np.array([100,200]) 
  D = Demand(0,365,3).get()

  de = DE(A,p,K,c,D)
  x = np.array([0,0,0])
  psi = np.array([0,0,0])
  u = np.array([0,0,0])

  for t in range(365):
    #print t,
    x,psi = de.step(x,psi,u,t)
    #print x,psi
  
