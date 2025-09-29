import csv
from datetime import datetime
from lxml import etree

from cls import *
from airport_s3 import *
from geo_yield_lookup import *
from bffreader2 import *


class BOFReader:
    '''
    Class implements reader for BOF XML file.
    '''
    
    def __init__(self,fname,dt):
        self.fname = fname
        self.dt = dt
        self.yl = GeoYieldLookup(datetime.strftime(dt, '%Y%m%d'))
        self.ap = AirportS3()


    @staticmethod
    def get_dt(s):
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S").strftime("%Y%m%d")    


    def parse_gts(self, gts):
        '''
         geo_travel_solution consists of:
             several previous tags,
             several next tags,
             several passanger tags.
        '''
        prevs = []
        nexts = []
        paxs = []
        for child in gts.getchildren():
            if child.tag == 'previous':
                arrdt = BOFReader.get_dt(child.attrib['ArrivalDateTime'])
                depdt = BOFReader.get_dt(child.attrib['DepartureDateTime'])
                mktfltnum = child.attrib['FlightNumber']
                rph = child.attrib['RPH']
                orgn,dstn,oprcc,oprfltnum,mktcc = 5 * ['']
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
                if oprcc == '' and oprfltnum == '':
                    oprcc, oprfltnum = mktcc, mktfltnum
                prevs.append([orgn,dstn,depdt,arrdt,oprcc,oprfltnum,mktcc,mktfltnum,rph])
            elif child.tag == 'next': 
                arrdt = BOFReader.get_dt(child.attrib['ArrivalDateTime'])
                depdt = BOFReader.get_dt(child.attrib['DepartureDateTime'])
                mktfltnum = child.attrib['FlightNumber'] 
                rph = child.attrib['RPH']
                orgn,dstn,oprcc,oprfltnum,mktcc = 5 * ['']
                for pchild in child.getchildren():
                    try:
                        # <iata:...> vs <...>
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
                if oprcc == '' and oprfltnum == '':
                    oprcc,oprfltnum = mktcc, mktfltnum 
                nexts.append([orgn,dstn,depdt,arrdt,oprcc,oprfltnum,mktcc,mktfltnum,rph])
            elif child.tag == 'passenger':
                '''
                passenger element consists of:
                  -- booking type tag
                  -- POS tag
                  -- booking tag
                '''
                rlocator, tdirection,\
                bkg_type, pseudocitycode, isocountry,\
                agdutycode, requestorid, sellcls, cabin,\
                reference = 10 * ['']
                for pchild in child.getchildren():
                    try:
                        # <iata:...> vs <...>
                        tag = pchild.tag.split('}')[1]
                    except:
                        tag = pchild.tag
                    if tag == 'record_locator':
                        try:
                            rlocator = pchild.text.strip()    
                        except:
                            rlocator = ''
                    elif tag == 'travel_direction':
                        try:
                            tdirection = pchild.text.strip()
                        except:
                            tdirection = ''
                    elif tag == 'booking_type':
                        bkg_type = pchild.text.strip()
                    elif tag == 'PoS':
                        ppchild = pchild.getchildren()[0]
                        try:
                            pseudocitycode = ppchild.attrib['PseudoCityCode']
                        except:
                            pseudocitycode = ''
                        isocountry = ppchild.attrib['ISOCountry']
                        try:
                            agdutycode = int(ppchild.attrib['AgentDutyCode'])
                        except:
                            agdutycode = ''
                        pppchild = ppchild.getchildren()[0]
                        requestorid = pppchild.attrib['ID']
                    elif tag == 'booking':
                        for ppchild in pchild.getchildren():
                            try:
                                # <iata:...> vs <...>
                                tag = ppchild.tag.split('}')[1]
                            except:
                                tag = ppchild.tag
                            if tag == 'selling_class':
                                sellcls = ppchild.text.strip()
                            elif tag == 'cabin':
                                cabin = ppchild.text.strip()
                            elif tag == 'reference':
                                reference = ppchild.text.strip()
                paxs.append([rlocator, tdirection, bkg_type, pseudocitycode, isocountry,\
                             agdutycode, requestorid, sellcls, cabin, reference]) 
        return [prevs,nexts,paxs]


    def parse_bts(self, btss):
        segs = []
        gtss = []
        for btss_child in btss.getchildren():
            if btss_child.tag == 'base_segments':
                depdt = BOFReader.get_dt(btss_child.attrib['DepartureDateTime'])
                arrdt = BOFReader.get_dt(btss_child.attrib['ArrivalDateTime'])
                rph = btss_child.attrib['RPH']
                orgn,dstn,oprcc,oprfltnum,mktcc,mktfltnum = 6 * ['']
                mktfltnum = btss_child.attrib['FlightNumber']
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
                if oprcc == '' and oprfltnum == '':
                    oprcc, oprfltnum = mktcc, mktfltnum
                segs.append([orgn,dstn,depdt,arrdt,oprcc,oprfltnum,mktcc,mktfltnum,rph])
            elif btss_child.tag == 'geo_travel_solution':
                gts = self.parse_gts(btss_child)
                gtss.append(gts)
            else:
                assert False
        return [segs, gtss]                        


    def btss(self):
        '''
        Format of result:
        ------------------
        BASE_OD_ORGN       (base_board_point)
        BASE_OD_DSTN       (base_off_point)
        BASE_OD_DEPT_DATE  (base_departure_date) 
        '''
        for event, elem in etree.iterparse(self.fname, tag = "OD_BookingFeed"):
            bod_orgn, bod_dstn, bod_dept_date = '', '', ''
            for bkgfeed_child in elem.getchildren():
                if bkgfeed_child.tag == 'base_board_point':
                    bod_orgn = bkgfeed_child.text.strip()
                elif bkgfeed_child.tag == 'base_off_point':
                    bod_dstn = bkgfeed_child.text.strip()
                elif bkgfeed_child.tag == 'base_departure_date':
                    bod_dept_date = BOFReader.get_dt(bkgfeed_child.text.strip())
                elif bkgfeed_child.tag == 'base_travel_solutions':
                    bts = self.parse_bts(bkgfeed_child)
                    yield [bod_orgn, bod_dstn, bod_dept_date, bts]


    @staticmethod
    def get_segs_str(segs):
        if len(segs) == 0:
            return '','','','','','',''
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
        via = '-'.join(vias[:-1])
        oprcc = '-'.join(oprccs)
        oprfltnums = [str(int(e)) for e in oprfltnums]
        oprfltnum = '-'.join(oprfltnums)
        mktcc = '-'.join(mktccs)
        mktfltnums = [str(int(e)) for e in mktfltnums]
        mktfltnum = '-'.join(mktfltnums)
        segdepdate = '-'.join(segdepdates)
        segarrdate = '-'.join(segarrdates)
        return via,oprcc,oprfltnum,mktcc,mktfltnum,segdepdate,segarrdate


    def get_od_csv_lines(self, l, src_date, src_week):
        assert len(l) == 4

        base_orig         = l[0]
        base_dstn         = l[1]
        base_od_dept_date = datetime.strptime(l[2], '%Y%m%d')

        base_od_orgn_country, base_od_orgn_region = self.ap.get_aycr(base_orig)
        base_od_dstn_country, base_od_dstn_region = self.ap.get_aycr(base_dstn)

        segs = l[3][0] # base segments
        gtss = l[3][1] # geo travel solutions

        base_via, base_opr_cc, base_opr_fltnum,\
        base_mkt_cc, base_mkt_fltnum, base_seg_dep_date,base_seg_arr_date = BOFReader.get_segs_str(segs)
       
        for gts in gtss: 
            prevs = gts[0]
            nexts = gts[1]
            paxs = gts[2]
       
            prev_via,\
            prev_opr_cc,prev_opr_fltnum,\
            prev_mkt_cc,prev_mkt_fltnum,prev_seg_dept_date,prev_seg_arr_date = 7 * ['']
            if len(prevs) > 0:    
                geo_orgn = prevs[0][0]
                prev_via, prev_opr_cc, prev_opr_fltnum,\
                prev_mkt_cc, prev_mkt_fltnum, prev_seg_dept_date, prev_seg_arr_date = BOFReader.get_segs_str(prevs)
            else:
                geo_orgn = base_orig

            next_via,\
            next_opr_cc,next_opr_fltnum,\
            next_mkt_cc,next_mkt_fltnum,next_seg_dept_date,next_seg_arr_date = 7 * ['']
            if len(nexts) > 0:
                geo_dstn = nexts[len(nexts)-1][1]
                next_via, next_opr_cc, next_opr_fltnum,\
                next_mkt_cc, next_mkt_fltnum, next_seg_dept_date, next_seg_arr_date = BOFReader.get_segs_str(nexts)
            else:
                geo_dstn = base_dstn
            

            for pax in paxs:
                rlocator = pax[0]
                tdirection = pax[1]
                bkg_type = pax[2]
                pseudo_city_code = pax[3]
                iso_country = pax[4]
                iso_region = self.ap.get_ayr(iso_country)
                agduty_code = pax[5]
                requestor_id = pax[6]
                sell_cls = pax[7]
                cabin = pax[8]
                reference = pax[9]
                daysprior = (base_od_dept_date.date() - src_date.date()).days
                yld = self.yl.lookup(base_orig, base_dstn, iso_country, sell_cls)

                base_od_dept_date_s = datetime.strftime(base_od_dept_date,'%Y%m%d')
                src_date_s = datetime.strftime(src_date,'%Y%m%d')

                row = [base_orig,base_dstn,base_via,\
                       base_od_orgn_country, base_od_orgn_region,\
                       base_od_dstn_country, base_od_dstn_region,\
                       base_opr_cc,base_opr_fltnum,\
                       base_mkt_cc,base_mkt_fltnum,base_od_dept_date_s,daysprior,\
                       base_seg_dep_date,base_seg_arr_date,\
                       geo_orgn,geo_dstn,\
                       prev_via,prev_opr_cc,prev_opr_fltnum,\
                       prev_mkt_cc,prev_mkt_fltnum,prev_seg_dept_date,prev_seg_arr_date,\
                       next_via,next_opr_cc,next_opr_fltnum,\
                       next_mkt_cc,next_mkt_fltnum,next_seg_dept_date,next_seg_arr_date,\
                       rlocator, tdirection,\
                       bkg_type,pseudo_city_code,iso_country,iso_region,agduty_code,\
                       requestor_id,sell_cls,cabin,reference,yld,src_date_s]
                k = BFFReader2.get_geo_od_ts_key(row, bof = True)
                yield [k] + row
    

    def get_seg_csv_lines(self, l, src_date, src_week):
        assert len(l) == 4

        base_orig         = l[0]
        base_dstn         = l[1]

        base_od_dept_date = datetime.strptime(l[2], '%Y%m%d')

        segs = l[3][0] # base segments
        gtss = l[3][1] # geo travel solutions

        for gts in gtss:
            prevs = gts[0]
            nexts = gts[1]
            paxs = gts[2]
      
            if len(prevs) > 0:    
                geo_orgn = prevs[0][0]
            else:
                geo_orgn = base_orig

            if len(nexts) > 0:
                geo_dstn = nexts[len(nexts)-1][0]
            else:
                geo_dstn = base_dstn

            for pax in paxs:
                rlocator = pax[0]
                tdirection = pax[1]
                bkg_type = pax[2]
                pseudo_city_code = pax[3]
                iso_country = pax[4]
                iso_region = self.ap.get_ayr(iso_country)
                agduty_code = pax[5]
                requestor_id = pax[6]
                sell_cls = pax[7]
                cabin = pax[8]
                reference = pax[9]

                index = 0
                for seg in segs:
                    prev_via, prev_opr_cc, prev_opr_fltnum,\
                    prev_mkt_cc, prev_mkt_fltnum, prev_seg_dept_date, prev_seg_arr_date = BOFReader.get_segs_str(prevs + segs[:index])

                    next_via, next_opr_cc, next_opr_fltnum,\
                    next_mkt_cc, next_mkt_fltnum, next_seg_dept_date, next_seg_arr_date = BOFReader.get_segs_str(segs[index+1:] + nexts)

                    orgn,dstn,depdt,arrdt,oprcc,oprfltnum,mktcc,mktfltnum,rph = seg
                    depdt = depdt.replace('-','')
                    daysprior = (datetime.strptime(depdt,'%Y%m%d').date() - src_date.date()).days

                    src_date_s = datetime.strftime(src_date,'%Y%m%d')

                    yield [orgn,dstn,oprcc,oprfltnum,mktcc,mktfltnum,depdt,arrdt,daysprior,\
                           geo_orgn,geo_dstn,\
                           prev_via,prev_opr_cc,prev_opr_fltnum,\
                           prev_mkt_cc,prev_mkt_fltnum,prev_seg_dept_date,prev_seg_arr_date,\
                           next_via,next_opr_cc,next_opr_fltnum,\
                           next_mkt_cc,next_mkt_fltnum,next_seg_dept_date,next_seg_arr_date,\
                           rlocator, tdirection,\
                           bkg_type,pseudo_city_code,iso_country,iso_region,agduty_code,\
                           requestor_id,sell_cls,cabin,reference,src_date_s]
                    index += 1
 

