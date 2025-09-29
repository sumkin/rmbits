import os
import time
import ConfigParser

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

tsdb_host = config.get('TSDB','host')
tsdb_port = config.get('TSDB','port')

class TSDBPusher:
  def __init__(self):
    self.host = tsdb_host
    self.port = tsdb_port

  def push(self,metric,timestamp,value,tags):
    """Push message to TSDB
       @arg metric --- metric name
       @arg timestamp --- Unix timestamp
       @arg value --- value of metric
       @arg tags --- dictionary of tags (key is tag 
                     name, value is tag value)"""
    cmd = "echo 'put " + metric + " " + str(timestamp) +\
          " " + str(value) + " " +\
          " ".join([k+"="+v for k,v in tags.items()])+"' "+\
          "| nc -w 30 " + self.host + " " + self.port
    os.system(cmd)

if __name__ == '__main__':
  lder = TSDBLoader()
  lder.push('dummy.metric',int(time.time()),34,{'tag1':'A','tag2':'B'})
