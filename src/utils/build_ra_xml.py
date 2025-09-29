import os
import sys
import csv
import ConfigParser
from datetime import date

# Read config
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)
sys.path.append(config.get('PATHS','datamanager'))

from db_connector import dbConnector
from xml.dom.minidom import Document

if __name__ == '__main__':

    file_num = 0
    curs = dbConnector.get_or_curs()

    q = "SELECT DISTINCT dow, path, flight_nums, dep_dates\
         FROM ra_data"
    curs.execute(q)
    rows = curs.fetchall()

    i = 0

    for row in rows:

        if i % 20000 == 0:
            doc = Document()
            odif = doc.createElement("ODIF_data")
            doc.appendChild(odif)
            
        i += 1
        print i

        dow         = str(row[0])
        path        = row[1]
        flight_nums = row[2]
        dep_dates   = row[3]   

        legs    = path.split(" ")
        flights = flight_nums.split(" ")
        dates    = dep_dates.split(" ")         

        if len(legs) != len(flights) or len(flights) != len(dates):
            continue

        it = doc.createElement("IT")
        odif.appendChild(it)
 
        itdt       = doc.createElement("ITDT")
        itdt_txt   = doc.createTextNode(dates[0])
        itdt.appendChild(itdt_txt)
        it.appendChild(itdt)

        itdw     = doc.createElement("ITDW")
        itdw_txt = doc.createTextNode(dow)
        itdw.appendChild(itdw_txt)
        it.appendChild(itdw)

        ito     = doc.createElement("ITO")
        ito_txt = doc.createTextNode(legs[0].split("-")[0])
        ito.appendChild(ito_txt)
        it.appendChild(ito)

        itd     = doc.createElement("ITD")
        itd_txt = doc.createTextNode(legs[len(legs)-1].split("-")[1])
        itd.appendChild(itd_txt)
        it.appendChild(itd)

        for leg in legs:
            ind = legs.index(leg)

            itl     = doc.createElement("ITL")
            crr     = doc.createElement("CR")
            crr_txt = doc.createTextNode("AY")
            crr.appendChild(crr_txt)
            itl.appendChild(crr)

            fn     = doc.createElement("FN")
            fn_txt = doc.createTextNode(flights[ind])
            #fn_txt = fn_txt[1:]
            fn.appendChild(fn_txt)
            itl.appendChild(fn)

            dt_s = dates[ind]
            dt_s_y = dt_s[0:4]
            dt_s_m = dt_s[4:6]
            dt_s_d = dt_s[6:8]
            dt = date(int(dt_s_y),int(dt_s_m),int(dt_s_d))           
 
            ldw     = doc.createElement("LDW")
            ldw_txt = doc.createTextNode(str(dt.weekday()+1))
            ldw.appendChild(ldw_txt)
            itl.appendChild(ldw)

            ldt     = doc.createElement("LDT")
            ldt_txt = doc.createTextNode(dates[ind])
            ldt.appendChild(ldt_txt)
            itl.appendChild(ldt)

            lo     = doc.createElement("LO")
            lo_txt = doc.createTextNode(leg.split("-")[0])
            lo.appendChild(lo_txt)
            itl.appendChild(lo)

            ld     = doc.createElement("LD")
            ld_txt = doc.createTextNode(leg.split("-")[1])
            ld.appendChild(ld_txt) 
            itl.appendChild(ld)

            it.appendChild(itl)

        sub_q = "SELECT DISTINCT pos FROM ra_data\
                 WHERE dow = " + dow  + " AND\
                       path = '" + path + "' AND\
                       flight_nums = '" + flight_nums + "' AND\
                       dep_dates = '" + dep_dates + "'"
        curs.execute(sub_q)

        sub_rows = curs.fetchall()
        for sub_row in sub_rows:
            pos = sub_row[0]
        
            psd = doc.createElement("PSD")
            it.appendChild(psd) 
            
            psc     = doc.createElement("PSC")
            psc_txt = doc.createTextNode("XXX")
            psc.appendChild(psc_txt)
            psd.appendChild(psc)

            pscy     = doc.createElement("PSCY")
            pscy_txt = doc.createTextNode(str(pos))
            pscy.appendChild(pscy_txt)
            psd.appendChild(pscy)

            cdm = doc.createElement("CDM")
            psd.appendChild(cdm)

            cmps = ['J','Y']

            for cmpt in cmps:
                cc = doc.createElement("CC")
                cc_txt = doc.createTextNode(cmpt)
                cc.appendChild(cc_txt)
                cdm.appendChild(cc)

                sub_sub_q = "SELECT DISTINCT ra_data.cls, tot_client_net_net_rev, pax_cnt\
                             FROM ra_data,nesting\
                             WHERE dow = " + str(dow) + " AND\
                                   pos = '" + pos + "' AND\
                                   path = '" + path + "' AND\
                                   flight_nums = '" + flight_nums + "' AND\
                                   dep_dates = '" + dep_dates + "' AND\
                                   nesting.cls = ra_data.cls AND nesting.cmp = '" + cmpt + "'"
                curs.execute(sub_sub_q)
                sub_sub_rows = curs.fetchall()

                for sub_sub_row in sub_sub_rows:
                    cls = sub_sub_row[0]
                    fare = sub_sub_row[1]
                    pax_cnt = sub_sub_row[2]

                    fdm = doc.createElement("FDM")
                    cdm.appendChild(fdm)
                
                    bc = doc.createElement("BC")
                    bc_txt = doc.createTextNode(cls)
                    bc.appendChild(bc_txt)
                    fdm.appendChild(bc)
              
                    fcd = doc.createElement("FCD")
                    fcd_txt = doc.createTextNode(cls)
                    fcd.appendChild(fcd_txt)
                    fdm.appendChild(fcd) 
 
                    idd = doc.createElement("ID")
                    idd_txt = doc.createTextNode("0")
                    idd.appendChild(idd_txt)
                    fdm.appendChild(idd)
 
                    f = doc.createElement("F")
                    if pax_cnt != 0:
                        f_txt = doc.createTextNode(str(float(fare)/pax_cnt))
                    else:
                        f_txt = ''
                    f.appendChild(f_txt)
                    fdm.appendChild(f)

                    fd = doc.createElement("FD")
                    fd_txt = doc.createTextNode(str(pax_cnt))
                    fd.appendChild(fd_txt)
                    fdm.appendChild(fd)

                    up = doc.createElement("UP")
                    up_txt = doc.createTextNode(str(pax_cnt))
                    up.appendChild(up_txt)
                    fdm.appendChild(up)

        if i % 20000 == 0:

            f = open('out_' + str(file_num) + '.xml','w')
            doc.writexml(f)
            f.close()
            del doc
            file_num += 1
            print str(file_num) + ' is written'

    f = open('out_' + str(file_num) + '.xml','w')
    doc.writexml(f)
    f.close()