if __name__ == "__main__":
    dt = datetime(2020,10,24) #datetime.now()
    xmlfname = '/mnt/data/tmp/PRD.NGI.IBAONDXML.ODB_FEED.D201024.T160056.AMA.FIN.FTP.DATA'

    # Derive source_file_date and source_file_week from file name.
    src_date = datetime.strptime(xmlfname.split('/')[4].split('.')[4][1:], "%y%m%d")
    src_week = str(src_date.year) + '-' + str(src_date.isocalendar()[1])

    od_csvoutfname = '/mnt/data/tmp/BKG_OD_' + src_date.strftime("%Y%m%d") + '.csv'
    seg_csvoutfname = '/mnt/data/tmp/BKG_SEG_' + src_date.strftime("%Y%m%d") + '.csv'

    bofReader = BOFReader(xmlfname, dt)
    num = 0
    with open(od_csvoutfname, 'w') as od_fout:
        with open(seg_csvoutfname, 'w') as seg_fout: 
            od_csvwriter = csv.writer(od_fout)
            od_csvwriter.writerow(['GEO_OD_TS_KEY',\
                                   'BASE_OD_ORGN','BASE_OD_DSTN','BASE_OD_VIA',\
                                   'BASE_OD_ORGN_COUNTRY','BASE_OD_ORGN_REGION',\
                                   'BASE_OD_DSTN_COUNTRY','BASE_OD_DSTN_REGION',\
                                   'BASE_OPR_CC','BASE_OPR_FLTNUM',\
                                   'BASE_MKT_CC','BASE_MKT_FLTNUM','BASE_OD_DEPT_DATE','DAYSPRIOR',\
                                   'BASE_SEG_DEPT_DATE','BASE_SEG_ARR_DATE',\
                                   'GEO_ORGN','GEO_DSTN',\
                                   'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM','PREV_MKT_CC','PREV_MKT_FLTNUM',\
                                   'PREV_SEG_DEPT_DATE','PREV_SEG_ARR_DATE',\
                                   'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM','NEXT_MKT_CC','NEXT_MKT_FLTNUM',\
                                   'NEXT_SEG_DEPT_DATE','NEXT_SEG_ARR_DATE',\
                                   'RLOCATOR','TDIRECTION',\
                                   'BKG_TYPE','PSEUDO_CITY_CODE','ISO_COUNTRY','ISO_REGION','AGDUTY_CODE','REQUESTOR_ID',\
                                   'SELL_CLS','CABIN','REFERENCE','YIELD','SRC_DATE'])
            seg_csvwriter = csv.writer(seg_fout)
            seg_csvwriter.writerow(['ORGN','DSTN','OPR_CC','OPR_FLTNUM','MKT_CC','MKT_FLTNUM','DEPT_DATE','ARR_DATE','DAYSPRIOR',\
                                    'GEO_ORGN','GEO_DSTN',\
                                    'PREV_VIA','PREV_OPR_CC','PREV_OPR_FLTNUM','PREV_MKT_CC','PREV_MKT_FLTNUM',\
                                    'PREV_SEG_DEPT_DATE','PREV_SEG_ARR_DATE',\
                                    'NEXT_VIA','NEXT_OPR_CC','NEXT_OPR_FLTNUM','NEXT_MKT_CC','NEXT_MKT_FLTNUM',\
                                    'NEXT_SEG_DEPT_DATE','NEXT_SEG_ARR_DATE',\
                                    'RLOCATOR','TDIRECTION',\
                                    'BKG_TYPE','PSEUDO_CITY_CODE','ISO_COUNTRY','ISO_REGION','AGDUTY_CODE','REQUESTOR_ID',\
                                    'SELL_CLS','CABIN','REFERENCE','SRC_DATE'])
 
            for bts in bofReader.btss():
                for csvline in bofReader.get_od_csv_lines(bts, src_date, src_week):
                    od_csvwriter.writerow(csvline)
                for csvline in bofReader.get_seg_csv_lines(bts, src_date, src_week):
                    seg_csvwriter.writerow(csvline)


 
