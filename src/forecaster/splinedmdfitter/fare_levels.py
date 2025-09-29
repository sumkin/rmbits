import numpy as np
from scipy import optimize

from splinedmdfitter import *


def calc(ys,cds,bp,ps):
    '''
    ys  --- vector of yields.
    cds --- cumulative demands.
    bp  --- value of bid price.
    ps  --- new price points.
    '''

    # Price-demand curve.
    Dp = SplineDmdFitter.fit(ys, cds)

    # Demand-price curve.
    def Pd(d):
        y0 = ys[len(ys)-1]
        y1 = ys[0]
        f = lambda x: abs(Dp(x) - d)
        res = optimize.minimize_scalar(f, bounds = (y0,y1), method = "bounded")
        return res.x

    # Price-reveue curve. 
    Rp = lambda x: x * Dp(x)

    # Demand-revenue curve.
    Rd = lambda x: Pd(x) * x

    d, min_d = cds[0], np.inf
    delta = 0.5
    min_diff = np.inf
    while d < cds[len(cds) - 1]:

        Rd_d = Rd(d)
        Rd_d_plus_delta = Rd(d + delta)

        Rd_der = (Rd_d_plus_delta - Rd_d) / delta

        if abs(Rd_der - bp) < min_diff:
            min_diff = abs(Rd_der - bp)
            min_d = d
        
        d += delta

    Dc = min_d
    pc = Pd(min_d)
    Rc = Rd(Dc)

    # Calculate pl and ph prices.
    ps.reverse()
    pl = ps[0]
    for p in ps[1:]:
        if pc < p: 
            ph = p
            break
        pl = p

    # Calculate demands at these points.
    Dl = Dp(pl)
    Dh = Dp(ph)

    # Calculate revenue at these points.
    Rl = Rd(Dl)
    Rh = Rd(Dh)

    if pc >= ps[len(ps)-1]:
        Dh = 0
        Rh = 0

    # Linearlly interpolate.
    if pc <= ps[0]:
        Rc_prime = Rh
    else:
        A = (Rh - Rl) / (Dh - Dl)
        B = Rl - A * Dl
        Rc_prime = A * Dc + B

    # Lost revenue.
    R_lost = Rc - Rc_prime

    return R_lost, pc, Dc


        
if __name__ == "__main__": 
    ys = [900,500,200,100]
    cds = [10,30,80,180]
    bp = 3500
    ps = [850,650,350,250]
    R_lost, dc, pc = calc(ys, cds, bp, ps)
    print("R_lost, dc, pc = ", R_lost, dc, pc)

   
    
    
