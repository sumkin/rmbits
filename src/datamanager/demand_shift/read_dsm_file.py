import sys
from demand_shift_estimate import print_demand_shift_matrix
import pickle

if __name__ == '__main__':
    if len(sys.argv) == 3:
        orgn = sys.argv[1]
        dstn = sys.argv[2]
        file_name = orgn + '-' + dstn + '.pkl'
    elif len(sys.argv) == 4:
        orgn = sys.argv[1]
        hop  = sys.argv[2]
        dstn = sys.argv[3]
        file_name = orgn + '-' + hop + '-' + dstn + '.pkl'
    f = open('output/'+file_name,'rb')
    dsm = pickle.load(f)
    print_demand_shift_matrix(dsm)
    
    
