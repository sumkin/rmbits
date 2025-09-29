import csv
import gzip
from datetime import datetime, timedelta
from lxml import etree
import subprocess

from defs import *
from airport_s3 import AirportS3
from s3utils import *


class BFFReader2:
    """
    Class implements reader for BFF XML file.
    """
    
    def __init__(self,fname):
        self.fname = fname

    @staticmethod
    def get_dt(s):
        res = s[:10]
        return res

    @staticmethod
    def get_geo_od_ts_key(row, bof = False):
        """
        Returns key for joining to RS tables.
        """
        if bof:
            base_od_orgn = row[0]
            base_od_dstn = row[1]
            base_od_via = row[2].split('-')
            base_od_via = [e for e in base_od_via if e != '']
            base_opr_cc = row[7].split('-')
            base_opr_cc = [e for e in base_opr_cc if e != '']
            base_opr_fltnum = row[8].split('-')
            base_opr_fltnum = [e for e in base_opr_fltnum if e != '']
            base_mkt_cc = row[9].split('-')
            base_mkt_cc = [e for e in base_mkt_cc if e != '']
            base_mkt_fltnum = row[10].split('-')
            base_mkt_fltnum = [e for e in base_mkt_fltnum if e != '']
            base_od_dep_date = row[11].split('-')
            base_od_dep_date = [e for e in base_od_dep_date if e != '']
            base_seg_dep_dates = row[13].split('-')
            base_seg_dep_dates = [e for e in base_seg_dep_dates if e != '']
            base_seg_arr_dates = row[14].split('-')
            base_seg_arr_dates = [e for e in base_seg_arr_dates if e != '']
            geo_orgn = row[15]
            geo_dstn = row[16]
            prev_via = row[17].split('-')
            prev_via = [e for e in prev_via if e != '']
            prev_opr_cc = row[18].split('-')
            prev_opr_cc = [e for e in prev_opr_cc if e != '']
            prev_opr_fltnum = row[19].split('-')
            prev_opr_fltnum = [e for e in prev_opr_fltnum if e != '']
            prev_mkt_cc = row[20].split('-')
            prev_mkt_cc = [e for e in prev_mkt_cc if e != '']
            prev_mkt_fltnum = row[21].split('-')
            prev_mkt_fltnum = [e for e in prev_mkt_fltnum if e != '']
            prev_seg_dep_dates = row[22].split('-')
            prev_seg_dep_dates = [e for e in prev_seg_dep_dates if e != '']
            prev_seg_arr_dates = row[23].split('-')
            prev_seg_arr_dates = [e for e in prev_seg_arr_dates if e != '']
            next_via = row[24].split('-')
            next_via = [e for e in next_via if e != '']
            next_opr_cc = row[25].split('-')
            next_opr_cc = [e for e in next_opr_cc if e != '']
            next_opr_fltnum = row[26].split('-')
            next_opr_fltnum = [e for e in next_opr_fltnum if e != '']
            next_mkt_cc = row[27].split('-')
            next_mkt_cc = [e for e in next_mkt_cc if e != '']
            next_mkt_fltnum = row[28].split('-')
            next_mkt_fltnum = [e for e in next_mkt_fltnum if e != '']
            next_seg_dep_dates = row[29].split('-')
            next_seg_dep_dates = [e for e in next_seg_dep_dates if e != '']
            next_seg_arr_dates = row[30].split('-')
            next_seg_arr_dates = [e for e in next_seg_arr_dates if e != '']
        else:
            base_od_orgn = row[0]
            base_od_dstn = row[1]
            base_od_via = row[2].split('-')
            base_od_via = [e for e in base_od_via if e != '']
            base_opr_cc = row[7].split('-')
            base_opr_cc = [e for e in base_opr_cc if e != '']
            base_opr_fltnum = row[8].split('-')
            base_opr_fltnum = [e for e in base_opr_fltnum if e != '']
            base_mkt_cc = row[9].split('-')
            base_mkt_cc = [e for e in base_mkt_cc if e != '']
            base_mkt_fltnum = row[10].split('-')
            base_mkt_fltnum = [e for e in base_mkt_fltnum if e != '']
            base_od_dep_date = row[11].split('-')
            base_od_dep_date = [e for e in base_od_dep_date if e != '']
            base_seg_dep_dates = row[12].split('-')
            base_seg_dep_dates = [e for e in base_seg_dep_dates if e != '']
            base_seg_arr_dates = row[13].split('-')
            base_seg_arr_dates = [e for e in base_seg_arr_dates if e != '']
            geo_orgn = row[14]
            geo_dstn = row[15]
            prev_via = row[16].split('-')
            prev_via = [e for e in prev_via if e != '']
            prev_opr_cc = row[17].split('-')
            prev_opr_cc = [e for e in prev_opr_cc if e != '']
            prev_opr_fltnum = row[18].split('-')
            prev_opr_fltnum = [e for e in prev_opr_fltnum if e != '']
            prev_mkt_cc = row[19].split('-')
            prev_mkt_cc = [e for e in prev_mkt_cc if e != '']
            prev_mkt_fltnum = row[20].split('-')
            prev_mkt_fltnum = [e for e in prev_mkt_fltnum if e != '']
            prev_seg_dep_dates = row[21].split('-')
            prev_seg_dep_dates = [e for e in prev_seg_dep_dates if e != '']
            prev_seg_arr_dates = row[22].split('-')
            prev_seg_arr_dates = [e for e in prev_seg_arr_dates if e != '']
            next_via = row[23].split('-')
            next_via = [e for e in next_via if e != '']
            next_opr_cc = row[24].split('-')
            next_opr_cc = [e for e in next_opr_cc if e != '']
            next_opr_fltnum = row[25].split('-')
            next_opr_fltnum = [e for e in next_opr_fltnum if e != '']
            next_mkt_cc = row[26].split('-')
            next_mkt_cc = [e for e in next_mkt_cc if e != '']
            next_mkt_fltnum = row[27].split('-')
            next_mkt_fltnum = [e for e in next_mkt_fltnum if e != '']
            next_seg_dep_dates = row[28].split('-')
            next_seg_dep_dates = [e for e in next_seg_dep_dates if e != '']
            next_seg_arr_dates = row[29].split('-')
            next_seg_arr_dates = [e for e in next_seg_arr_dates if e != '']
       
        # Produce key.
        res = ''

        # Previous segments.
        if len(prev_opr_cc) > 0:
            assert len(prev_via) + 1 == len(prev_opr_cc)
            assert len(prev_opr_cc) == len(prev_opr_fltnum)
            assert len(prev_opr_fltnum) == len(prev_seg_dep_dates)
            assert len(prev_seg_dep_dates) == len(prev_seg_arr_dates)
 
            orgn = geo_orgn 
            for i in range(len(prev_via)):
                dstn = prev_via[i]
                cc = prev_opr_cc[i]
                fltnum = prev_opr_fltnum[i].zfill(4)
                depdt = prev_seg_dep_dates[i]
                arrdt = prev_seg_arr_dates[i]
                res +=  orgn + dstn + depdt + arrdt + cc + fltnum
                orgn = dstn
            res += orgn + base_od_orgn +\
                   prev_seg_dep_dates[len(prev_seg_dep_dates) - 1] +\
                   prev_seg_arr_dates[len(prev_seg_arr_dates) - 1] +\
                   prev_opr_cc[len(prev_opr_cc) - 1] + prev_opr_fltnum[len(prev_opr_fltnum) - 1].zfill(4)

        # Base segments.
        if len(base_opr_cc) == 0:
            # Return empty geo_od_ts_key. Most likely these entries won't be joined, because
            # it is not clear how to join them.
            return ''
        else:
            assert len(base_od_via) + 1 == len(base_opr_cc)
        assert len(base_opr_cc) == len(base_opr_fltnum)
        assert len(base_opr_fltnum) == len(base_seg_dep_dates)
        assert len(base_seg_dep_dates) == len(base_seg_arr_dates)

        orgn = base_od_orgn
        for i in range(len(base_od_via)):
            dstn = base_od_via[i]
            cc = base_opr_cc[i] 
            fltnum = base_opr_fltnum[i].zfill(4)
            depdt = base_seg_dep_dates[i]
            arrdt = base_seg_arr_dates[i]
            res += orgn + dstn + depdt + arrdt + cc + fltnum
            orgn = dstn
        res += orgn + base_od_dstn +\
               base_seg_dep_dates[len(base_seg_dep_dates) - 1] +\
               base_seg_arr_dates[len(base_seg_arr_dates) - 1] +\
               base_opr_cc[len(base_opr_cc) - 1] + base_opr_fltnum[len(base_opr_fltnum) - 1].zfill(4)

        # Next segments.
        if len(next_opr_cc) > 0:
            assert len(next_via) + 1 == len(next_opr_cc)
            assert len(next_opr_cc) == len(next_opr_fltnum)
            assert len(next_opr_fltnum) == len(next_seg_dep_dates)
            assert len(next_seg_dep_dates) == len(next_seg_arr_dates)

            orgn = base_od_dstn
            for i in range(len(next_via)):
                dstn = next_via[i]
                cc = next_opr_cc[i]
                fltnum = next_opr_fltnum[i].zfill(4)
                depdt = next_seg_dep_dates[i]
                arrdt = next_seg_arr_dates[i]
                res += orgn + dstn + depdt + arrdt + cc + fltnum
                orgn = dstn
            res += orgn + geo_dstn +\
                   next_seg_dep_dates[len(next_seg_dep_dates) - 1] +\
                   next_seg_arr_dates[len(next_seg_arr_dates) - 1] +\
                   next_opr_cc[len(next_opr_cc) - 1] + next_opr_fltnum[len(next_opr_fltnum) - 1].zfill(4)

        return res

    @staticmethod
    def convert_geo_od_ts_key_prev_year(geo_od_ts_key):
        nsegs = int(len(geo_od_ts_key) / 28)

        res = ''
        for i in range(nsegs):
            seg = geo_od_ts_key[28 * i:28 * (i+1)]
            orgn = seg[0:3]
            dstn = seg[3:6]
            depdate = seg[6:14]
            arrdate = seg[14:22]
            cc = seg[22:24]
            fltnum = seg[24:28]    
 
            depdt = datetime.strptime(depdate, '%Y%m%d')
            arrdt = datetime.strptime(arrdate, '%Y%m%d')
            delta = (arrdt - depdt).days

            depdt_py = depdt - timedelta(days = 364)
            arrdt_py = depdt_py + timedelta(days = delta)

            res += orgn + dstn +\
                   datetime.strftime(depdt_py, '%Y%m%d') +\
                   datetime.strftime(arrdt_py, '%Y%m%d') +\
                   cc + fltnum       
        return res

    @staticmethod
    def convert_geo_od_ts_key_2_opr_od_ts_key(geo_od_ts_key):
        nsegs = int(len(geo_od_ts_key) / 28)

        res = ''
        for i in range(nsegs):
            seg = geo_od_ts_key[28 * i:28 * (i+1)]
            orgn = seg[0:3]
            dstn = seg[3:6]
            depdate = seg[6:14]
            arrdate = seg[14:22]
            cc = seg[22:24]
            if cc != 'AY':
                continue
            fltnum = seg[24:28]    
            res += orgn + dstn + depdate + arrdate + cc + fltnum
        return res

    def parse_gts(self, gts):
        '''
         geo_travel_solution consists of:
             several previous tags,
             several next tags,
             several forecast_by_pos tags.
        '''
        prevs = []
        nexts = []
        fcsts = []
        for child in gts.getchildren():
            if child.tag == 'previous':
                arrdt = BFFReader2.get_dt(child.attrib['ArrivalDateTime']).replace('-','')
                depdt = BFFReader2.get_dt(child.attrib['DepartureDateTime']).replace('-','')
                orgn,dstn,oprcc,oprfltnum,mktcc,mktfltnum = 6 * ['']
                try:
                    mktfltnum = child.attrib['FlightNumber']
                except:
                    mktfltnum = ''
                rph = child.attrib['RPH']
                for pchild in child.getchildren():
                    try:
                        tag = pchild.tag.split('}')[1]
                    except:
                        tag = pchild.tag
                    if tag == 'DepartureAirport':
                        orgn = pchild.attrib['LocationCode']
                    elif tag == 'ArrivalAirport':
                        dstn = pchild.attrib['LocationCode']
                    elif tag == 'OperatingAirline':
                        oprcc = pchild.attrib['Code']
                        oprfltnum = pchild.attrib['FlightNumber']
                    elif tag == 'MarketingAirline':
                        mktcc = pchild.attrib['Code']
                    else:
                        assert False
                prevs.append([orgn,dstn,depdt,arrdt,oprcc,oprfltnum,mktcc,mktfltnum,rph])  
            elif child.tag == 'next':
                arrdt = BFFReader2.get_dt(child.attrib['ArrivalDateTime']).replace('-','')
                depdt = BFFReader2.get_dt(child.attrib['DepartureDateTime']).replace('-','')
                orgn,dstn,oprcc,oprfltnum,mktcc,mktfltnum = 6 * [''] 
                try:
                    mktfltnum = child.attrib['FlightNumber']
                except:
                    mktfltnum = ''
                rph = child.attrib['RPH']
                for pchild in child.getchildren():
                    try:
                        # <iata:..> vs <...>
                        tag = pchild.tag.split('}')[1]
                    except:
                        tag = pchild.tag
                    if tag == 'DepartureAirport':
                        orgn = pchild.attrib['LocationCode']
                    elif tag == 'ArrivalAirport':
                        dstn = pchild.attrib['LocationCode']
                    elif tag == 'OperatingAirline':
                        oprcc = pchild.attrib['Code']
                        oprfltnum = pchild.attrib['FlightNumber']
                    elif tag == 'MarketingAirline':
                        mktcc = pchild.attrib['Code']
                    else:
                        assert False
                nexts.append([orgn,dstn,depdt,arrdt,oprcc,oprfltnum,mktcc,mktfltnum,rph])
            elif child.tag == 'forecast_by_pos':
                pos = child.attrib['pos']
                for pchild in child.getchildren():
                    assert pchild.tag == 'forecast_by_product'
                    try:
                        ff = pchild.attrib['fare_family']
                    except:
                        ff = ''
                    bc,mp,tp,\
                    pb,sfd,srd,srgcd,\
                    ard,argcd,afd = 10 * ['']
                    for ppchild in pchild.getchildren():
                        assert ppchild.tag == 'forecast_by_booking_class'
                        bc = ppchild.attrib['booking_class']
                        # System marginal profit.
                        try:
                            smp = ppchild.attrib['system_marginal_profit']
                        except:
                            assert False
                        # System marginal profit curve.
                        try:
                            smpc = ppchild.attrib['system_marginal_profit_curve']
                        except:
                            assert False
                        # Adjusted marginal profit.
                        try:
                            amp = ppchild.attrib['adjusted_marginal_profit']
                        except:
                            amp = smp
                        # Adjusted marginal profit curve.
                        try:
                            ampc = ppchild.attrib['adjusted_marginal_profit_curve']
                        except:
                            ampc = smpc

                        for pppchild in ppchild.getchildren():
                            assert pppchild.tag == 'forecast_by_travel_purpose'
                            tp = pppchild.attrib['travel_purpose'] 
                            assert len(pppchild.getchildren()) == 1 
                            f = pppchild.getchildren()[0]
                            pb = f.attrib['projected_bookings'] 

                            sfd = f.attrib['system_final_demand'] 
                            srd = f.attrib['system_remaining_demand'] 
                            srdc = f.attrib['system_remaining_demand_curve']
                            sgcd = f.attrib['system_going_class_demand']
                            sgcdc = f.attrib['system_going_class_demand_curve']
                            try:
                                srgcd = f.attrib['system_remaining_going_class_demand']
                            except:
                                srgcd = 0.0
                            try:
                                afd = f.attrib['adjusted_final_demand']
                            except:
                                afd = sfd
                            try:
                                ard = f.attrib['adjusted_remaining_demand']
                            except:
                                ard = srd
                            try:
                                ardc = f.attrib['adjusted_remaining_demand_curve']
                            except:
                                ardc = srdc
                            try:
                                agcd = f.attrib['adjusted_going_class_demand']
                            except:
                                agcd = sgcd
                            try:
                                agcdc = f.attrib['adjusted_going_class_demand_curve']
                            except:
                                agcdc = sgcdc
                            try:
                                argcd = f.attrib['adjusted_remaining_going_class_demand']
                            except:
                                argcd = srgcd 
                            fcsts.append([pos, bc, ff, smp, smpc, amp, ampc, tp, pb, \
                                          sfd, srd, srdc, sgcd, sgcdc, srgcd, \
                                          afd, ard, ardc, agcd, agcdc, argcd])
        return [prevs,nexts,fcsts]

    def parse_bts(self, btss):
        segs = []
        cms = []
        gtss = []
        for btss_child in btss.getchildren():
            if btss_child.tag == 'base_segments':
                depdt = BFFReader2.get_dt(btss_child.attrib['DepartureDateTime']).replace('-','')
                arrdt = BFFReader2.get_dt(btss_child.attrib['ArrivalDateTime']).replace('-','')
                rph = btss_child.attrib['RPH']
                orgn,dstn,oprcc,oprfltnum,mktcc,mktfltnum = 6 * ['']
                try:
                    mktfltnum = btss_child.attrib['FlightNumber']
                except:
                    mktfltnum = ''
                for btss_child_child in btss_child:
                    tag = btss_child_child.tag
                    tag = tag[(tag.find('}') + 1):]
                    if tag == 'DepartureAirport':
                        orgn = btss_child_child.attrib['LocationCode']
                    elif tag == 'ArrivalAirport':
                        dstn = btss_child_child.attrib['LocationCode']
                    elif tag == 'OperatingAirline':
                        oprcc = btss_child_child.attrib['Code']
                        oprfltnum = btss_child_child.attrib['FlightNumber']
                    elif tag == 'MarketingAirline':
                        mktcc = btss_child_child.attrib['Code']
                    else:
                        print('tag = ', tag)
                        assert False
                segs.append([orgn,dstn,depdt,arrdt,oprcc,oprfltnum,mktcc,mktfltnum,rph])
            elif btss_child.tag == 'cabin_mapping':
                bc = btss_child.attrib['booking_class']
                cp = btss_child.attrib['cabin_path']
                cms.append([bc,cp])
            elif btss_child.tag == 'geo_travel_solution':
                gtss.append(self.parse_gts(btss_child))
            else:
                assert False
        return [segs, cms, gtss]                        

    def btss(self):
        """
        Format of result:
        ------------------
        BASE_OD_ORGN       (base_board_point)
        BASE_OD_DSTN       (base_off_point)
        BASE_OD_DEP_DATE  (base_departure_date) 
        """
        ress = []
        for event, elem in etree.iterparse(self.fname, tag="OD_ForecastFeed"):
            bod_orgn, bod_dstn, bod_dept_date, btss = '', '', '', []
            for bkgfeed_child in elem.getchildren():
                if bkgfeed_child.tag == 'base_board_point':
                    bod_orgn = bkgfeed_child.text.strip()
                elif bkgfeed_child.tag == 'base_off_point':
                    bod_dstn = bkgfeed_child.text.strip()
                elif bkgfeed_child.tag == 'base_departure_date':
                    bod_dept_date = BFFReader2.get_dt(bkgfeed_child.text.strip())
                elif bkgfeed_child.tag == 'base_travel_solutions':
                    bts = self.parse_bts(bkgfeed_child)
                    ress.append([bod_orgn, bod_dstn, bod_dept_date, bts])
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
        return ress

    @staticmethod
    def dcp_from_to(dcp_from):
        if dcp_from == 1:
            return 0
        elif dcp_from == 3:
            return 2
        elif dcp_from == 6:
            return 4
        elif dcp_from == 10:
            return 7
        elif dcp_from == 15:
            return 11
        elif dcp_from == 21:
            return 16
        elif dcp_from == 28:
            return 22
        elif dcp_from == 36:
            return 29
        elif dcp_from == 48:
            return 37
        elif dcp_from == 64:
            return 49
        elif dcp_from == 84:
            return 65
        elif dcp_from == 114:
            return 85
        elif dcp_from == 154:
            return 115
        elif dcp_from == 204:
            return 155
        elif dcp_from == 264:
            return 205
        elif dcp_from == 365:
            return 265 

    @staticmethod
    def get_csv_lines(l, src_date, src_week):
        assert len(l) == 4

        base_orig = l[0]
        base_dstn = l[1]
        base_od_dept_date = l[2].replace('-','')

        ap = AirportS3()
        base_od_orgn_country, base_od_orgn_region = ap.get_aycr(base_orig)
        base_od_dstn_country, base_od_dstn_region = ap.get_aycr(base_dstn)

        segs = l[3][0]
        cms = l[3][1]
        gtss = l[3][2]

        vias = []
        oprccs = []
        oprfltnums = []
        mktccs = []
        mktfltnums = []
        segdepdates = []
        segarrdates = []
        for seg in segs:
            orgn,dstn,depdt,arrdt,oprcc,oprfltnum,mktcc,mktfltnum,rph = seg
            vias.append(dstn)
            oprccs.append(oprcc)
            oprfltnums.append(oprfltnum)
            mktccs.append(mktcc)
            mktfltnums.append(mktfltnum)
            segdepdates.append(depdt)
            segarrdates.append(arrdt)
        base_via = '-'.join(vias[:-1])
        base_opr_cc = '-'.join(oprccs)
        base_opr_fltnum = '-'.join(oprfltnums)
        base_mkt_cc = '-'.join(mktccs)
        base_mkt_fltnum = '-'.join(mktfltnums)
        base_seg_dep_dates = '-'.join(segdepdates)
        base_seg_arr_dates = '-'.join(segarrdates)

        cd = {}
        for cm in cms:
            if len(cm[1]) == 1:
                cd[cm[0]] = [cm[1],cm[1]]
            else:
                cd[cm[0]] = [min(cm[1][0],cm[1][2]),cm[1]]

        for gts in gtss:
            prevs = gts[0]
            nexts = gts[1]
            fcsts = gts[2]

            prev_via,\
            prev_opr_cc,prev_opr_fltnum,\
            prev_mkt_cc,prev_mkt_fltnum,prev_seg_dep_dates,prev_seg_arr_dates = 7 * ['']
            if len(prevs) > 0:
                geo_orgn = prevs[0][0]
                vias = []
                oprccs = []
                oprfltnums = []
                mktccs = []
                mktfltnums = []
                segdepdates = []
                segarrdates = []
                for prev in prevs:
                    orgn,dstn,depdt,arrdt,oprcc,oprfltnum,mktcc,mktfltnum,rph = prev
                    vias.append(dstn)
                    oprccs.append(oprcc)
                    oprfltnums.append(oprfltnum)
                    mktccs.append(mktcc)
                    mktfltnums.append(mktfltnum)
                    segdepdates.append(depdt)
                    segarrdates.append(arrdt)
                prev_via = '-'.join(vias[:-1])
                prev_opr_cc = '-'.join(oprccs)
                prev_opr_fltnum = '-'.join(oprfltnums)
                prev_mkt_cc = '-'.join(mktccs)
                prev_mkt_fltnum = '-'.join(mktfltnums)
                prev_seg_dep_dates = '-'.join(segdepdates)
                prev_seg_arr_dates = '-'.join(segarrdates)
            else:
                geo_orgn = base_orig

            next_via,\
            next_opr_cc,next_opr_fltnum,\
            next_mkt_cc,next_mkt_fltnum,next_seg_dep_dates,next_seg_arr_dates = 7 * ['']
            if len(nexts) > 0:
                geo_dstn = nexts[len(nexts)-1][1]
                vias = []
                oprccs = []
                oprfltnums = []
                mktccs = []
                mktfltnums = []
                segdepdates = []
                segarrdates = []
                for nxt in nexts:
                    orgn,dstn,depdt,arrdt,oprcc,oprfltnum,mktcc,mktfltnum,rph = nxt
                    vias.append(dstn)
                    oprccs.append(oprcc)
                    oprfltnums.append(oprfltnum)
                    mktccs.append(mktcc)
                    mktfltnums.append(mktfltnum)
                    segdepdates.append(depdt)
                    segarrdates.append(arrdt)
                next_via = '-'.join(vias[1:])
                next_opr_cc = '-'.join(oprccs)
                next_opr_fltnum = '-'.join(oprfltnums)
                next_mkt_cc = '-'.join(mktccs)
                next_mkt_fltnum = '-'.join(mktfltnums)
                assert len(segdepdates) == len(segarrdates)
                next_seg_dep_dates = '-'.join(segdepdates)
                next_seg_arr_dates = '-'.join(segarrdates)
            else:
                geo_dstn = base_dstn

            for fcst in fcsts:
                pos = fcst[0]
                bc = fcst[1]
                ff = fcst[2]
                smp = fcst[3]
                amp = fcst[5]
                tp = fcst[7]
                pb = fcst[8]

                sfd = fcst[9]
                srd = fcst[10]
                sgcd = fcst[12]
                srgcd = fcst[14]

                afd = fcst[15]
                ard = fcst[16]
                agcd = fcst[18]
                argcd = fcst[20]

                # Curves.
                smpc = fcst[4].lstrip("c('").rstrip("')")
                ampc = fcst[6].lstrip("c('").rstrip("')")
                srdc = fcst[11].lstrip("c('").rstrip("')")
                sgcdc = fcst[13].lstrip("c('").rstrip("')")
                ardc = fcst[17].lstrip("c('").rstrip("')")
                agcdc = fcst[19].lstrip("c('").rstrip("')")

                smpcs = smpc.split('+')
                ampcs = ampc.split('+')
                srdcs = srdc.split('+')
                sgcdcs = sgcdc.split('+')
                ardcs = ardc.split('+')
                agcdcs = agcdc.split('+')

                smpcs = [float(e.split(':')[0]) for e in smpcs]
                try:
                    ampcs = [float(e.split(':')[0]) for e in ampcs]
                except:
                    ampcs = smpcs
                srdcs = [float(e.split(':')[0]) for e in srdcs]
                sgcdcs = [float(e.split(':')[0]) for e in sgcdcs]

                try:
                    ardcs = [float(e.split(':')[0]) for e in ardcs]
                except:
                    ardcs = srdcs
                try:
                    agcdcs = [float(e.split(':')[0]) for e in agcdcs]
                except:
                    agcdcs = sgcdcs

                # System remaining going class constrained demand. 
                srdsum = sum([srdcs[i] for i in range(len(srdcs))])
                srgccd = sum([srdcs[i] if smpcs[i] > 0.0 else 0.0 for i in range(len(srdcs))])
                if srgccd > EPS:
                    smpwa = sum([smpcs[i] * srdcs[i] / srgccd if smpcs[i] > 0.0 else 0.0 for i in range(len(srdcs))])
                else:
                    smpwa = 0.0
  
                # Adjusted remaining going class constrained demand.
                ardsum = sum([ardcs[i] for i in range(len(ardcs))])
                argccd = sum([ardcs[i] if ampcs[i] > 0.0 else 0.0 for i in range(len(ardcs))])
                if argccd > EPS:
                    ampwa = sum([ampcs[i] * ardcs[i] / argccd if ampcs[i] > 0.0 else 0.0 for i in range(len(ardcs))])
                    if ampwa > 1000000:
                        assert False
                else:
                    ampwa = 0.0

                row = [base_orig, base_dstn, base_via,
                       base_od_orgn_country, base_od_orgn_region,
                       base_od_dstn_country, base_od_dstn_region,
                       base_opr_cc,base_opr_fltnum,
                       base_mkt_cc, base_mkt_fltnum, base_od_dept_date, base_seg_dep_dates, base_seg_arr_dates,
                       geo_orgn,geo_dstn,
                       prev_via, prev_opr_cc,prev_opr_fltnum,
                       prev_mkt_cc, prev_mkt_fltnum, prev_seg_dep_dates, prev_seg_arr_dates,
                       next_via, next_opr_cc, next_opr_fltnum,
                       next_mkt_cc, next_mkt_fltnum, next_seg_dep_dates, next_seg_arr_dates,
                       pos, bc, ff, smp, smpwa, amp, ampwa, tp, pb,
                       sfd, srd, srdsum, srgccd, sgcd, srgcd,
                       afd, ard, ardsum, argccd, agcd, argcd,
                       datetime.strftime(src_date,'%Y%m%d')]
                k = BFFReader2.get_geo_od_ts_key(row)
                yield [k] + row

    @staticmethod
    def get_dcp_csv_lines(l, src_date_s, ap):
        assert len(l) == 4

        base_orig = l[0]
        base_dstn = l[1]
        base_od_dept_date = l[2].replace('-','')
   
        base_od_orgn_country, base_od_orgn_region = ap.get_aycr(base_orig)
        base_od_dstn_country, base_od_dstn_region = ap.get_aycr(base_dstn)

        segs = l[3][0]
        cms = l[3][1]
        gtss = l[3][2]

        vias = []
        oprccs = []
        oprfltnums = []
        mktccs = []
        mktfltnums = []
        segdepdates = []
        segarrdates = []
        for seg in segs:
            orgn,dstn,depdt,arrdt,oprcc,oprfltnum,mktcc,mktfltnum,rph = seg
            vias.append(dstn)
            oprccs.append(oprcc)
            oprfltnums.append(oprfltnum)
            mktccs.append(mktcc)
            mktfltnums.append(mktfltnum)
            segdepdates.append(depdt)
            segarrdates.append(arrdt)
        base_via = '-'.join(vias[:-1])
        base_opr_cc = '-'.join(oprccs)
        base_opr_fltnum = '-'.join(oprfltnums)
        base_mkt_cc = '-'.join(mktccs)
        base_mkt_fltnum = '-'.join(mktfltnums)
        base_seg_dep_dates = '-'.join(segdepdates)
        base_seg_arr_dates = '-'.join(segarrdates)

        cd = {}
        for cm in cms:
            if len(cm[1]) == 1:
                cd[cm[0]] = [cm[1],cm[1]]
            else:
                cd[cm[0]] = [min(cm[1][0],cm[1][2]),cm[1]]

        for gts in gtss:
            prevs = gts[0]
            nexts = gts[1]
            fcsts = gts[2]

            prev_via,\
            prev_opr_cc,prev_opr_fltnum,\
            prev_mkt_cc,prev_mkt_fltnum,prev_seg_dep_dates,prev_seg_arr_dates = 7 * ['']
            if len(prevs) > 0:
                geo_orgn = prevs[0][0]
                vias = []
                oprccs = []
                oprfltnums = []
                mktccs = []
                mktfltnums = []
                segdepdates = []
                segarrdates = []
                for prev in prevs:
                    orgn,dstn,depdt,arrdt,oprcc,oprfltnum,mktcc,mktfltnum,rph = prev
                    vias.append(dstn)
                    oprccs.append(oprcc)
                    oprfltnums.append(oprfltnum)
                    mktccs.append(mktcc)
                    mktfltnums.append(mktfltnum)
                    segdepdates.append(depdt)
                    segarrdates.append(arrdt)
                prev_via = '-'.join(vias[:-1])
                prev_opr_cc = '-'.join(oprccs)
                prev_opr_fltnum = '-'.join(oprfltnums)
                prev_mkt_cc = '-'.join(mktccs)
                prev_mkt_fltnum = '-'.join(mktfltnums)
                prev_seg_dep_dates = '-'.join(segdepdates)
                prev_seg_arr_dates = '-'.join(segarrdates)
            else:
                geo_orgn = base_orig

            next_via,\
            next_opr_cc,next_opr_fltnum,\
            next_mkt_cc,next_mkt_fltnum,next_seg_dep_dates,next_seg_arr_dates = 7 * ['']
            if len(nexts) > 0:
                geo_dstn = nexts[len(nexts)-1][1]
                vias = []
                oprccs = []
                oprfltnums = []
                mktccs = []
                mktfltnums = []
                segdepdates = []
                segarrdates = []
                for nxt in nexts:
                    orgn,dstn,depdt,arrdt,oprcc,oprfltnum,mktcc,mktfltnum,rph = nxt
                    vias.append(dstn)
                    oprccs.append(oprcc)
                    oprfltnums.append(oprfltnum)
                    mktccs.append(mktcc)
                    mktfltnums.append(mktfltnum)
                    segdepdates.append(depdt)
                    segarrdates.append(arrdt)
                next_via = '-'.join(vias[1:])        
                next_opr_cc = '-'.join(oprccs)
                next_opr_fltnum = '-'.join(oprfltnums)
                next_mkt_cc = '-'.join(mktccs)
                next_mkt_fltnum = '-'.join(mktfltnums)
                assert len(segdepdates) == len(segarrdates)
                next_seg_dep_dates = '-'.join(segdepdates)
                next_seg_arr_dates = '-'.join(segarrdates)
            else:
                geo_dstn = base_dstn

            brow = [base_orig,base_dstn,base_via,\
                    base_od_orgn_country,base_od_orgn_region,\
                    base_od_dstn_country,base_od_dstn_region,\
                    base_opr_cc,base_opr_fltnum,\
                    base_mkt_cc,base_mkt_fltnum,base_od_dept_date,base_seg_dep_dates,base_seg_arr_dates,\
                    geo_orgn,geo_dstn,\
                    prev_via,prev_opr_cc,prev_opr_fltnum,\
                    prev_mkt_cc,prev_mkt_fltnum,prev_seg_dep_dates,prev_seg_arr_dates,\
                    next_via,next_opr_cc,next_opr_fltnum,\
                    next_mkt_cc,next_mkt_fltnum,next_seg_dep_dates,next_seg_arr_dates]
            k = BFFReader2.get_geo_od_ts_key(brow)

            for fcst in fcsts:      
                pos = fcst[0]
                bc = fcst[1]
                ff = fcst[2]

                smp = fcst[3]
                amp = fcst[5]
                tp = fcst[7]
                pb = fcst[8]

                sfd = fcst[9]
                srd = fcst[10]
                sgcd = fcst[12]
                srgcd = fcst[14]

                afd = fcst[15]
                ard = fcst[16]
                agcd = fcst[18]
                argcd = fcst[20]
     
                # Curves.
                smpc = fcst[4].lstrip("c('").rstrip("')")
                ampc = fcst[6].lstrip("c('").rstrip("')")
                srdc = fcst[11].lstrip("c('").rstrip("')")
                sgcdc = fcst[13].lstrip("c('").rstrip("')")
                ardc = fcst[17].lstrip("c('").rstrip("')")
                agcdc = fcst[19].lstrip("c('").rstrip("')")

                smpcs = smpc.split('+')
                ampcs = ampc.split('+')
                srdcs = srdc.split('+')
                sgcdcs = sgcdc.split('+')
                ardcs = ardc.split('+')
                agcdcs = agcdc.split('+')

                dcps   = [int(e.split(':')[1]) for e in smpcs]
                smpcs  = [float(e.split(':')[0]) for e in smpcs]
                try:
                    ampcs  = [float(e.split(':')[0]) for e in ampcs]
                except:
                    ampcs = smpcs
                srdcs  = [float(e.split(':')[0]) for e in srdcs]
                sgcdcs = [float(e.split(':')[0]) for e in sgcdcs]

                try:
                    ardcs  = [float(e.split(':')[0]) for e in ardcs]
                except:
                    ardcs = srdcs
                try:
                    agcdcs = [float(e.split(':')[0]) for e in agcdcs]
                except:
                    agcdcs = sgcdcs

                assert len(dcps) == len(smpcs)
                assert len(dcps) == len(ampcs)
                assert len(dcps) == len(srdcs)
                assert len(dcps) == len(sgcdcs)
                assert len(dcps) == len(ardcs)
                assert len(dcps) == len(agcdcs)

                for i in range(len(dcps)):
                    dcp = dcps[i]
                    smp = smpcs[i]
                    amp = ampcs[i]
                    srd = srdcs[i]
                    sgcd = sgcdcs[i]
                    ard = ardcs[i]
                    agcd = agcdcs[i]
                    row = brow +\
                          [pos,bc,ff,tp,\
                           dcps[i],smpcs[i],ampcs[i],srdcs[i],sgcdcs[i],ardcs[i],agcdcs[i],\
                           src_date_s]
               
                    yield [k] + row        
                
    @staticmethod
    def get_bkgdate_csv_lines(l, src_date, src_date_s, ap):
        assert len(l) == 4

        base_orig = l[0]
        base_dstn = l[1]
        base_od_dept_date = l[2].replace('-','')
   
        #base_od_orgn_country, base_od_orgn_region = ap.get_aycr(base_orig)
        #base_od_dstn_country, base_od_dstn_region = ap.get_aycr(base_dstn)

        vias = []
        oprccs = []
        oprfltnums = []
        mktccs = []
        mktfltnums = []
        segdepdates = []
        segarrdates = []
        for seg in l[3][0]:
            orgn,dstn,depdt,arrdt,oprcc,oprfltnum,mktcc,mktfltnum,rph = seg
            vias.append(dstn)
            oprccs.append(oprcc)
            oprfltnums.append(oprfltnum)
            mktccs.append(mktcc)
            mktfltnums.append(mktfltnum)
            segdepdates.append(depdt)
            segarrdates.append(arrdt)
        base_via = '-'.join(vias[:-1])
        base_opr_cc = '-'.join(oprccs)
        base_opr_fltnum = '-'.join(oprfltnums)
        base_mkt_cc = '-'.join(mktccs)
        base_mkt_fltnum = '-'.join(mktfltnums)
        base_seg_dep_dates = '-'.join(segdepdates)
        base_seg_arr_dates = '-'.join(segarrdates)

        cd = {}
        for cm in l[3][1]:
            if len(cm[1]) == 1:
                cd[cm[0]] = [cm[1],cm[1]]
            else:
                cd[cm[0]] = [min(cm[1][0],cm[1][2]),cm[1]]

        for gts in l[3][2]:
            prevs = gts[0]
            nexts = gts[1]
            fcsts = gts[2]

            prev_via,\
            prev_opr_cc,prev_opr_fltnum,\
            prev_mkt_cc,prev_mkt_fltnum,prev_seg_dep_dates,prev_seg_arr_dates = 7 * ['']
            if len(prevs) > 0:
                geo_orgn = prevs[0][0]
                vias = []
                oprccs = []
                oprfltnums = []
                mktccs = []
                mktfltnums = []
                segdepdates = []
                segarrdates = []
                for prev in prevs:
                    orgn,dstn,depdt,arrdt,oprcc,oprfltnum,mktcc,mktfltnum,rph = prev
                    vias.append(dstn)
                    oprccs.append(oprcc)
                    oprfltnums.append(oprfltnum)
                    mktccs.append(mktcc)
                    mktfltnums.append(mktfltnum)
                    segdepdates.append(depdt)
                    segarrdates.append(arrdt)
                prev_via = '-'.join(vias[:-1])
                prev_opr_cc = '-'.join(oprccs)
                prev_opr_fltnum = '-'.join(oprfltnums)
                prev_mkt_cc = '-'.join(mktccs)
                prev_mkt_fltnum = '-'.join(mktfltnums)
                prev_seg_dep_dates = '-'.join(segdepdates)
                prev_seg_arr_dates = '-'.join(segarrdates)
            else:
                geo_orgn = base_orig

            next_via,\
            next_opr_cc,next_opr_fltnum,\
            next_mkt_cc,next_mkt_fltnum,next_seg_dep_dates,next_seg_arr_dates = 7 * ['']
            if len(nexts) > 0:
                geo_dstn = nexts[len(nexts)-1][1]
                vias = []
                oprccs = []
                oprfltnums = []
                mktccs = []
                mktfltnums = []
                segdepdates = []
                segarrdates = []
                for nxt in nexts:
                    orgn,dstn,depdt,arrdt,oprcc,oprfltnum,mktcc,mktfltnum,rph = nxt
                    vias.append(dstn)
                    oprccs.append(oprcc)
                    oprfltnums.append(oprfltnum)
                    mktccs.append(mktcc)
                    mktfltnums.append(mktfltnum)
                    segdepdates.append(depdt)
                    segarrdates.append(arrdt)
                next_via = '-'.join(vias[1:])        
                next_opr_cc = '-'.join(oprccs)
                next_opr_fltnum = '-'.join(oprfltnums)
                next_mkt_cc = '-'.join(mktccs)
                next_mkt_fltnum = '-'.join(mktfltnums)
                assert len(segdepdates) == len(segarrdates)
                next_seg_dep_dates = '-'.join(segdepdates)
                next_seg_arr_dates = '-'.join(segarrdates)
            else:
                geo_dstn = base_dstn

            brow = [base_orig, base_dstn, base_via, \
                    '', '', \
                    '', '', \
                    base_opr_cc, base_opr_fltnum,\
                    base_mkt_cc, base_mkt_fltnum, base_od_dept_date, base_seg_dep_dates, base_seg_arr_dates,\
                    geo_orgn, geo_dstn,\
                    prev_via, prev_opr_cc, prev_opr_fltnum,\
                    prev_mkt_cc, prev_mkt_fltnum, prev_seg_dep_dates, prev_seg_arr_dates,\
                    next_via, next_opr_cc, next_opr_fltnum,\
                    next_mkt_cc, next_mkt_fltnum, next_seg_dep_dates, next_seg_arr_dates]
            bbrow = [base_orig, base_dstn, \
                     base_od_dept_date, \
                     geo_orgn,geo_dstn]
            k = BFFReader2.get_geo_od_ts_key(brow)
            depdate = datetime.strptime(base_od_dept_date, '%Y%m%d')

            for fcst in fcsts:      
                # Curves.
                smpc = fcst[4].lstrip("c('").rstrip("')")
                ampc = fcst[6].lstrip("c('").rstrip("')")
                srdc = fcst[11].lstrip("c('").rstrip("')")
                sgcdc = fcst[13].lstrip("c('").rstrip("')")
                ardc = fcst[17].lstrip("c('").rstrip("')")
                agcdc = fcst[19].lstrip("c('").rstrip("')")

                smpcs = smpc.split('+')
                ampcs = ampc.split('+')
                srdcs = srdc.split('+')
                sgcdcs = sgcdc.split('+')
                ardcs = ardc.split('+')
                agcdcs = agcdc.split('+')

                dcps = [int(e.split(':')[1]) for e in smpcs]
                smpcs = [float(e.split(':')[0]) for e in smpcs]
                ampcs = [float(e.split(':')[0]) for e in ampcs]
                srdcs = [float(e.split(':')[0]) for e in srdcs]
                sgcdcs = [float(e.split(':')[0]) for e in sgcdcs]

                try:
                    ardcs  = [float(e.split(':')[0]) for e in ardcs]
                except:
                    ardcs = srdcs
                try:
                    agcdcs = [float(e.split(':')[0]) for e in agcdcs]
                except:
                    agcdcs = sgcdcs

                assert len(dcps) == len(smpcs)
                assert len(dcps) == len(ampcs)
                assert len(dcps) == len(srdcs)
                assert len(dcps) == len(sgcdcs)
                assert len(dcps) == len(ardcs)
                assert len(dcps) == len(agcdcs)

                for i in range(len(dcps)):
                    dcp_to = int(BFFReader2.dcp_from_to(dcps[i]))
                    numdays = int(dcps[i]) - dcp_to + 1

                    ndays = 0
                    for j in range(numdays):
                        bkgdate = depdate - timedelta(days=dcp_to + j)
                        if bkgdate >= src_date:
                            ndays += 1    

                    if ndays == 0:
                        row = bbrow + [fcst[0],fcst[1],fcst[2],fcst[7]] +\
                                      [smpcs[i],ampcs[i],0,0,0,0,src_date_s]
                    else:
                        row = bbrow + [fcst[0],fcst[1],fcst[2],fcst[7]] +\
                                      [smpcs[i], ampcs[i], srdcs[i]/ndays, sgcdcs[i]/ndays, ardcs[i]/ndays, agcdcs[i]/ndays, src_date_s]

                    for j in range(numdays):
                        bkgdate = depdate - timedelta(days = dcp_to + j)     
                        if bkgdate >= src_date:
                            bkgdate = '{}{:02d}{:02d}'.format(bkgdate.year, bkgdate.month, bkgdate.day)
                            yield [k] + row + [bkgdate]    
 

if __name__ == "__main__":
    xmlfname = "/mnt/data/tmp/PRD.RMS.NFS.XML.D240909.T020003.AMA.FIN.DD241215.xml"
    csvoutfname = "/mnt/data/tmp/FCST_OD_20240909_20241215.csv"

    bffReader = BFFReader2(xmlfname)
    num = 0
    with gzip.open(csvoutfname + ".gz", "wt") as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(["GEO_OD_TS_KEY", "BASE_OD_ORGN", "BASE_OD_DSTN",
                            "BASE_OD_DEP_DATE", "GEO_ORGN", "GEO_DSTN",
                            "POS", "BC", "FF", "TP",
                            "SMP", "AMP", "SRD", "SGCD", "ARD", "AGCD",
                            "SRC_DATE", "BKG_DATE"])
        ap = AirportS3()
        for bts in bffReader.btss():
            sgcd = 0
            for csvline in BFFReader2.get_bkgdate_csv_lines(bts, datetime(2024, 9, 16), "20240916", ap):
                csvwriter.writerow(csvline)



