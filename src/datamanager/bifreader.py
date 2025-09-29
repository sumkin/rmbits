import csv
from datetime import datetime

from edifacter import *
from utils import get_decomposition_dt

class BIFReader:
    """
    Class implements reader for BIF EDIFACT file.

    Format:
    =======

    UNB+...                             // header of the file. 
    UNH+<unh-key>+...                   // contains unh-key and some other stuff.
    FDR+<cc>+<fltnum>+<depdt>'          // flight date for which information is provided.
    FDD++INT'                           // flight status. It could be '','SO','BRB' (nothing,cancelled,under seat rebuild).  
    REF'                                // lock information. It could be '','LID','ELC' (nothing, GUI lock, emergency lock).
    STX+<code>+<code>+...               // DCS status. ACT,DCS,INA,VMS (active in DCS, sent to DCS, link broken NGI<->DCS,AutoVMS process triggered
    IFD+++R+EUR++Y'                     // Under active (Y) revenue control (R) with currency EUR.
    APD+:::::::HEL:JFK'                 // board on/off points (leg)
    DAT+708:DDMMYY:HHMM+707:DDMMYY:HHMM // Leg scheduled departure and arrival times.
    STX+FD'                             // DCS status. INA,FD,SL,ACT,PNL (none,departed,boarding,boarded figures recieved, pax name recieved). 
    EQP+J+333::OHLTS+AY'                // aircraft type (J333,OHLTS) and owner (AY).
    EQI+++++++:::33D'                   // aircraft leg configuration.
    EQD++++++A01'                       // leg saleable configuration.
    LEG+A01+NXC'                        // leg parameters for cross-cabin availability calculation NXC (no cross cabin).
    EQI+J:32+...                        // leg cabin capacity and AU. S (saleable), A (authorization), O (operational), E (effective).
    CBL+0+0+...                         // details for each leg-cabin blockspace.
    EQN+100:COF                         // leg-cabin counters. COF (cabin overbooking)...
    CBA+0+..                            // leg-cabin availabilities.
    BUC...                              // revenue control value for the leg-cabin.
    EQN+0:CSY+0:DAJ                     // counters for DCS adjustments. CSY (accepted stand-by), DAJ (DCS adjustments).
    ATR...                              // additional infor provided by RMS to other systems.

    to be continued...
    """

    def __init__(self,fname):
        self.fname = fname
        self.edifacter = Edifacter(self.fname)

    def esb(self,bkc,group_bkg,egs,amr,rcr):
        """
        Returns expected survived bookings.
        bkc        --- booking counters.
        group_bkg  --- group bookings.
        egs        --- effective group size (1A contains meaningless data, use group_bkg instead).
        amr        --- average materialization rate.
        rcr        --- remaining cancellation rate.
        """
        if group_bkg is not None and float(amr) > 0:
            res = float(group_bkg)
            res += (1 - float(rcr) / 100.0) * max(float(bkc) - float(group_bkg) / (float(amr) / 100.0), 0)
        else:
            res = (1 - float(rcr) / 100.0) * float(bkc)
        return res


    def legs(self):
        """
        Returns next leg info.
        """
        attr_lvl = ""  # ATR is child for FDR,EQI,SCI,PDI
                       # This variable tells about parent.

        cc, fltnum, depdt, deptm, arrdt, arrtm, orgn, dstn, daysprior, aircraft_type, cabin,\
        caps, capa, capo, cape, bkc, group_bkg, etb, rc, egs, amr, rcr = 22 * [None]
        for line in self.edifacter.next_line():
            line_code = line[:3]
            if line_code == 'UNB':
                lines = line.split('+')
                self.src_dt = datetime.strptime(lines[4],'%y%m%d:%H%M')
            elif line_code == 'UNH':
                pass
            elif line_code == 'FDR':
                attr_lvl = 'FDR'

                if cabin is not None:
                    # Yield result for current cabin.
                    daysprior = (depdt.date() - self.src_dt.date()).days
                    depdt_s = datetime.strftime(depdt, "%Y%m%d")
                    arrdt_s = datetime.strftime(arrdt, "%Y%m%d")
                    decompositiondt_s = get_decomposition_dt(orgn, dstn, depdt, deptm, arrdt, arrtm)
                    yield (cc, fltnum, decompositiondt_s, depdt_s, deptm, arrdt_s, arrtm,
                           orgn, dstn, daysprior, aircraft_type, cabin,
                           caps, capa, capo, cape, bkc, etb, rc,
                           egs, amr, rcr, str(self.esb(bkc, group_bkg, egs, amr, rcr)),
                           datetime.strftime(self.src_dt, "%Y%m%d"))
 
                # New flight. Clean-up all figures.
                cc, fltnum, depdt, deptm, arrdt, arrtm, orgn, dstn, daysprior, aircraft_type, cabin,\
                caps, capa, capo, cape, bkc, group_bkg, etb, rc, egs, amr, rcr = 22 * [None]

                lines = line.split('+')
                cc = lines[1]
                fltnum = lines[2]
                #depdt = datetime.strptime(lines[3].strip().strip("'"),'%d%m%y')
            elif line_code == 'FDD':
                # Flight level data.
                pass
            elif line_code == 'REF':
                # Reference information (lock).
                pass
            elif line_code == 'STX':
                # Status details (segment flags).
                pass
            elif line_code == 'IFD':
                lines = line.split('+')
                rc = lines[3]+lines[6].strip().strip("'")
            elif line_code == 'APD':
                if orgn is not None and dstn is not None:
                    # Fix for triangular flights.
                    daysprior = (depdt.date() - self.src_dt.date()).days
                    depdt_s = datetime.strftime(depdt, "%Y%m%d")
                    arrdt_s = datetime.strftime(arrdt, "%Y%m%d")
                    decompositiondt_s = get_decomposition_dt(orgn, dstn, depdt, deptm, arrdt, arrtm)
                    yield (cc, fltnum, decompositiondt_s, depdt_s, deptm, arrdt_s, arrtm,
                           orgn, dstn, daysprior, aircraft_type, cabin,
                           caps, capa, capo, cape, bkc, etb, rc,
                           egs, amr, rcr, str(self.esb(bkc, group_bkg, egs, amr, rcr)),
                           datetime.strftime(self.src_dt,'%Y%m%d'))
                    deptm, arrdt, arrtm, orgn, dstn, daysprior, aircraft_type, cabin,\
                    caps, capa, capo, cape, bkc, etb,\
                    egs, amr, rcr, bkc, group_bkg, egs, amr = [None] * 21
                    
                lines = line.split('+')
                cities = lines[1].split(':')
                cities = [e.strip() for e in cities]
                cities = [e.strip("'") for e in cities]
                orgn = cities[len(cities)-2]
                dstn = cities[len(cities)-1]
            elif line_code == 'DAT':
                # DAT+708:DDMMYY:HHMM+707:DDMMYY:HHMM' is departure and arrival time.
                # DAT+:DDMMYY:HHMM::... is datetime of file generation.
                lines = line.split('+')
                if len(lines) == 3:
                    if lines[1][:3] == '708':
                        depdt, deptm = lines[1].split(':')[1:3]
                        deptm = deptm.strip().strip("'")
                        depdt = datetime.strptime(depdt,'%d%m%y')
                    if lines[2][:3] == '707':
                        arrdt, arrtm = lines[2].split(':')[1:3]
                        arrtm = arrtm.strip().strip("'")
                        arrdt = datetime.strptime(arrdt,'%d%m%y')
            elif line_code == 'EQP':
                # Equipment information.
                pass
            elif line_code == 'EQI':
                if cabin is not None:
                    # Yield result for current cabin.
                    daysprior = (depdt.date() - self.src_dt.date()).days
                    depdt_s = datetime.strftime(depdt, "%Y%m%d")
                    arrdt_s = datetime.strftime(arrdt, "%Y%m%d")
                    decompositiondt_s = get_decomposition_dt(orgn, dstn, depdt, deptm, arrdt, arrtm)
                    yield (cc, fltnum, decompositiondt_s, depdt_s, deptm, arrdt_s, arrtm,
                           orgn, dstn, daysprior, aircraft_type,cabin,
                           caps, capa, capo, cape, bkc, etb, rc,
                           egs, amr, rcr, str(self.esb(bkc,group_bkg, egs, amr, rcr)),
                           datetime.strftime(self.src_dt,'%Y%m%d'))
                    # Clean-up cabin figures.
                    cabin, caps, capa, capo, cape, bkc, group_bkg, etb, egs, amr, rcr = 11 * [None]
 
                attr_lvl = 'EQI'

                if 'S' in line[3:] and 'A' in line[3:] and 'O' in line[3:] and 'E' in line[3:]:
                    lines = [e.strip() for e in line.split('+')]
                    for l in lines[1:]:
                        if l.strip() == '':
                            continue
                        ls = [e.strip("'") for e in l.split(':')]
                        cabin = ls[0]
                        if ls[2] == 'S':
                            caps = ls[1]
                        elif ls[2] == 'A':
                            capa = ls[1]
                        elif ls[2] == 'O':
                            capo = ls[1]
                        elif ls[2] == 'E':
                            cape = ls[1]
                        else:
                            assert False
                else:
                    # This is aircraf type.
                    lines = line.split(":")
                    aircraft_type = lines[len(lines) - 1][:-2]
            elif line_code == 'EQD':
                # Equipment information (saleable configuration).
                pass
            elif line_code == 'LEG':
                # Leg data.
                pass
            elif line_code == 'CBL':
                # Leg cabin details.
                pass
            elif line_code == 'EQN':
                # Leg date counters.
                pass
            elif line_code == 'CBA':
                line = line.replace("'","").strip();
                lparts = line.split('+')
                assert len(lparts) == 7
                # 6 numbers are:
                #   - unsold protector
                #   - booking counter
                #   - net availability
                #   - gross availability
                #   - average cancellation profile
                #   - expected to board
                bkc = lparts[2]
                etb = lparts[6]

            elif line_code == 'BUC':
                # Revenue bucket.
                pass
            elif line_code == 'ATR':
                if attr_lvl == 'EQI':
                    line = line.split('++')[1]
                    lparts = line.split('+')
                    for lpart in lparts:
                        k,v = lpart.split(':')
                        k = k.strip().strip("'")
                        v = v.strip().strip("'")
                        if k == 'EGS':
                            egs = v
                        elif k == 'REMCNLRATE':
                            rcr = v
                        elif k == 'AVGMATRATE':
                            amr = v
                    if amr is None:
                        amr = '100'
                    if rcr is None:
                        rcr = '0'
                    if egs is None:
                        egs = '0'
            elif line_code == 'ODI':
                pass
            elif line_code == 'SCI':
                attr_lvl = 'SCI'
                pass
            elif line_code == 'TBU':
                pass
            elif line_code == 'PDI':
                # Booking class.
                attr_lvl = 'PDI'
            elif line_code == 'CLA':
                pass
            elif line_code == 'SBI':
                pass
            elif line_code == 'SBC':
                parts = line.split("+")
                cls = parts[6].split(":")[-1].rstrip("0")
                if cls.isalpha() and len(cls) == 1:
                    bkg = parts[8].split(":")[0]
                    if cls == "G":
                        group_bkg = int(bkg)
                pass
            elif line_code == 'ATC':
                pass
            elif line_code == 'UNT':
                pass
            elif line_code == 'LTS':
                pass
            elif line_code == 'CAR':
                pass
            elif line_code == 'TRF':
                pass
            elif line_code == 'UNZ':
                pass
            elif line_code == 'IMD':
                pass
            else:
                assert False

if __name__ == "__main__":
    """
    sys.argv[1] is input file.
    sys.argv[2] is date in format YYYYMMDD.
    sys.argv[3] is output file.
    """
    bifReader = BIFReader('/home/ay49514/tmp/INV.DATA')
    with open('/home/ay49514/tmp/INV.csv','w') as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(["CC", "FLTNUM", "DECOMPOSITION_DT", "DEPDT", "DEPTM",
                            "ARRDT", "ARRTM", "ORGN", "DSTN", "DAYSPRIOR", "AIRCRAFT_TYPE", "CABIN",
                            "CAPS", "CAPA", "CAPO", "CAPE", "BKC", "ETB", "RC", "EGS", "AMR",
                            "RCR", "ESB", "SRC_DATE"])

        for leg in bifReader.legs():
            print(leg)
            csvwriter.writerow([leg[0], leg[1], leg[2], leg[3], leg[4], leg[5], leg[6],
                                leg[7], leg[8], leg[9], leg[10], leg[11], leg[12], leg[13],
                                leg[14], leg[15], leg[16], leg[17], leg[18], leg[19], leg[20], leg[21], leg[22]])
            
 
