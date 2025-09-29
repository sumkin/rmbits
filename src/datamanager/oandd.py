import sys
import time
from datetime import date, datetime, timedelta

from db_connector import dbConnector
from departure import departure
from booking import Booking
from cls import *
from airport import *

TC_P2P = 0
TC_LH  = 1
TC_IE  = 2

class OandD:
    
    def __init__(self,airports,dfrom = None,dto = None):
        # airports is the list of airport codes for one-way
        # for example: [SVX,HEL,JFK]
        assert len(airports) == 3 or len(airports) == 2
        self.airports = airports
        self.num_hops = len(self.airports)
        self.dfrom    = dfrom
        self.dto      = dto

    def get_orgn(self):
        return self.airports[0]

    def get_dstn(self):
        if len(self.airports) == 2:
            return self.airports[1]
        else:
            return self.airports[2]
        
    def get_type(self):
        # Point to point, long-haul or intra-europe
        if len(self.airports) == 2:
            orgn = self.airports[0]
            dstn = self.airports[1]
        else:
            orgn = self.airports[0]
            hop  = self.airports[1]
            dstn = self.airports[2]
        orgn_ap = airport(orgn)
        dstn_ap = airport(dstn)
        orgn_region = orgn_ap.get_region()
        dstn_region = dstn_ap.get_region()
        if len(self.airports) == 2:
            if (orgn_region == 'EUROP' or orgn_region == 'EURAS') and\
               (dstn_region == 'EUROP' or dstn_region == 'EURAS'):
                return TC_P2P
            else:
                return TC_LH
        else:
            if (orgn_region == 'EUROP' or orgn_region == 'EURAS') and\
               (dstn_region == 'EUROP' or dstn_region == 'EURAS'):
                return TC_IE
            else:
                return TC_LH

    def to_str(self):
        return '-'.join(self.airports)

    def get_ap_cls_stats_d(self,cls):
        # Only 2 or 3 hops so far
        assert self.num_hops == 2 or self.num_hops == 3
        curs = dbConnector.get_or_curs()
        if self.num_hops == 2:
            q = "SELECT fst_tkt,COUNT(flightdate) AS cnt\
                 FROM paras_used_" + cls.lower() + "\
                 WHERE (depairport = '" + self.airports[0] + "' AND\
                        arrairport = '" + self.airports[1] + "') OR\
                       (depairport = '" + self.airports[1] + "' AND\
                        arrairport = '" + self.airports[0] + "')\
                 GROUP BY fst_tkt having cnt = 2"
        else:
            q = "SELECT fst_tkt,COUNT(flightdate) AS cnt\
                 FROM paras_used_" + cls.lower() + "\
                 WHERE (depairport = '" + self.airports[0] + "' AND\
                        arrairport = '" + self.airports[1] + "') OR\
                       (depairport = '" + self.airports[1] + "' AND\
                        arrairport = '" + self.airports[0] + "') OR\
                       (depairport = '" + self.airports[1] + "' AND\
                        arrairport = '" + self.airports[2] + "') OR\
                       (depairport = '" + self.airports[2] + "' AND\
                        arrairport = '" + self.airports[1] + "')\
                 GROUP BY fst_tkt HAVING cnt = 4"
        curs.execute(q)
        
        res = {}
        rows = curs.fetchall()
        for row in rows:
            fst_tkt = row[0]
            bkg = Booking(fst_tkt,cls.lower())
            legs = bkg.get_legs()
            if self.num_hops == 2:
                if len(legs) == 2:
                    if legs[0]['depairport'] == self.airports[0] and\
                       legs[0]['arrairport'] == self.airports[1] and\
                       legs[1]['depairport'] == self.airports[1] and\
                       legs[1]['arrairport'] == self.airports[0]:
                        res[bkg.fst_tkt] = (legs[0]['flightdate'] - legs[0]['bkg_cre_dt_tm'].date()).days
            else:
                if len(legs) == 4:
                    if legs[0]['depairport'] == self.airports[0] and\
                       legs[0]['arrairport'] == self.airports[1] and\
                       legs[1]['depairport'] == self.airports[1] and\
                       legs[1]['arrairport'] == self.airports[2] and\
                       legs[2]['depairport'] == self.airports[2] and\
                       legs[2]['arrairport'] == self.airports[1] and\
                       legs[3]['depairport'] == self.airports[1] and\
                       legs[3]['arrairport'] == self.airports[0]:
                        res[bkg.fst_tkt] = (legs[0]['flightdate'] - legs[0]['bkg_cre_dt_tm'].date()).days
            row = curs.fetchone()
        return res

    def __old__get_ap_cls_stats_d(self,cls):
        # FIXME: doulbe check queires.
        #print 'get_ap_cls started...'
        curs = dbConnector.get_or_curs()
        if self.num_hops == 2:
            q = "SELECT fst_tkt,flightdate,bkg_cre_dt_tm FROM paras_used_" + cls.lower() + "\
                 WHERE depairport = '" + self.airports[0] + "' AND\
                       arrairport = '" + self.airports[1] + "' AND\
                       fst_tkt IN\
                       (SELECT fst_tkt FROM paras_used_" + cls.lower() + "\
                        WHERE depairport = '" + self.airports[1] + "' AND\
                              arrairport = '" + self.airports[0] + "') AND\
                       fst_tkt NOT IN\
                       (SELECT fst_tkt FROM paras_used_" + cls.lower() + "\
                        WHERE depairport = '" + self.airports[1] + "' AND\
                              arrairport <> '" + self.airports[0] + "')"

        else:
            q = "SELECT fst_tkt,flightdate,bkg_cre_dt_tm FROM paras_used_" + cls.lower() + "\
                 WHERE depairport = '" + self.airports[0] + "' AND\
                       arrairport = '" + self.airports[1] + "' AND\
                       bookingclass = '" + cls + "' AND\
                       fst_tkt IN\
                       (SELECT fst_tkt FROM paras_used_" + cls.lower() + "\
                        WHERE depairport = '" + self.airports[1] + "' AND\
                              arrairport = '" + self.airports[2] + "')\
                 ORDER BY fst_tkt,flightdate,bkg_cre_dt_tm"
        curs.execute(q)
        #print 'get_ap_cls query executed...'
        row = curs.fetchone()
        to_d = {}
        while row is not None:
            fst_tkt = row[0]
            flightdate = row[1]
            bkg_cre_dt_tm = row[2]
            if bkg_cre_dt_tm != '' and bkg_cre_dt_tm is not None:
                if (flightdate - bkg_cre_dt_tm.date()).days >= 0:
                    to_d[fst_tkt] = (flightdate - bkg_cre_dt_tm.date()).days
            row = curs.fetchone()
        return to_d

    def get_ap_cls_stats(self,cls):
        ap_cls_d = self.get_ap_cls_stats_d(cls)
        ret = []
        for k in ap_cls_d.keys():
            if ap_cls_d[k] >= 0:
                ret.append(ap_cls_d[k])
        return ret

    def get_stay_length_stats_d(self,cls):
        # Only two of three hops so far
        assert self.num_hops == 3 or self.num_hops == 2
        curs = dbConnector.get_or_curs()
        #print 'n hops:', self.num_hops
        # FIXME: these queries return more than needed!
        # result is filtered later going throught all bookings.
        if self.num_hops == 2:
            q = "SELECT fst_tkt,COUNT(flightdate) AS cnt\
                 FROM paras_used_" + cls.lower() + "\
                 WHERE (depairport = '" + self.airports[0] + "' AND\
                        arrairport = '" + self.airports[1] + "') OR\
                       (depairport = '" + self.airports[1] + "' AND\
                        arrairport = '" + self.airports[0] + "')\
                 GROUP BY fst_tkt having cnt = 2"
        else:
            q = "SELECT fst_tkt,COUNT(flightdate) AS cnt\
                 FROM paras_used_" + cls.lower() + "\
                 WHERE (depairport = '" + self.airports[0] + "' AND\
                        arrairport = '" + self.airports[1] + "') OR\
                       (depairport = '" + self.airports[1] + "' AND\
                        arrairport = '" + self.airports[0] + "') OR\
                       (depairport = '" + self.airports[1] + "' AND\
                        arrairport = '" + self.airports[2] + "') OR\
                       (depairport = '" + self.airports[2] + "' AND\
                        arrairport = '" + self.airports[1] + "')\
                 GROUP BY fst_tkt HAVING cnt = 4"
        curs.execute(q)
        
        res = {}
        rows = curs.fetchall()
        for row in rows:
            fst_tkt = row[0]
            bkg = Booking(fst_tkt,cls.lower())
            legs = bkg.get_legs()
            #print fst_tkt,len(legs)
            if self.num_hops == 2:
                if len(legs) == 2:
                    if legs[0]['depairport'] == self.airports[0] and\
                       legs[0]['arrairport'] == self.airports[1] and\
                       legs[1]['depairport'] == self.airports[1] and\
                       legs[1]['arrairport'] == self.airports[0]:
                        res[bkg.fst_tkt] = (legs[1]['flightdate'] - legs[0]['flightdate']).days
            else:
                if len(legs) == 4:
                    if legs[0]['depairport'] == self.airports[0] and\
                       legs[0]['arrairport'] == self.airports[1] and\
                       legs[1]['depairport'] == self.airports[1] and\
                       legs[1]['arrairport'] == self.airports[2] and\
                       legs[2]['depairport'] == self.airports[2] and\
                       legs[2]['arrairport'] == self.airports[1] and\
                       legs[3]['depairport'] == self.airports[1] and\
                       legs[3]['arrairport'] == self.airports[0]:
                        res[bkg.fst_tkt] = (legs[2]['flightdate'] - legs[1]['flightdate']).days
            row = curs.fetchone()
        return res

    def __old__get_stay_length_stats_d(self,cls):

        # FIXME: we do not consider more than 3 hops
        # in OD

        # FIXME: functions for some reasons return
        # negative values. Check that queries are
        # correct.
        assert self.num_hops == 3 or self.num_hops == 2

        #print 'get_stay_length started...'
        curs = dbConnector.get_or_curs()
        if self.num_hops == 2:
            q = "SELECT fst_tkt,flightdate FROM paras_used_" + cls.lower() + "\
                 WHERE depairport = '" + self.airports[0] + "' AND\
                       arrairport = '" + self.airports[1] + "' AND\
                       fst_tkt NOT IN\
                       (SELECT fst_tkt FROM paras_used_" + cls.lower() + "\
                        WHERE depairport = '" + self.airports[1] + "' AND\
                              arrairport <> '" + self.airports[0] + "')\
                 ORDER BY fst_tkt,flightdate"
        else:
            q = "SELECT fst_tkt,flightdate FROM paras_used_" + cls.lower() + "\
                 WHERE\
                     (depairport = '" + self.airports[0] + "' AND\
                      arrairport = '" + self.airports[1] + "') OR\
                     (depairport = '" + self.airports[1] + "' AND\
                      arrairport = '" + self.airports[2] + "')\
                 ORDER BY fst_tkt,flightdate"
        curs.execute(q)
        #print 'get_stay_length executed...'
        row = curs.fetchone()
        prev_fst_tkt = None
        prev_flightdate = None
        to_d = {}
        if self.num_hops == 2:
            while row is not None:
                fst_tkt = row[0]
                flightdate = row[1]
                to_d[fst_tkt] = flightdate
                row = curs.fetchone()
        else:
            while row is not None:
                fst_tkt = row[0]
                flightdate = row[1]
                if fst_tkt == prev_fst_tkt:
                    to_d[fst_tkt] = flightdate
                prev_fst_tkt = fst_tkt
                prev_flightdate = flightdate
                row = curs.fetchone()
        to_keys = to_d.keys()
                
        # FIXME: carrier and datetime should be
        # presented in query
        # FIXME: no class in return, because
        # it could be different. It needs clarifications.
        if self.num_hops == 2:
            q = "SELECT fst_tkt,flightdate FROM paras_used_" + cls.lower() + "\
                 WHERE\
                     depairport = '" + self.airports[1] + "' AND\
                     arrairport = '" + self.airports[0] + "' AND\
                     fst_tkt NOT IN\
                     (SELECT fst_tkt FROM paras_used_" + cls.lower() + "\
                      WHERE depairport = '" + self.airports[0] + "' AND\
                            arrairport <> '" + self.airports[1] + "')\
                 ORDER BY fst_tkt,flightdate"
        else:
            q = "SELECT fst_tkt,flightdate FROM paras_used_" + cls.lower() + "\
                 WHERE\
                     (depairport = '" + self.airports[2] + "' AND\
                      arrairport = '" + self.airports[1] + "') OR\
                     (depairport = '" + self.airports[1] + "' AND\
                      arrairport = '" + self.airports[0] + "')\
                 ORDER BY fst_tkt,flightdate"
        curs.execute(q)
        row = curs.fetchone()
        prev_fst_tkt = None
        prev_flightdate = None
        from_d = {}
        if self.num_hops == 2:
            while row is not None:
                fst_tkt = row[0]
                flightdate = row[1]
                from_d[fst_tkt] = flightdate
                row = curs.fetchone()
        else:
            while row is not None:
                fst_tkt = row[0]
                flightdate = row[1]
                if fst_tkt == prev_fst_tkt:
                    from_d[fst_tkt] = flightdate
                prev_fst_tkt = fst_tkt
                prev_flightdate = flightdate
                row = curs.fetchone()
        from_keys = from_d.keys()

        to_from_keys = filter(lambda x: x in from_keys,to_keys)
        ret = {}
        for k in to_from_keys:
            if (from_d[k] - to_d[k]).days >= 0:
                ret[k] = (from_d[k] - to_d[k]).days
        return ret

    def get_stay_length_stats(self,cls):
        stay_length_d = self.get_stay_length_stats_d(cls)
        ret = []
        for k in stay_length_d.keys():
            ret.append(stay_length_d[k])                  
        return ret

    def get_stay_length_and_ap_stats(self,cls):
        stay_length_d = self.get_stay_length_stats_d(cls)
        ap_d = self.get_ap_cls_stats_d(cls)
        keys = [e for e in ap_d.keys() if e in stay_length_d.keys()]
        ret = []
        for key in keys:
            ret.append([stay_length_d[key],ap_d[key]])

        # FIXME: stay length should not be negative
        # and ap should be in [0,365].
        # Those values are indication of errors in DB(?)
        # Merely filter bad observations.
        # Lack of time...
        res = [[e[0],e[1]] for e in ret if e[0] >= 0 and e[1] >= 0 and e[1] <= 365]
        return res
    
    def get_avg_tot_fare_cls(self,cls):
        curs = dbConnector.get_or_curs()
        if len(self.airports) == 3:
            path = self.airports[0] + '-' + self.airports[1] +\
                   ' ' + self.airports[1] + '-' + self.airports[2]
        elif len(self.airports) == 2:
            path = self.airports[0] + '-' + self.airports[1]
            
        q = "SELECT AVG(total_fare/pax_cnt) FROM ra_data\
             WHERE path = '" + path + "' AND\
                   cls = '" + cls + "'"
        curs.execute(q)
        row = curs.fetchone()
        return row[0]

    def get_avg_tot_fare_cls_robust(self,cls):
        fare = self.get_avg_tot_fare_cls(cls)
        if fare is None:
            upper_fare = fare
            upper_cls = cls
            while upper_fare is None:
                upper_cls = get_upper_cls(upper_cls)
                #print 'upper_cls:',upper_cls
                if upper_cls is None:
                    break
                upper_fare = self.get_avg_tot_fare_cls(upper_cls)
            #print 'upper_cls:',upper_cls
            lower_fare = fare
            lower_cls = cls
            while lower_fare is None and lower_cls is not None:
                lower_cls = get_lower_cls(lower_cls)
                if lower_cls is None:
                    break
                lower_fare = self.get_avg_tot_fare_cls(lower_cls)
            if lower_fare is None:
                fare = upper_fare
            elif upper_fare is None:
                fare = lower_fare
            else:
                fare = float(lower_fare + upper_fare)/2
        return fare 
    



 
