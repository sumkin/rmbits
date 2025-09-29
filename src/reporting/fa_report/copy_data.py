import os
import sys
import ConfigParser
from datetime import datetime,timedelta

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector

def copy_data_fl(dfroms,dtos):

    # Because this function copies data
    # from compartment table,
    # it should be executed after
    # the function which copies compartment
    # level data.
    
    or_curs = dbConnector.get_or_curs()

    # Truncate forecast accuracy fl table
    print '\t - Truncating table and dropping indices'
    q = "TRUNCATE TABLE forecast_accuracy_fl;"
    or_curs.execute(q)

    try:
        q = "DROP INDEX orgn_dstn ON forecast_accuracy_fl;"
        or_curs.execute(q)

        q = "DROP INDEX fdccd ON forecast_accuracy_fl;"
        or_curs.execute(q)
    except:
        pass

    print '\t - Copying data...'
    q = "SELECT orgn,dstn,fltnum,dptdt,daysprior,SUM(consfnldmd),SUM(booked)\
         FROM forecast_accuracy_cmp\
         WHERE dptdt >= DATE('"+dfroms+"') AND\
               dptdt <= DATE('"+dtos+"')\
         GROUP BY orgn,dstn,fltnum,dptdt,daysprior"
    or_curs.execute(q)
    rows = or_curs.fetchall()
    num = 0
    for row in rows:
        orgn = row[0]
        dstn = row[1]
        fltnum = row[2]
        dptdt = row[3]
        daysprior = row[4]
        consfnldmd = row[5]
        booked = row[6]

        q = "INSERT INTO forecast_accuracy_fl\
             (orgn,dstn,fltnum,dptdt,daysprior,consfnldmd,booked)\
             VALUES\
             ('"+orgn+"','"+dstn+"','"+fltnum+"',\
              DATE('"+dptdt.strftime('%Y-%m-%d')+"'),\
              "+str(daysprior)+","+str(consfnldmd)+","+str(booked)+")"
        or_curs.execute(q)
        num += 1
        if num % 10000 == 0:
            or_conn = dbConnector.get_or_conn()
            or_conn.commit()
    or_conn.commit()

    # Create indices
    print '\t - Creating indices...'
    
    q = "CREATE INDEX orgn_dstn ON forecast_accuracy_fl(orgn,dstn)"
    or_curs.execute(q)

    q = "CREATE INDEX fdccd ON forecast_accuracy_fl(fltnum,dptdt,daysprior)"
    or_curs.execute(q)

    return dfroms,dtos

def copy_data_cmp(dfroms,dtos):
    prosuser_curs = dbConnector.get_prosuser_curs()
    or_curs = dbConnector.get_or_curs()

    # Truncate forecast_accuracy cls table
    print '\t - Truncating table and dropping indices'
    q = "TRUNCATE TABLE forecast_accuracy_cmp;"
    or_curs.execute(q)

    try:
      q = "DROP INDEX orgn_dstn ON forecast_accuracy_cmp;"
      or_curs.execute(q)

      q = "DROP INDEX fdccd ON forecast_accuracy_cmp;"
      or_curs.execute(q)
    except:
      pass

    print '\t - Copying data to local database...'
    q = "SELECT orgn,dstn,fltnum,dptdt,cmpsym,daysprior,consfnldmd,booked\
         FROM hleg_compartment\
         WHERE dptdt >= TO_DATE('"+dfroms+"','yyyy-mm-dd') AND\
               dptdt <= TO_DATE('"+dtos+"','yyyy-mm-dd')"
    prosuser_curs.execute(q)
    row = prosuser_curs.fetchone()
    num = 0
    while row is not None:
        orgn       = row[0]
        dstn       = row[1]
        fltnum    = row[2]
        dptdt      = row[3]
        cmp        = row[4]
        daysprior  = row[5]
        consfnldmd = row[6]
        booked = row[7]

        sub_q = "INSERT INTO forecast_accuracy_cmp\
        (orgn,dstn,fltnum,dptdt,cmp,daysprior,consfnldmd,booked)\
        VALUES\
        ('"+orgn+"','"+dstn+"','"+fltnum+"',\
         DATE('"+dptdt.strftime('%Y-%m-%d')+"'),\
         '"+cmp+"',"+str(daysprior)+","+str(consfnldmd)+","+str(booked)+");"
        or_curs.execute(sub_q)
        num += 1
        if num % 10000 == 0:
            or_conn = dbConnector.get_or_conn()
            or_conn.commit()
        row = prosuser_curs.fetchone()

    or_conn.commit()
    
    # Create indices
    print '\t - Creating indices...'
    
    q = "CREATE INDEX orgn_dstn ON forecast_accuracy_cmp(orgn,dstn)"
    or_curs.execute(q)

    q = "CREATE INDEX fdccd ON forecast_accuracy_cmp(fltnum,dptdt,cmp,daysprior)"
    or_curs.execute(q)

    return dfroms,dtos

