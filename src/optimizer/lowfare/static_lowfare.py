'''
Fares:    f_1 < f_2 < ... < f_n
Demand:   d_1,d_2,...,d_n
Capacity: Q
Strategy: q_1,q_2,...,q_n (q_i seats allocated to i class)
'''


def prod_revenue(fs,ds,qs):
    # Revenue for product-oriented demand.
    assert len(fs) == len(ds) == len(qs)

    # Return value = \sum_{i=1}^n f_i \min\{q_i,d_i\} 
    return sum([f*e for f,e in zip(fs,[min(d,q) for d,q in zip(ds,qs)])]) 

def price_revenue_wc(fs,ds,qs):
   # Revenue for price-oriented demand
   # for the worst case.
   # Later means that if q_i seats open
   # in class i and highest class having 
   # demand is j then highest class gets
   # priority to fill capacity for ith class.
   # In other words higher class demand comes
   # first to fill lower class capacity.
   assert len(fs) == len(ds) == len(qs)
  
   # Redistribute demand in greedy fashion.
   # Start with the highest class demand
   # and put maximum to the lowest available
   # class. Then if some demand remains to
   # the next after lowest and so on.
   # When demand from the highest class got
   # redistributed take the second highest
   # class and do the same and so on...

   bs = [0] * len(ds)    # bookings in classes 
   f_ind = -1             # forward index of class
   for d in ds:
     f_ind += 1
     #print 'Redistribution of demand from class ',f_ind
     for b_ind in range(len(ds)-1,f_ind-1,-1):
       if d == 0:
         break
       # b_ind - backward index. Move from bottom to top.
       cap = qs[b_ind]-bs[b_ind] # capacity left in class.
       if cap > 0:
         put = min(cap,d)     # number of bookings put in class
         bs[b_ind] += put
         d -= put
         #print 'Put ',put,' in class ',b_ind,'. Remained ',d
   #print bs
   rev = sum([f*b for f,b in zip(fs,bs)])
   #print rev
   return rev

def price_revenue_bc(f,d,q):
   # Revenue for price-oriented demand
   # for the best case.
   assert len(f) == len(d) == len(q)

def next_strategy(n,Q):
   if n == 1:
     yield [Q]
   else:
     for q in range(0,Q+1):
       for e in next_strategy(n-1,Q-q):
         yield [q]+e
   

def find_opt_strategy(fs,ds,Q):
   # fs - list of fares
   # ds - list of demands
   # Q  - total capacity
   assert len(fs) == len(ds)   

   # Brute force.
   max_qs  = None
   max_rev = 0
   for qs in next_strategy(len(fs),Q):
     rev = price_revenue_wc(fs,ds,qs)
     if rev > max_rev:
       max_qs = qs      
       max_rev = rev
   print 'Maximum revenue:',max_rev
   print 'Optimal allocation:',max_qs 






