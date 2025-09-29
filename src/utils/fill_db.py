from xml.dom.minidom import parse, parseString
from datetime import datetime
import MySQLdb

conn = MySQLdb.connect(host = 'localhost',
                       user = 'root',
                       passwd = 'gbpltw',
                       db = 'or_data')
curs = conn.cursor()

print 'Started ', datetime.now()

in_file = './sched.xml'
f = open(in_file,'r')
d = {'CR':None,'FN':None,'SDW':None,'LO':None,'LD':None}
for line in f:
    try:
      ind = line.index('<CR>')
      tag = 'CR'
    except:
      try:
        ind = line.index('<FN>')
        tag = 'FN'
      except:
        try:
          ind = line.index('<SDW>')
          tag = 'SDW'
        except:
          try:
            ind = line.index('<LO>')
            tag = 'LO'
          except:
            try:
              ind = line.index('<LD>')
              tag = 'LD'
            except:
              tag = ''

    if tag != '':
        start_ind = line.index('<'+tag+'>')
        start_ind += len(tag) + 2
        end_ind = line.index('</'+tag+'>')
        content = line[start_ind:end_ind].strip()

    if tag == 'CR':
      # Check that everything is in dictionary and flush
      if d['CR'] is not None and d['FN'] is not None and\
         d['SDW'] is not None and d['LO'] is not None and d['LD'] is not None:
        q = "INSERT INTO sched_tmp ('cr','fn','sdw','lo','ld') VALUES\
             ('"+d['CR']+"','"+d['FN']+"','"+d['SDW']+"','"+d['LO']+"','"+d['LD']+"')"
        curs.execute(q)
      d = {'CR': content, 'FN': None, 'SDW': None, 'LO': None, 'LD': None}
    elif tag == 'FN':
      # Check that FL,CR are filled and others empty
      d['FN'] = content
    elif tag == 'SDW':
      # Check that FL,CR,DDT are filled and others empty
      d['SDW'] = content
    elif tag == 'LO':
      # Check that FL,CR,DDT,SDW are filled and others empty
      d['LO'] = content
    elif tag == 'LD':
      # Check that FL,CR,DDT,SDW,LO are filled and others empty
      d['LD'] = content
  
 

