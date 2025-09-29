from numba import jit
import numpy as np

from inv_corr import correct

@jit
def dc_calc(mp, f, d):
    # Fares shouldn't be inverted.
    # Correct them.
    correct(f)

    mres = np.zeros(len(mp)) # Marginal demand.
    mres[0] = d[0]
    sm = d[0]
    res = np.zeros(len(mp))
    res[0] = d[0]

    starti = None
    for i in range(len(mp)):
        if mp[i] == f[i]:
            # Fix for NRMS data.
            # If marginal fare is equal to fare
            # then all demand above should be zero.
            starti = i
    # starti is the lowest class 
    # where mp == f.

    # It could happen that highest class mp != f.
    if starti is None:
        starti = 0

    # All demand above is equal zero.
    for i in range(starti):
        mres[i] = 0
        res[i] = 0
        sm += d[i]
    
    # Accomodate all demand to the class starti.
    mres[starti] = sm
    res[starti] = sm
    starti += 1

    for i in range(len(mp))[starti:]:
        assert abs(mp[i] - f[i]) > 0
        d = ((f[i] - f[i-1]) * sm)/(mp[i] - f[i])
        if d < 0.0:
            d = 0.0
        assert d >= 0
        mres[i] = d
        sm += d
        res[i] = sm
    return res, mres


if __name__ == "__main__":
    #mp = [477.97799699999996, 177.003006, 141.977997, 70.19699859999999, 35.9720001, 1.74800003, -83.6679993, -88.8529968, -94.0370026]
    #fs = [488, 456, 406, 369, 345, 321, 275, 250, 202]
    #dd = [0.00535300048, 0.000537800021, 0.00110250001, 0.0008057000229999999, 0.00039200001600000003, 0.00018430000599999998, 0.0, 0.0, 0.0]
    #d,md = dc_calc(mp, fs, dd)
    mps =  [779.0, 580.0, 480.0, 430.0, 406.0, 381.0, 348.0, 292.0, 203.468, 182.326, 126.09899999999999, 69.873, 60.048, 36.661, 3.855, -3.855]
    fs =  [779.0, 581.0, 483.0, 433.0, 409.0, 384.0, 354.0, 296.0, 251.0, 224.0, 200.0, 176.0, 160.0, 138.0, 126.0, 81.0]
    ad =  [2.7999999999999996e-05, 5.5e-05, 0.00013820000000000003, 0.00017820000000000002, 0.0001509, 0.00020519999999999997, 0.0003583, 0.0012599, 0.0011997, 0.0017149, 0.004081100000000001, 0.0022177, 0.0031969999999999993, 0.0064889, 0.0019186000000000003, 0.0]
    d,md = dc_calc(mps,fs,ad)
    print(fs)
    print(mps)
    print(ad)
    print(d.tolist())
    print(md.tolist())


  
