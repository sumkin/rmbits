import os
import sys
import ConfigParser
from time import sleep

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

class SchedulerDataReader:

  def __init__(self,dfrom,dto):
    self.dfrom = dfrom
    self.dto = dto



