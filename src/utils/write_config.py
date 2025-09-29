import ConfigParser

config = ConfigParser.RawConfigParser()

#
#   EMAIL
#
###############################################

config.add_section('IMAP')
config.set('IMAP','Server','157.200.13.47')
config.set('IMAP','User','rerouting')
config.set('IMAP','Pass','Monday04.')

config.add_section('SMTP')
config.set('SMTP','Server','157.200.13.44')
config.set('SMTP','Port','25')

#
#   DBs
#
###############################################

config.add_section('SIEBEL_DB')
config.set('SIEBEL_DB','Server','157.200.88.150')
config.set('SIEBEL_DB','Port','50005')
config.set('SIEBEL_DB','User','guser1')
config.set('SIEBEL_DB','Pass','itc@guest')
config.set('SIEBEL_DB','Name','ANALYTIC')

config.add_section('PROS_DW_DB')
config.set('PROS_DW_DB','Server','dw.finnair.fi')
config.set('PROS_DW_DB','Port','50000')
config.set('PROS_DW_DB','User','ay49514')
config.set('PROS_DW_DB','Pass','82pass04.')
config.set('PROS_DW_DB','Name','DW01')

config.add_section('ADS_DW_DB')
config.set('ADS_DW_DB','Server','dw.finnair.fi')
config.set('ADS_DW_DB','Port','50000')
config.set('ADS_DW_DB','User','ay49514')
config.set('ADS_DW_DB','Pass','82pass04.')
config.set('ADS_DW_DB','Name','DW01')

config.add_section('OR_DB')
config.set('OR_DB','Server','localhost')
config.set('OR_DB','Port','3306')
config.set('OR_DB','User','root')
config.set('OR_DB','Pass','gbpltw')
config.set('OR_DB','Name','or_data')

#
#   PATHS
#
###############################################

config.add_section('PATHS')

config.set('PATHS','root','/home/fnikitin/projects/RandomWalker/rw_src/src')
config.set('PATHS','analyzer','/home/fnikitin/projects/RandomWalker/rw_src/src/analyzer')
config.set('PATHS','datamanager','/home/fnikitin/projects/RandomWalker/rw_src/src/datamanager')
config.set('PATHS','emailui','/home/fnikitin/projects/RandomWalker/rw_src/src/email_ui/src')
config.set('PATHS','forecaster','/home/fnikitin/projects/RandomWalker/rw_src/src/forecaster')
config.set('PATHS','optimizer','/home/fnikitin/projects/RandomWalker/rw_src/src/optimizer')
config.set('PATHS','simulator','/home/fnikitin/projects/RandomWalker/rw_src/src/simulator')
config.set('PATHS','utils','/home/fnikitin/projects/RandomWalker/rw_src/src/utils')
config.set('PATHS','webgui','/home/fnikitin/projects/RandomWalker/rw_src/src/webgui')

config.set('PATHS','data','/home/fnikitin/projects/RandomWalker/rw_data')
config.set('PATHS','graph_db','/home/fnikitin/projects/RandomWalker/rw_data/graph_db')

config.set('PATHS','logs','/home/fnikitin/projects/RandomWalker/rw_logs')
config.set('PATHS','email_logs','/home/fnikitin/projects/RandomWalker/rw_logs/email_logs')

with open('../rw.cfg','wb') as configfile:

    config.write(configfile)

