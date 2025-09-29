import os
import sys
import ConfigParser
from scipy import *
from pylab import *
import sqlite3

# Read config
config = ConfigParser.RawConfigParser()
rel_path = '../../../rw.cfg'
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),rel_path)
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from dt_func import *
from datetime import timedelta
from numpy import *

sqlite3_fldr = config.get('PATHS','sqlite')

if __name__ == '__main__':
    carrier = sys.argv[1]
    orgn    = sys.argv[2]
    dstn    = sys.argv[3]

    fname = sqlite3_fldr+'/'+carrier+'_'+orgn+'_'+dstn+'.db'
    conn = sqlite3.connect(fname)
    c = conn.cursor()

    # Define minimum and maximum dates
    q = "SELECT MIN(dfrom) FROM prices"
    c.execute(q)
    row = c.fetchone()
    min_dt = date_str_to_date(row[0])

    q = "SELECT MAX(dto) FROM prices"
    c.execute(q)
    row = c.fetchone()
    max_dt = date_str_to_date(row[0])

    dim = (max_dt - min_dt).days
    dim = 30

    l = []
    for i in range(0,dim):
        l.append([])
        for j in range(0,dim):
            l[i].append(0)

    q = "SELECT dfrom,dto,price FROM prices ORDER BY dfrom,dto"
    c.execute(q)
    row = c.fetchone()
    while row is not None:
        dfrom = date_str_to_date(row[0])
        dto   = date_str_to_date(row[1])
        price = float(row[2]) 

        i = (dfrom - min_dt).days
        j = (dto - min_dt).days   
        if i < dim and j < dim:    
            l[j][i] = price
 
        row = c.fetchone()
    ar = array(l)

    figure(1)
    imshow(ar,origin='lower',interpolation='nearest')
    grid(True)
    show()

    savefig('aeroflot_prices')

    
