import csv
from datetime import datetime
from lxml import etree

from airport import *


class BFFReader:
    '''
    Class implements reader for BFF XML file.
    '''
    
    def __init__(self,fname):
        self.fname = fname


    @staticmethod
    def get_dt(s):
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")    


    @staticmethod
    def get_geo_od_ts_key(row):
        '''
        Returns key for joining to RS tables.
        '''
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
        pos = row[30]
        bc = row[31]
        ff = row[32]    
       
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
                arrdt = BFFReader.get_dt(child.attrib['ArrivalDateTime']).replace('-','')
                depdt = BFFReader.get_dt(child.attrib['DepartureDateTime']).replace('-','')
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
                arrdt = BFFReader.get_dt(child.attrib['ArrivalDateTime']).replace('-','')
                depdt = BFFReader.get_dt(child.attrib['DepartureDateTime']).replace('-','')
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
                pos,bc,ff,mp,tp,\
                pb,sfd,srd,srgcd,\
                ard,argcd,afd = 12 * ['']
                pos = child.attrib['pos'] 
                for pchild in child.getchildren():
                    if pchild.tag != 'forecast_by_booking_class':
                        assert False
                    bc = pchild.attrib['booking_class']
                    try: 
                        ff = pchild.attrib['fare_family']
                    except:
                        ff = ''
                    try:
                        mp = pchild.attrib['marginal_profit']
                    except:
                        mp = '0.0'
                    for ppchild in pchild.getchildren():
                        assert ppchild.tag == 'forecast_by_travel_purpose'
                        tp = ppchild.attrib['travel_purpose'] 
                        assert len(ppchild.getchildren()) == 1 
                        f = ppchild.getchildren()[0]
                        pb = f.attrib['projected_bookings'] 
                        sfd = f.attrib['system_final_demand'] 
                        srd = f.attrib['system_remaining_demand'] 
                        try:
                            srgcd = f.attrib['system_remaining_going_class_demand'] 
                        except:
                            srgcd = '0.0'
                        try:
                            ard = f.attrib['adjusted_remaining_demand'] 
                        except:
                            ard = srd # Attribute might be absent then it means it wasn't adjusted.
                        try:
                            argcd = f.attrib['adjusted_remaining_going_class_demand']
                        except:
                            argcd = srgcd # Attribute might be absent then it means it wasn't adjusted.
                        try:
                            afd = f.attrib['adjusted_final_demand'] 
                        except:
                            afd = sfd # Attribute might be absent then it means it wasn't adjusted.
                        fcsts.append([pos,bc,ff,mp,tp,pb,sfd,srd,srgcd,ard,argcd,afd])        
        return [prevs,nexts,fcsts]


    def parse_bts(self, btss):
        segs = []
        cms = []
        gtss = []
        for btss_child in btss.getchildren():
            if btss_child.tag == 'base_segments':
                depdt = BFFReader.get_dt(btss_child.attrib['DepartureDateTime']).replace('-','')
                arrdt = BFFReader.get_dt(btss_child.attrib['ArrivalDateTime']).replace('-','')
                rph = btss_child.attrib['RPH']
                orgn,dstn,oprcc,oprfltnum,mktcc,mktfltnum = 6 * ['']
                try:
                    mktfltnum = btss_child.attrib['FlightNumber']
                except:
                    mktfltnum = ''
                for btss_child_child in btss_child:
                    try:
                        # Difference in files is noticed.
                        # <iata:DepartureAirport> vs <DepartureAirport>
                        # This try-except should handle both cases.
                        tag = btss_child_child.tag.split('}')[1]
                    except:
                        tag = btss_child_child.tag
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
        '''
        Format of result:
        ------------------
        BASE_OD_ORGN       (base_board_point)
        BASE_OD_DSTN       (base_off_point)
        BASE_OD_DEP_DATE  (base_departure_date) 
        '''
        ress = []
        for event, elem in etree.iterparse(self.fname, tag="OD_ForecastFeed"):
            bod_orgn, bod_dstn, bod_dept_date, btss = '', '', '', []
            for bkgfeed_child in elem.getchildren():
                if bkgfeed_child.tag == 'base_board_point':
                    bod_orgn = bkgfeed_child.text.strip()
                elif bkgfeed_child.tag == 'base_off_point':
                    bod_dstn = bkgfeed_child.text.strip()
                elif bkgfeed_child.tag == 'base_departure_date':
                    bod_dept_date = BFFReader.get_dt(bkgfeed_child.text.strip())
                elif bkgfeed_child.tag == 'base_travel_solutions':
                    bts = self.parse_bts(bkgfeed_child)
                    ress.append([bod_orgn, bod_dstn, bod_dept_date, bts])
        return ress


    @staticmethod
    def get_csv_lines(l, src_date, src_week):
        assert len(l) == 4

        base_orig      = l[0]
        base_dstn      = l[1]
        base_od_dept_date = l[2].replace('-','')

        ap = Airport()
        base_od_orgn_country, base_od_orgn_region = ap.get_aycr(base_orig)
        base_od_dstn_country, base_od_dstn_region = ap.get_aycr(base_dstn)

        segs = l[3][0]
        cms  = l[3][1]
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
                    mktccs.append(mktfltnum)
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
                mp = fcst[3]
                tp = fcst[4]
                pb = fcst[5]
                sfd = fcst[6]
                srd = fcst[7]
                srgcd = fcst[8]
                ard = fcst[9]
                argcd = fcst[10]
                afd = fcst[11]

                row = [base_orig,base_dstn,base_via,\
                       base_od_orgn_country, base_od_orgn_region,\
                       base_od_dstn_country, base_od_dstn_region,\
                       base_opr_cc,base_opr_fltnum,\
                       base_mkt_cc,base_mkt_fltnum,base_od_dept_date,base_seg_dep_dates,base_seg_arr_dates,\
                       geo_orgn,geo_dstn,\
                       prev_via,prev_opr_cc,prev_opr_fltnum,\
                       prev_mkt_cc,prev_mkt_fltnum,prev_seg_dep_dates,prev_seg_arr_dates,\
                       next_via,next_opr_cc,next_opr_fltnum,\
                       next_mkt_cc,next_mkt_fltnum,next_seg_dep_dates,next_seg_arr_dates,\
                       pos,bc,ff,mp,tp,pb,sfd,srd,srgcd,ard,argcd,afd,datetime.strftime(src_date,'%Y%m%d')]
                k = BFFReader.get_geo_od_ts_key(row)
                yield [k] + row


