import sys
from datetime import date, timedelta

from db_connector import dbConnector
from leg import *
from flight import *

class CRMCase:
  def __init__(self, case_id):
    self.case_id = case_id

  def get_cmpnstn_list(self):
    # FIXME consider storing this value in object
    siebel_curs = dbConnector.get_siebel_curs()
    siebel_curs.execute("SELECT case_cmpnstn_id, compenation_status_description,\
                                cmpnstn_type_desc, paid_to, cmpnstn_amt, reason_desc\
                         FROM case_compensation_fact\
                         WHERE case_id='" + self.case_id + "'")
    case_list = [list(case) for case in siebel_curs.fetchall()]
    return case_list

  def get_num_pax(self):
    siebel_curs = dbConnector.get_siebel_curs()
    siebel_curs.execute("SELECT pax_cnt FROM case_fact WHERE case_id='" + self.case_id + "'")
    try:
      pax_cnt = siebel_curs.fetchone()[0]
    except:
      pax_cnt = None
    return pax_cnt if pax_cnt is not None else 0

  def get_cat_list(self):
    ans = []
    siebel_curs = dbConnector.get_siebel_curs()
    siebel_curs.execute("SELECT cat_nm,\
                                sub_cat_nm,\
                                child_sub_cat_nm\
                         FROM category_dim_h\
                         WHERE case_id = '" + self.case_id + "'")
    cat_list = []
    for cat in siebel_curs.fetchall():
      cat0 = '' if cat[0] is None else cat[0]
      cat1 = '' if cat[1] is None else cat[1]
      cat2 = '' if cat[2] is None else cat[2]
      ans.append(cat0+'/'+cat1+'/'+cat2)
    return ans

  def get_calendar_date(self,c_key):
    curs = dbConnector.get_siebel_curs()
    q = "SELECT calendar_date\
         FROM calendar_dim\
         WHERE calendar_key = " + str(c_key)
    curs.execute(q)
    row = curs.fetchone()
    return row[0].strftime('%Y-%m-%d') 

  def get_flight_nbr(self):
    ans = None
    curs = dbConnector.get_siebel_curs()
    q = "SELECT flight_nbr,flight_date\
         FROM case_fact\
         WHERE case_id = '" + self.case_id + "'"
    curs.execute(q)
    row = curs.fetchone()

    if row[0] is not None:
      fn = row[0]
      fd = self.get_calendar_date(row[1])
      carr = fn[:2]
      try:
        nbr = int(fn[2:])
      except:
        nbr = 0
      ans = [carr,nbr,fd]
    else:
      ans = ['XX','00000','1970-01-01']

    return ans

  def get_flight(self):
    '''
    ans = []
    curs = dbConnector.get_siebel_curs()
    q = "SELECT dep_city,arr_city,airline_nm,flight_nbr,flight_date\
         FROM case_flight_fact\
         WHERE case_id = '" + self.case_id + "'"
    curs.execute(q)
    rows = curs.fetchall()
    if len(rows) == 1:
      row = rows[0]
      orgn = row[0]
      dstn = row[1]
      carr = row[2]
      fltnum = row[3]
      flight_date = self.get_calendar_date(row[4])
      ans.append([orgn,dstn,carr,fltnum,flight_date])
    else:
      for row in rows:
        orgn = row[0]
        dstn = row[1]
        carr = row[2]
        fltnum = row[3]
        flight_date = self.get_calendar_date(row[4])
        a_carr,a_nbr = self.get_flight_nbr()
        if carr == a_carr and int(fltnum) == int(a_nbr):
          ans.append([orgn,dstn,carr,fltnum,flight_date])
    '''
    carr,nbr,fd = self.get_flight_nbr()
    orgn,dstn = Flight.get_orgn_dstn(nbr)
    return [orgn,dstn,carr,str(nbr),fd]

  def _get_flight(self):
    ans = []
    siebel_curs = dbConnector.get_siebel_curs()
    siebel_curs.execute("SELECT dep_city,\
                                arr_city,\
                                flight_nbr,\
                                calendar_date\
                         FROM case_flight_fact\
                         LEFT OUTER JOIN calendar_dim\
                           ON case_flight_fact.flight_date = calendar_dim.calendar_key\
                         WHERE case_id = '"+self.case_id+"' AND\
                               airline_nm='AY'\
                         ORDER BY calendar_date ASC")
    rows = siebel_curs.fetchall()
    for row in rows:
      try:
        orgn = row[0]
      except:
        orgn = ''
      try:
        dstn = row[1]
      except:
        dstn = ''
      try:
        fltnum = str(row[2]).zfill(5)
      except:
        fltnum = ''
      try:
        dptdt = row[3].strftime('%Y-%m-%d')
      except:
        dptdt = ''
      ans.append([orgn,dstn,fltnum,dptdt])
    return ans

  def rec_cre_dt(self):
    ans = []
    siebel_curs = dbConnector.get_siebel_curs()
    siebel_curs.execute("SELECT calendar_date\
                         FROM case_compensation_fact\
                         LEFT OUTER JOIN calendar_dim\
                           ON case_compensation_fact.rec_cre_dt = calendar_dim.calendar_key\
                         WHERE case_id = '"+self.case_id+"'")
    row = siebel_curs.fetchone()
    return row[0].strftime('%Y-%m-%d')

  def get_fltnum_date_list(self):
    siebel_curs = dbConnector.get_siebel_curs()
    siebel_curs.execute("SELECT flight_nbr, calendar_date\
                         FROM case_flight_fact\
                         LEFT OUTER JOIN calendar_dim\
                              ON case_flight_fact.flight_date = calendar_dim.calendar_key\
                         WHERE case_id = '" + self.case_id + "'")
    ret_val = []
    for flt_date in siebel_curs.fetchall():
      ret_val.append({'fltnum': flt_date[0], 'date': flt_date[1]})

    return ret_val                          

  def get_cmpn_amt(self):
    ans = []
    siebel_curs = dbConnector.get_siebel_curs()
    siebel_curs.execute("SELECT compenation_status_description, cmpnstn_amt, reason_desc\
                         FROM case_compensation_fact\
                         WHERE case_id='" + self.case_id + "'")
    cmpns = siebel_curs.fetchall()
    for cmpn in cmpns:
      stat = cmpn[0]
      amt = cmpn[1]
      reason = '' if cmpn[2] is None else cmpn[2]
      ans.append([stat,amt,reason])
    return ans

  @staticmethod
  def get_route_case_list(orgn, dstn, fltnum):
    siebel_curs = dbConnector.get_siebel_curs()
    siebel_curs.execute("SELECT case_flight_fact.case_id,\
                                case_flight_fact.pax_cnt,\
                                case_fact.case_status_desc,\
                                case_fact.assgn_cat_cd\
                         FROM case_flight_fact\
                         LEFT OUTER JOIN case_fact\
                              ON case_flight_fact.case_id = case_fact.case_id\
                         WHERE case_flight_fact.dep_city='" + orgn + "' AND\
                               case_flight_fact.arr_city='" + dstn + "' AND\
                               case_flight_fact.airline_nm='AY'")
    case_list = [list(case) for case in siebel_curs.fetchall()]
    return case_list

  @staticmethod
  def get_flt_case_list(orgn, dstn, fltnum):
    # select all cases
    siebel_curs = dbConnector.get_siebel_curs()
    siebel_curs.execute("SELECT case_flight_fact.case_id,\
                                case_flight_fact.pax_cnt,\
                                case_fact.case_status_desc,\
                                case_fact.assgn_cat_cd\
                         FROM case_flight_fact\
                         LEFT OUTER JOIN case_fact\
                              ON case_flight_fact.case_id = case_fact.case_id\
                         WHERE case_flight_fact.flight_nbr='" + fltnum[1:] + "' AND\
                               case_flight_fact.dep_city='" + orgn + "' AND\
                               case_flight_fact.arr_city='" + dstn + "' AND\
                               case_flight_fact.airline_nm = 'AY'")
    case_list = [list(case) for case in siebel_curs.fetchall()]
    ret_val_list = []
    for case in case_list:
      ret_val = []
      case_obj = CRMCase(case[0])
      cmpn = case_obj.get_cmpn_amt()

      ret_val.append(case[0]) # case id
      ret_val.append(case_obj.get_num_pax()) # number of passengers
      ret_val.append(case[2]) # case status
      ret_val.append(case[3]) # category
      ret_val.append(cmpn['cmpn']['amt']) # case compensation amount
      ret_val.append(cmpn['reason_list']) # reason description
      ret_val.append(case_obj.get_cat_list()) # list of categories / subcategories / child subcategories

      ret_val_list.append(ret_val)

    return ret_val_list

  @staticmethod
  def get_fltdep_case_list(orgn, dstn, fltnum, date):
    siebel_curs = dbConnector.get_siebel_curs()
    siebel_curs.execute("SELECT case_flight_fact.case_id,\
                                case_flight_fact.pax_cnt,\
                                case_fact.case_status_desc,\
                                case_fact.assgn_cat_cd\
                         FROM case_flight_fact\
                         LEFT OUTER JOIN calendar_dim\
                              ON case_flight_fact.flight_date = calendar_dim.calendar_key\
                         LEFT OUTER JOIN case_fact\
                              ON case_flight_fact.case_id = case_fact.case_id\
                         WHERE case_flight_fact.flight_nbr='" + fltnum[1:] + "' AND\
                               case_flight_fact.dep_city='" + orgn + "' AND\
                               case_flight_fact.arr_city='" + dstn + "' AND\
                               calendar_dim.calendar_date='" + date + "' AND\
                               case_flight_fact.airline_nm = 'AY'")
    # (case_id, pax_cnt, case_status_desc, assgn_cat_cd)
    case_list = [list(case) for case in siebel_curs.fetchall()]
    ret_val_list = []
    for case in case_list:
      ret_val = []
      case_obj = CRMCase(case[0])
      cmpn = case_obj.get_cmpn_amt()
      ret_val.append(case[0])                 # case id
      ret_val.append(case_obj.get_num_pax())  # number of passengers
      ret_val.append(case[2])                 # case status
      ret_val.append(case[3])                 # category
      ret_val.append(cmpn['cmpn']['amt'])      # case compensation amount
      ret_val.append(cmpn['reason_list'])     # reason description
      ret_val.append(case_obj.get_cat_list()) # list of categories / subcategories / child subcategories

      ret_val_list.append(ret_val)
    return ret_val_list

  @staticmethod
  def get_dep_db_case_list(orgn, dstn, fltnum, dt):
    siebel_curs = dbConnector.get_siebel_curs()
    siebel_curs.execute(" SELECT DISTINCT category_dim_h.case_id\
                          FROM category_dim_h\
                          LEFT OUTER JOIN case_flight_fact\
                               ON category_dim_h.case_id = case_flight_fact.case_id\
                          LEFT OUTER JOIN calendar_dim\
                               ON case_flight_fact.flight_date = calendar_dim.calendar_key\
                          WHERE sub_cat_nm = 'Overbooking' AND\
                                case_flight_fact.dep_city = '" + orgn + "' AND\
                                case_flight_fact.arr_city = '" + dstn + "' AND\
                                case_flight_fact.flight_nbr = '" + fltnum[1:] + "' AND\
                                calendar_dim.calendar_date = TO_DATE('" + dt.strftime('%Y-%m-%d') + "','yyyy-mm-dd')\
                          UNION\
                            SELECT DISTINCT case_compensation_fact.case_id\
                            FROM case_compensation_fact\
                            LEFT OUTER JOIN case_flight_fact\
                                 ON case_compensation_fact.case_id = case_flight_fact.case_id\
                            LEFT OUTER JOIN calendar_dim\
                                 ON case_flight_fact.flight_date = calendar_dim.calendar_key\
                            WHERE reason_desc = 'Denied Boarding' AND\
                                  case_flight_fact.dep_city = '" + orgn + "' AND\
                                  case_flight_fact.arr_city = '" + dstn + "' AND\
                                  case_flight_fact.flight_nbr = '" + fltnum[1:] + "' AND\
                                  calendar_dim.calendar_date = TO_DATE('" + dt.strftime('%Y-%m-%d') + "','yyyy-mm-dd')") 
    case_list = []
    for case in siebel_curs.fetchall():
      if case not in case_list:
         case_list.append(case[0])
    return case_list

  @staticmethod
  def get_dep_dg_case_list(orgn, dstn, fltnum, date):
    siebel_curs = dbConnector.get_siebel_curs()
    siebel_curs.execute(" SELECT DISTINCT category_dim_h.case_id\
                          FROM category_dim_h\
                          LEFT OUTER JOIN case_flight_fact\
                               ON category_dim_h.case_id = case_flight_fact.case_id\
                          LEFT OUTER JOIN calendar_dim\
                               ON case_flight_fact.flight_date = calendar_dim.calendar_key\
                          WHERE sub_cat_nm = 'Downgrading' AND\
                                case_flight_fact.dep_city = '" + orgn + "' AND\
                                case_flight_fact.arr_city = '" + dstn + "' AND\
                                case_flight_fact.flight_nbr = '" + fltnum[1:] + "' AND\
                                calendar_dim.calendar_date = DATE('" + date + "')\
                          UNION\
                            SELECT DISTINCT case_compensation_fact.case_id\
                            FROM case_compensation_fact\
                            LEFT OUTER JOIN case_flight_fact\
                              ON case_compensation_fact.case_id = case_flight_fact.case_id\
                            LEFT OUTER JOIN calendar_dim\
                              ON case_flight_fact.flight_date = calendar_dim.calendar_key\
                            WHERE reason_desc = 'Downgrading' AND\
                                  case_flight_fact.dep_city = '" + orgn + "' AND\
                                  case_flight_fact.arr_city = '" + dstn + "' AND\
                                  case_flight_fact.flight_nbr = '" + fltnum[1:] + "' AND\
                                  calendar_dim.calendar_date = DATE('" + date + "')")
    case_list = []
    for case in siebel_curs.fetchall():
      if case not in case_list:
        case_list.append(case[0])

    return case_list

  @staticmethod
  def get_dep_db_cases(orgn,dstn,fltnum,dt):
    """
    """
    res = []
    cases = CRMCase.get_dep_db_case_list(orgn,dstn,fltnum,dt)
    for case_id in cases:
      case = CRMCase(case_id)
      num_pax = case.get_num_pax()
      cmpns = case.get_cmpn_amt()
      tot_amnt = 0
      for cmpn in cmpns:
        status = cmpn[0]
        amount = cmpn[1]
        reason = cmpn[2]
        if status == 'Issued':  
          tot_amnt += amount
      res.append([case_id,num_pax,tot_amnt])
    return res

  @staticmethod
  def get_dep_db_total_compensation(orgn,dstn,fltnum,dt):
    """Returns total number of denied boarding compensation
       paid on departure"""
    cases = CRMCase.get_dep_db_case_list(orgn,dstn,fltnum,dt)
    total_compensation = 0
    for case_id in cases:
      case = CRMCase(case_id)
      cmpns = case.get_cmpn_amt()
      for cmpn in cmpns:
        status = cmpn[0]
        amount = cmpn[1]
        reason = cmpn[2]
        if status == 'Issued':
          total_compensation += amount
    return total_compensation

  @staticmethod
  def get_dep_db_total_num_pax(orgn,dstn,fltnum,dt):
    """Returns total number of denied boarded passengers"""
    cases = CRMCase.get_dep_db_case_list(orgn,dstn,fltnum,dt)
    total_num_pax = 0
    for case_id in cases:
      case = CRMCase(case_id)
      num_pax = case.get_num_pax()
      total_num_pax += num_pax
    return total_num_pax

  @staticmethod
  def get_flt_db_case_list(orgn, dstn, fltnum):
    # FIXME: why don't use SQL INTERSECT instead of 2 SQL SELECTs?
    siebel_curs = dbConnector.get_siebel_curs()
    # first take all cases from with subcategory overbooked
    siebel_curs.execute("SELECT DISTINCT category_dim_h.case_id\
                         FROM category_dim_h\
                         LEFT OUTER JOIN case_flight_fact\
                              ON category_dim_h.case_id = case_flight_fact.case_id\
                         WHERE sub_cat_nm='Overbooking' AND\
                               case_flight_fact.flight_nbr='" + fltnum[1:] + "' AND\
                               case_flight_fact.dep_city='" + orgn + "' AND\
                               case_flight_fact.arr_city='" + dstn + "'")
    case_list = [list(case) for case in siebel_curs.fetchall()]
    # second take all cases from compensation with reason denied boarding
    siebel_curs.execute("SELECT DISTINCT case_compensation_fact.case_id\
                         FROM case_compensation_fact\
                         LEFT OUTER JOIN case_flight_fact\
                              ON case_compensation_fact.case_id = case_flight_fact.case_id\
                         WHERE reason_desc='Denied Boarding' AND\
                               case_flight_fact.flight_nbr='" + fltnum[1:] + "' AND\
                               case_flight_fact.dep_city='" + orgn + "' AND\
                               case_flight_fact.arr_city='" + dstn + "'")
    for case in siebel_curs.fetchall():
      if case not in case_list:
        # add element, because it isn't present in old list
        case_list.append(list(case))

    return case_list 

  @staticmethod
  def get_flt_dg_case_list(orgn, dstn, fltnum):
    siebel_curs = dbConnector.get_siebel_curs()
    # first take all cases with subcategory 'Downgrading'
    siebel_curs.execute("SELECT DISTINCT category_dim_h.case_id\
                         FROM category_dim_h\
                         LEFT OUTER JOIN case_flight_fact\
                              ON category_dim_h.case_id = case_flight_fact.case_id\
                         WHERE sub_cat_nm = 'Downgrading' AND\
                               case_flight_fact.flight_nbr='" + fltnum[1:] + "' AND\
                               case_flight_fact.dep_city='" + orgn + "' AND\
                               case_flight_fact.arr_city='" + dstn + "'")
    case_list = [list(case) for case in siebel_curs.fetchall()]
    # second take cases with reason 'Downgrading'
    siebel_curs.execute("SELECT DISTINCT case_compensation_fact.case_id\
                         FROM case_compensation_fact\
                         LEFT OUTER JOIN case_flight_fact\
                              ON case_compensation_fact.case_id = case_flight_fact.case_id\
                         WHERE reason_desc='Downgrading' AND\
                               case_flight_fact.flight_nbr='" + fltnum[1:] + "' AND\
                               case_flight_fact.dep_city='" + orgn + "' AND\
                               case_flight_fact.arr_city='" + dstn + "'")

    for case in siebel_curs.fetchall():
      if case not in case_list:
        case_list.append(case)                        

    return case_list      
 
  @staticmethod
  def get_rt_db_case_list(orgn, dstn):
    siebel_curs = dbConnector.get_siebel_curs()
    siebel_curs.execute(" SELECT DISTINCT category_dim_h.case_id\
                          FROM category_dim_h\
                          LEFT OUTER JOIN case_flight_fact\
                               ON category_dim_h.case_id = case_flight_fact.case_id\
                          WHERE sub_cat_nm='Overbooking' AND\
                                case_flight_fact.dep_city='" + orgn + "' AND\
                                case_flight_fact.arr_city='" + dstn + "' \
                          UNION \
                            SELECT DISTINCT case_compensation_fact.case_id\
                            FROM case_compensation_fact\
                            LEFT OUTER JOIN case_flight_fact\
                                 ON case_compensation_fact.case_id = case_flight_fact.case_id\
                            WHERE reason_desc='Denied Boarding' AND\
                                  case_flight_fact.dep_city='" + orgn + "' AND\
                                  case_flight_fact.arr_city='" + dstn + "' ")
    case_list = []
    for case in siebel_curs.fetchall():
      if case not in case_list:
        # Do this check due to some problem 
        # with DB2 SQL UNION DISTINCT.
        # It merely doesn't work.
        case_list.append(case[0])
    return case_list 

  @staticmethod
  def get_rt_dg_case_list(orgn, dstn):
    siebel_curs = dbConnector.get_siebel_curs()
    siebel_curs.execute(" SELECT DISTINCT category_dim_h.case_id\
                          FROM category_dim_h\
                          LEFT OUTER JOIN case_flight_fact\
                               ON category_dim_h.case_id = case_flight_fact.case_id\
                          WHERE sub_cat_nm = 'Downgrading' AND\
                                case_flight_fact.dep_city='" + orgn + "' AND\
                                case_flight_fact.arr_city='" + dstn + "' \
                          UNION \
                            SELECT DISTINCT case_compensation_fact.case_id\
                            FROM case_compensation_fact\
                            LEFT OUTER JOIN case_flight_fact\
                                 ON case_compensation_fact.case_id = case_flight_fact.case_id\
                            WHERE reason_desc='Downgrading' AND\
                                  case_flight_fact.dep_city='" + orgn + "' AND\
                                  case_flight_fact.arr_city='" + dstn + "'")
    case_list = []
    for case in siebel_curs.fetchall():
      if case not in case_list:
        # Do this check due to some problem
        # with DB2 SQL UNION DISTINCT.
        # It merely doesn't work
        case_list.append(case[0])
    return case_list

  @staticmethod
  def get_case_list(dfrom,dto):
    siebel_curs = dbConnector.get_siebel_curs()
    # case_flight_fact.dep_city
    # case_flight_fact.arr_city
    # case_flight_fact.flight_nbr
    # calendar_dim.calendar_date

    q = "SELECT DISTINCT case_compensation_fact.case_id\
         FROM case_compensation_fact\
         LEFT OUTER JOIN case_flight_fact\
           ON case_compensation_fact.case_id = case_flight_fact.case_id\
         LEFT OUTER JOIN calendar_dim\
           ON case_flight_fact.flight_date = calendar_dim.calendar_key\
         WHERE calendar_dim.calendar_date >= TO_DATE('"+dfrom.strftime('%Y-%m-%d')+"','YYYY-MM-DD') AND\
               calendar_dim.calendar_date <= TO_DATE('"+dto.strftime('%Y-%m-%d')+"','YYYY-MM-DD')"
    siebel_curs.execute(q)
    ans = []
    for case in siebel_curs.fetchall():
      ans.append(case[0])
    return ans

  @staticmethod
  def get_db_cases(dfrom,dto):
    db_cases = []
    cases = CRMCase.get_case_list(dfrom,dto)
    for case_id in cases:
      e = {}
      case = CRMCase(case_id)
      e['case_id'] = case_id
      e['rec_cre_dt'] = case.rec_cre_dt()
      e['categories'] = '-'.join(case.get_cat_list())  
      e['num_pax'] = case.get_num_pax()
      e['cmpn'] = case.get_cmpn_amt()
      e['flight'] = case.get_flight()
      if 'OVERBOOKING' in e['categories']:
        db_cases.append(e)
      else:
        for a in e['cmpn']:
          if a[2] is None:
            continue
          if 'Denied Boarding' in a[2]:
            db_cases.append(e)
            break

    # Calculate total number of paxes
    tot_num = 0
    tot_amt = 0
    for case in db_cases:
      tot_num += int(case['num_pax'])
      for e in case['cmpn']:
        if 'Issued' in e[0] or 'Completed' in e[0]:
          tot_amt += float(e[1])
    return tot_num,tot_amt,db_cases

if __name__ == '__main__':
  orgn = sys.argv[1]
  dstn = sys.argv[2]

  dfrom_s = sys.argv[3]
  dto_s = sys.argv[4]
  dfroms = dfrom_s.split('-')
  dtos = dto_s.split('-')

  dfrom = date(int(dfroms[0]),int(dfroms[1]),int(dfroms[2]))
  dto = date(int(dtos[0]),int(dtos[1]),int(dtos[2]))

  l = Leg(orgn,dstn)

  fltnums = l.get_fltnums()
  for fltnum in fltnums:
    dt = dfrom
    while dt <= dto:
      s = CRMCase.get_dep_db_cases(orgn,dstn,fltnum,dt) 
      if len(s) != 0:
        print dt.strftime('%Y-%m-%d'),orgn,dstn,fltnum,s
      dt += timedelta(days=1)




