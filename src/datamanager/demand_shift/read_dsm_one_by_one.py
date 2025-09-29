import os
import sys
import glob
from demand_shift_estimate import print_demand_shift_matrix
import pickle

if __name__ == '__main__':

    path = 'output/'
    for infile in glob.glob(os.path.join(path,'*.pkl')):
        f = open(infile,'rb')
        dsm = pickle.load(f)
        print infile
        print_demand_shift_matrix(dsm)
        raw_input()
    
    
