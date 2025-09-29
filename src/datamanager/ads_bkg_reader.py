import os
import sys
import ConfigParser

from datetime import date,timedelta

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector


class AdsBkgReader:


    def __init__(self):
        self.ads_curs = dbConnector.get_ads_curs()
        self.neo4j_conn = dbConnector.get_neo4j_conn()


    def _get_flights(self,flt_ids):
        ac = self.ads_curs

        where_clause = ' flt_id='+str(flt_ids[0])+' '.join(['OR flt_id='+str(flt_id) for flt_id in flt_ids])
        q = "SELECT flt_id,flt_carrer_cd,flight_nbr,flt_date FROM ads_flight\
             WHERE " + where_clause
        ac.execute(q)

        fltnums = {}
        row = ac.fetchone()
        while row is not None:
            flt_id = row[0]
            ccode = row[1]
            fltnum = row[2].zfill(5)
            dptdt = row[3]
            fltnums[flt_id] = {'ccode': ccode, 'fltnum': fltnum, 'dptdt': dptdt}
            row = ac.fetchone()   
        return fltnums 


    def _get_tickets(self,tkt_ids):
        ac = self.ads_curs

        where_clause = ' tkt_id IN ('+','.join([str(tkt_id) for tkt_id in tkt_ids])+')'
        q = "SELECT tkt_id,ads_cre_tmstmp,ads_del_ind,ads_last_upd_tmstmp,\
                    currency,officeid,primary_nbr,tkt_issue_dt,totalamount\
             FROM ads_tkt\
             WHERE " + where_clause
        ac.execute(q)

        tkts = {}
        row = ac.fetchone()
        while row is not None:
            tkt_id = row[0]
            cre_dt = row[1]
            del_ind = row[2]
            last_upd = row[3]
            curr = row[4]
            officeid = row[5]
            primary_nbr = row[6]
            issue_dt = row[7]
            totamt = row[8]

            tkts[tkt_id] = {'cre_dt': cre_dt,'del_ind':del_ind,'last_upd':last_upd,
                            'curr': curr,'officeid':officeid,'primary_nbr':primary_nbr,
                            'issue_dt':issue_dt,'totamt':totamt}
            row = ac.fetchone()
        return tkts


    def update_fltnums(self,ress):
        opr_flt_ids = [res['opr_flt_id'] for res in ress]
        mkt_flt_ids = [res['mkt_flt_id'] for res in ress]
        opr_flt_ids = list(set(opr_flt_ids))
        mkt_flt_ids = list(set(mkt_flt_ids))

        flt_ids = list(set(opr_flt_ids + mkt_flt_ids))
        fltnums = self._get_flights(flt_ids)

        i = 0
        for i in range(len(ress)):
            ress[i]['opr_fltnum'] = fltnums[res['opr_flt_id']]
            ress[i]['mkt_fltnum'] = fltnums[res['mkt_flt_id']]
            i += 1
        return ress


    def update_tkts(self,ress):
        tkt_ids = [res['bkg_tkt_id'] for res in ress if res['bkg_tkt_id'] is not None]
        tkt_ids = list(set(tkt_ids))
        tkts = self._get_tickets(tkt_ids)

        i = 0
        for i in range(len(tkts)):
            bkg_tkt_id = res['bkg_tkt_id']
            if bkg_tkt_id is not None:
                ress[i]['tkt'] = tkts[bkg_tkt_id]
            else:
                ress[i]['tkt'] = None
            i += 1
        return ress


    def daily_bookings(self,dt):
        ac = self.ads_curs

        dt_s = dt.strftime('%Y-%m-%d')
        dt_plus_s = (dt+timedelta(days=1)).strftime('%Y-%m-%d')
        q = "SELECT bkg_cre_dt_tm,\
                    bkg_confirm_dt_tm,\
                    bkg_cancel_dt_tm,\
                    class,\
                    bkg_tkt_id,\
                    mkt_flt_id,\
                    opr_flt_id,\
                    ads_last_upd_tmstmp\
             FROM ADS_BKG\
             WHERE ads_last_upd_tmstmp >= TO_DATE('"+dt_s+"','yyyy-mm-dd') AND\
                   ads_last_upd_tmstmp < TO_DATE('"+dt_plus_s+"','yyyy-mm-dd')"
        ac.execute(q)  

        ress = []
        row = ac.fetchone()
        i = 0
        while row is not None:
            res = {}
            res['bkg_cre_dt_tm'] = row[0]
            res['bkg_confirm_dt_tm'] = row[1]
            res['bkg_cancel_dt_tm'] = row[2]
            res['class'] = row[3]
            res['bkg_tkt_id'] = row[4]
            res['mkt_flt_id'] = row[5]
            res['opr_flt_id'] = row[6]
            res['last_upd'] = row[7]
            ress.append(res)
            i += 1
            row = ac.fetchone()
        ress = self.update_fltnums(ress)
        ress = self.update_tkts(ress)
        return ress

if __name__ == '__main__':
  dt = date(2013,7,8)
  nl = AdsBkgReader()
  ress = nl.daily_bookings(dt)
  print ress


  