def copy_data_cls(dfroms,dtos):
    prosuser_curs = dbConnector.get_prosuser_curs()
    or_curs = dbConnector.get_or_curs()

    # Truncate forecast_accuracy cls table
    print '\t - Truncating table and dropping indices'
    q = "TRUNCATE TABLE forecast_accuracy_cls;"
    or_curs.execute(q)

    try:
      q = "DROP INDEX orgn_dstn ON forecast_accuracy_cls;"
      or_curs.execute(q)

      q = "DROP INDEX fdccd ON forecast_accuracy_cls;"
      or_curs.execute(q)
    except:
      pass

    print '\t - Copying data to local database...'
    q = "SELECT orgn,dstn,fltnum,dptdt,cmpsym,clssym,daysprior,consfnldmd,booked\
         FROM hleg_class\
         WHERE dptdt >= TO_DATE('"+dfroms+"','yyyy-mm-dd') AND\
               dptdt <= TO_DATE('"+dtos+"','yyyy-mm-dd')"
    prosuser_curs.execute(q)
    row = prosuser_curs.fetchone()
    num = 0
    while row is not None:
        orgn       = row[0]
        dstn       = row[1]
        fltnum    = row[2]
        dptdt      = row[3]
        cmp        = row[4]
        cls        = row[5]
        daysprior  = row[6]
        consfnldmd = row[7]
        booked = row[8]

        sub_q = "INSERT INTO forecast_accuracy_cls\
        (orgn,dstn,fltnum,dptdt,cmp,cls,daysprior,consfnldmd,booked)\
        VALUES\
        ('"+orgn+"','"+dstn+"','"+fltnum+"',\
         DATE('"+dptdt.strftime('%Y-%m-%d')+"'),\
         '"+cmp+"','"+cls+"',"+str(daysprior)+","+str(consfnldmd)+","+str(booked)+");"
        or_curs.execute(sub_q)
        num += 1
        if num % 10000 == 0:
            or_conn = dbConnector.get_or_conn()
            or_conn.commit()
        row = prosuser_curs.fetchone()

    or_conn.commit()
    
    # Create indices
    print '\t - Creating indices...'
    
    q = "CREATE INDEX orgn_dstn ON forecast_accuracy_cls(orgn,dstn)"
    or_curs.execute(q)

    q = "CREATE INDEX fdccd ON forecast_accuracy_cls(fltnum,dptdt,cmp,cls,daysprior)"
    or_curs.execute(q)

    return dfroms,dtos

def copy_data():
    dto = datetime.now() - timedelta(days=2)
    dfrom = dto - timedelta(days=30)
    
    dtos = dto.strftime('%Y-%m-%d')
    dfroms = dfrom.strftime('%Y-%m-%d')

    print 'Copying compartment table...'  
    copy_data_cmp(dfroms,dtos)
    print 'Copying flight table...'
    copy_data_fl(dfroms,dtos)
    print 'Copying class table...'
    copy_data_cls(dfroms,dtos)

    return dfroms,dtos

if __name__ == '__main__':

    copy_data()


    
    