if __name__ == "__main__":
    xmlfname = '/mnt/data/tmp/PRD.RMS.NFS.XML.D190820.T060004.AMA.FIN.DD191027.xml'

    # Derive source_file_date, days_to_departure and source_file_week from file name.
    src_date = datetime.strptime(xmlfname.split('/')[4].split('.')[4][1:], "%y%m%d")
    src_week = str(src_date.year) + '-' + str(src_date.isocalendar()[1])
    dep_date = datetime.strptime(xmlfname.split('/')[4].split('.')[8][2:], "%y%m%d")

    csvoutfname = '/mnt/data/tmp/FCST_OD_'+src_date.strftime("%Y%m%d")+\
                                       '_'+dep_date.strftime("%Y%m%d")+'.csv'

    bffReader = BFFReader(xmlfname)
    num = 0
    with open(csvoutfname, 'w') as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(['GEO_OD_TS_KEY','BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                            'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                            'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                            'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                            'BASE_MKT_CC','BASE_MKT_FLTNUM','BASE_OD_DEP_DATE','BASE_SEG_DEP_DATE','BASE_SEG_ARR_DATE'\
                            'GEO_ORGN','GEO_DSTN',\
                            'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM','PREV_MKT_CC','PREV_MKT_FLTNUM',\
                            'PREV_SEG_DEP_DATE','PREV_SEG_ARR_DATE',\
                            'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM','NEXT_MKT_CC','NEXT_MKT_FLTNUM',\
                            'NEXT_SEG_DEP_DATE','NEXT_SEG_ARR_DATE'\
                            'POS','BC','FF','MP','TP','PB','SFD','SRD','SRGCD','ARD','ARGCD','AFD','SRC_DATE'])

        for bts in bffReader.btss():
            for csvline in BFFReader.get_csv_lines(bts, src_date, src_week):
                csvwriter.writerow(csvline)
 
