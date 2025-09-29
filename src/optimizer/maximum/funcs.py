import numpy as np

A = np.matrix([[1,0,1],[0,1,1]])
p = np.array([100,200,400])
x = np.array([150,20])
c = np.array([100,150])
K = np.array([400,600])
psi = np.array([300,100])
u = np.array([0,1,1])
D = np.array([20,30,40])

def P(p,A,K,x,c):
  xc = x-c
  e = np.exp(xc)
  tmp = K*e
  res = np.matrix(p) - A.transpose().dot(tmp)
  return np.array(res)

def hamiltonian(psi,x,u,D,p,A,K,c):
  '''
  Hamiltonian function.
  Returns the value of Hamiltonian.

  All inputs numpy vectors and matrices.
  '''
  size = psi.shape[0]
  uD = u*D
  return psi[0]*(P(p,A,K,x,c).dot(uD)) + psi[1:]*( A.dot(uD) ) + psi[size] 

def ham_max(psi,A,p,K,x,c):
  '''
  Function returns value of 
  control variables 0 or 1
  when hamiltonian is maximzied.
  '''
  res = psi.dot(A) - p + A.transpose().dot(K*np.exp(x-c))
  r = np.asarray(res).reshape(-1)
  return [1 if e > 0 else 0 for e in r]

def RHS(x0,x,psi,p,c,K,u,D,A):
  '''
  Right-hand side of DE.
  '''
  xc = x-c
  e = np.exp(xc)
  tmp = K*e

  r1 = P(p,A,K,x,c)
  r2 = A
  r3 = (-A.transpose()).dot(tmp)  
  r4 = p - psi.dot(A) 
 
  r = np.vstack([r1,r2,r3,r4])
  r = r.dot(u*D)
  r = np.asarray(r).reshape(-1)

  return r 

if __name__ == '__main__':
  x0 = 0
  print RHS(x0,x,psi,p,c,K,u,D,A)
  #print ham_max(psi,A,p,K,x,c)




