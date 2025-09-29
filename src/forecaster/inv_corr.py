from numba import jit
from defs import *

@jit
def correct(fs):
    ''' 
    Simple inversion correction.
    Inverted fares are replaced with average
    recursively.
    '''
    while True:
        fixed = False
        for i in range(len(fs)):
            if i != 0:
                if fs[i-1] + EPS < fs[i]:
                    mf = (fs[i-1] + fs[i]) / 2
                    fs[i-1] = mf
                    fs[i] = mf
                    fixed = True
        if not fixed:
            break
    return fixed


