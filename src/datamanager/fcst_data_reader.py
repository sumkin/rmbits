import os
import sys
import ConfigParser
from time import sleep
from datetime import date

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

from db_connector import dbConnector

class FcstDataReader:

  def __init__(self,orgn=None,dstn=None,fltnum=None,cls=None,daysprior=None,dow = None,sh = None):
    self.orgn = orgn
    self.dstn = dstn
    self.fltnum = fltnum
    self.cls = cls
    self.daysprior = daysprior
    self.dow = dow
    self.sh = sh

  def get_fcst_err(self,dfrom,dto):
    '''
    Generator which returns dictionary
    {'orgn': 'HEL', 'dstn': 'OUL', 'fltnum': '00005', 'dptdt': '2013-04-02',
     'daysprior': '20', 'cls': 'Z', 'err': '10.0'}
    [dfrom,dto] is departure range
    '''
    curs = dbConnector.get_prosuser_curs()
    q = "SELECT orgn,dstn,fltnum,dptdt,clssym,consfnldmd\
         FROM hleg_class\
         WHERE dptdt >= TO_DATE('" + dfrom.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
               dptdt <= TO_DATE('" + dto.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
               daysprior = -1\
         ORDER BY orgn,dstn,fltnum,clssym"
    curs.execute(q)
    rows = curs.fetchall()
    for row in rows:
      orgn = row[0]
      dstn = row[1]
      fltnum = row[2]
      dptdt = row[3]
      cls = row[4]
      fcst = row[5]  
      
      q = "SELECT daysprior,consfnldmd\
           FROM hleg_class\
           WHERE dptdt >= TO_DATE('" + dfrom.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                 dptdt <= TO_DATE('" + dto.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                 orgn = '" + orgn + "' AND\
                 dstn = '" + dstn + "' AND\
                 fltnum = '" + fltnum + "' AND\
                 dptdt = TO_DATE('" + dptdt.strftime('%Y-%m-%d') + "','yyyy-mm-dd') AND\
                 clssym = '" + cls + "'"
      curs.execute(q)
      srows = curs.fetchall()
      for srow in srows: 
        daysprior = srow[0]
        val = srow[1]
        yield [orgn,dstn,fltnum,dptdt.strftime('%Y-%m-%d'),cls,daysprior,val-fcst]

  def get_fcst_vals(self,typ,pool_id):
    cursor = dbConnector.get_prosuser_curs()
    fcst_vals = {}
    if self.sh is not None:
      for dr in self.sh.get_date_ranges(pool_id):
        dfrom = dr.get_dfrom()
        dto = dr.get_dto()
        if typ == 'cons':
          q = "SELECT dptdt,consfnldmd FROM hleg_class\
               WHERE crr = 'AY' AND orgn = '" + self.orgn + "' AND\
                     daysprior = '" + str(self.daysprior) + "' AND\
                     dstn = '" + self.dstn + "' AND\
                     fltnum = '" + self.fltnum + "' AND\
                     clssym = '" + self.cls + "' AND\
                     DAYOFWEEK(dptdt) = " + str(self.dow) + " AND\
                     dptdt >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
                     dptdt <= DATE('" + dto.strftime('%Y-%m-%d') + "')\
               ORDER BY dptdt" 
        elif typ == 'uncons':
          q = "SELECT dptdt,uncdmd FROM hleg_class\
               WHERE crr = 'AY' AND orgn = '" + self.orgn + "' AND\
                     daysprior = '" + str(self.daysprior) + "' AND\
                     dstn = '" + self.dstn + "' AND\
                     fltnum = '" + self.fltnum + "' AND\
                     clssym = '" + self.cls + "' AND\
                     DAYOFWEEK(dptdt) = " + str(self.dow) + " AND\
                     dptdt >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
                     dptdt <= DATE('" + dto.strftime('%Y-%m-%d') + "')\
               ORDER BY dptdt"
        else:
          print 'Unkonwn type in fcstDataReader->get_fcst_vals()!'
          assert 0
          num_atts = 100
          while num_atts > 0:
            try:
              cursor.execute(q)
              rows = cursor.fetchall()
              break
            except:
              es = EmailSender()
              mail_text = 'Query failed in get_fcst_vals(). attempt ' + str(num_atts)
              es.send_quick('Query failed',mail_text)
              num_atts = num_atts - 1
              sleep(10) 
            for row in rows:
              fcst_vals[row[0]] = row[1]
    else:
      # write query for all split history pools
      #if self.dow is None:
      #    if typ == 'cons'     
      pass
    return fcst_vals

  def get_fcst_outl_vals(self,type_,pool_id):
    # Get forecast values which were marked as outliers
    cursor = dbConnector.get_prosuser_curs()

    fcst_vals = {}

    for dr in self.sh.get_date_ranges(pool_id):
      dfrom = dr.get_dfrom()
      dto = dr.get_dto()

      if type_ == 'cons':
        q = "SELECT dptdt,consfnldmd FROM hsegment_class\
             WHERE crr = 'AY' AND orgn = '" + self.orgn + "' AND\
                   dstn = '" + self.dstn + "' AND\
                   daysprior = '" + str(self.daysprior) + "' AND\
                   fltnum = '" + self.fltnum + "' AND\
                   clssym = '" + self.cls + "' AND\
                   DAYOFWEEK(dptdt) = " + str(self.dow) + " AND\
                   dptdt >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
                   dptdt <= DATE('" + dto.strftime('%Y-%m-%d') + "') AND\
                   outlier = 'Y'\
             ORDER BY dptdt"
      elif type_ == 'uncons':
        q = "SELECT dptdt,uncdmd FROM hsegment_class\
             WHERE crr = 'AY' AND orgn = '" + self.orgn + "' AND\
                   dstn = '" + self.dstn + "' AND\
                   daysprior = '" + str(self.daysprior) + "' AND\
                   fltnum = '" + self.fltnum + "' AND\
                   clssym = '" + self.cls + "' AND\
                   DAYOFWEEK(dptdt) = " + str(self.dow) + " AND\
                   dptdt >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
                   dptdt <= DATE('" + dto.strftime('%Y-%m-%d') + "') AND\
                   outlier = 'Y'\
             ORDER BY dptdt"
      else:
        print 'Unknown type in fcstDataReader->get_fcst_vals()'
        assert 0                    

    cursor.execute(q)
    rows = cursor.fetchall()
    for row in rows:
      fcst_vals[row[0]] = row[1]
 
    return fcst_vals         

  def get_booked_vals(self,pool_id):
    cursor = dbConnector.get_prosuser_curs()
    booked_vals = {}
    for dr in self.sh.get_date_ranges(pool_id):
      dfrom = dr.get_dfrom()
      dto = dr.get_dto()

      q = "SELECT dptdt,booked FROM hleg_class\
           WHERE crr = 'AY' AND orgn = '" + self.orgn + "' AND\
                 dstn = '" + self.dstn + "' AND\
                 fltnum = '" + self.fltnum + "' AND\
                 clssym = '" + self.cls + "' AND\
                 DAYOFWEEK(dptdt) = " + str(self.dow) + " AND\
                 daysprior = '" + str(self.daysprior) + "' AND\
                 dptdt >= DATE('" + dfrom.strftime('%Y-%m-%d') + "') AND\
                 dptdt <= DATE('" + dto.strftime('%Y-%m-%d') + "')\
           ORDER BY dptdt"

      num_atts = 100
      while num_atts > 0:
        try:
          cursor.execute(q)
          rows = cursor.fetchall()
          break
        except:
          es = EmailSender()
          mail_text = 'Query failed in get_fcst_vals(). attempt ' + str(num_atts)
          es.send_quick('Query failed',mail_text)
          num_atts = num_atts - 1
          sleep(10)

        for row in rows:
          booked_vals[row[0]] = row[1] 
      return booked_vals

  def get_fcst_minus_booked_vals(self,typ,pool_id):
    fcst_vals = self.get_fcst_vals('uncons',pool_id)
    booked_vals = self.get_booked_vals(pool_id)

    dptdts = list(frozenset(fcst_vals.keys()).intersection(booked_vals.keys()))
    fcst_minus_booked_vals = []
    for dptdt in dptdts:
      fcst_minus_booked_vals.append(fcst_vals[dptdt] - booked_vals[dptdt])
    return fcst_minus_booked_vals
      
  def get_obs_vals(self,typ):
    pass

if __name__ == '__main__':
  fdr = FcstDataReader()
  dfrom = date(2013,5,1)
  dto = date(2013,6,1)
  for v in fdr.get_fcst_err(dfrom,dto):
    print v    
        
