import sys
import os
import ConfigParser

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from airport import *

if __name__ == '__main__':

    airport_pairs = airport.get_airport_pairs()
    for airport_pair in airport_pairs:

        print airport_pair

