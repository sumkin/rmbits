import csv
from datetime import datetime

from edifacter import *


class YieldReader:
    '''
    Class implements reader for BIF EDIFACT file.

    Format:
    =======

    UNB+...                             // header of the file. 
    UNH+<unh-key>+...                   // contains unh-key a.
    ODI+<orgn>+<dstn>'
    PER+L:DDMMYYHHMM/DDMMYYHHMM+<DOW>'  // specifies travel date time and day of weeks.
    TRA+<CC>' 
    STX+<flags...>'                      // Yield flags CNX,AVS,MAN,CLS,FLS.
    ATR+....'                            // Connecting airlines criteria of Yield.
    PDI++<BC>'                           // Booking class.
    MON+...                              // Value, type and currency of the yield.
    WGT+...                              // Weight of the yield.

    Yield flags:
        Connection flag CNX = 0 (Direct), 1 (Connection), 2 (All), 3 (Nonstop)
        AVS flag AVS = 0 (No), 1 (Yes)
        Manual flag MAN = 0 (No), 1 (Yes)
        Closure indicator CLS = 0 (Opened), 1 (Closed)
        Flight segment indicator FLS = 0 (No), 1 (Yes)  
    '''

    def __init__(self,fname):
        self.fname = fname
        self.edifacter = Edifacter(self.fname)


    def yields(self):
        orgn,dstn = '',''
        trvlfrm, trvlto, dows = '','',''
        salesfrm, salesto = '',''
        cc = ''
        cnx,avs,man,clsd = '','','',''
        pos, cls = '',''
        gbl_am, gbl_cr = 0.0,''
        yq_am, yq_cr = 0.0,''
        tax_am, tax_cr = 0.0,''
        weight = ''
        # 1) Why there are 2 PER+L entries? DOW is not use at the moment so all yield for all day-of-week.
        # 2) What is yield weight? Something internal for 1A. We should not care about this.
        for line in self.edifacter.next_line():
            line_code = line[:3]
            if line_code == 'UNB':
                self.srcdate = datetime.strptime(line.split(':')[1].split('+')[3], '%y%m%d')
            elif line_code == 'UNH':
                pass
            elif line_code == 'ODI':
                lparts = line.split('+')
                orgn = lparts[1].strip().strip("'")
                dstn = lparts[2].strip().strip("'")
            elif line_code == 'PER':
                if line[4] == 'L':
                    lparts = line.split(':')
                    if '+' in lparts[1]:
                        fromto, dows = lparts[1].split('+')
                        dows = dows.replace("'","").strip()
                        assert dows == '1234567'
                        trvlfrm, trvlto = fromto.split('/')
                        trvlfrm = datetime.strptime(trvlfrm, '%d%m%y')
                        trvlto = datetime.strptime(trvlto.strip("'"), '%d%m%y')
                    else:
                        fromto = lparts[1]
                        salesfrm, salesto = fromto.split('/')
                        salesfrm = datetime.strptime(salesfrm, '%d%m%y')
                        salesto = salesto.replace("'","").strip()
                        salesto = datetime.strptime(salesto, '%d%m%y')
                else:
                    assert False
            elif line_code == 'TRA':
                cc = line.split('+')[1].replace("'","").strip()
            elif line_code == 'STX':
                line = line.replace("'","")
                lparts = line.split('+')
                for lpart in lparts[1:]:
                    k,v = lpart.split(':')
                    if k == 'CNX':
                        cnx = v.strip()
                    elif k == 'AVS':
                        avs = v.strip()
                    elif k == 'MAN':
                        man = v.strip()
                    elif k == 'CLS':
                        clsd = v.strip()
                    else:
                        assert False
            elif line_code == 'ATR':
                line = line.replace("'","")
                lparts = line.split(':')
                if lparts[0] == 'ATR+B+S':
                    pos = lparts[1].strip()
                    if pos == 'ROW':
                        pass
                    elif pos[:3] == 'GEO':
                        pos = pos[4:].strip()
                    else: 
                        assert False
                else:
                    assert False    
            elif line_code == 'PDI':
                line = line.replace("'","")
                cls = line[5]
            elif line_code == 'MON':
                line = line.replace("'","").strip()
                lparts = line.split('+')
                for lpart in lparts[1:]:
                    es = lpart.split(':')
                    if es[0] == 'GBL':
                        gbl_am, gbl_cr = es[1], es[2]
                    elif es[0] == 'YQ':
                        yq_am, yq_cr = es[1], es[2]
                    elif es[0] == 'TAX':
                        tax_am, tax_cr = es[1], es[2]
                    else:
                        print(line)
                        assert False
                yield [orgn,dstn,trvlfrm,trvlto,salesfrm,salesto,dows,cc,cnx,avs,man,clsd,\
                       pos,cls,gbl_am,gbl_cr,yq_am,yq_cr,tax_am,tax_cr,weight,self.srcdate]
            elif line_code == 'EQN':
                line = line.replace("'","").strip()
                lparts = line.split('+')
                es = lparts[1].split(':')
                assert es[1] == 'WGT'
                weight = es[0]    
            elif line_code == 'UNT':
                # End of yield. Output 
                pass
            elif line_code == 'UNZ':
                # End of file.
                pass
            else:
                print(line)
                assert False      
   
 
if __name__ == "__main__":
    '''
    sys.argv[1] is input file.
    sys.argv[2] is date in format YYYYMMDD.
    sys.argv[3] is output file.
    '''
    yieldReader = YieldReader('/home/ay49514/tmp/yield')
    for line in yieldReader.yields():
        pass

    '''
    with open('/home/ay49514/tmp/INV.csv','w') as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(['CC','FLTNUM','DEPDT','ORGN','DSTN',\
                            'JCAPS','JCAPA','JCAPO','JCAPE',\
                            'YCAPS','YCAPA','YCAPO','YCAPE','SRC_DATE'])
        for leg in bifReader.legs():
            csvwriter.writerow([leg[0],leg[1],leg[2],leg[3],leg[4],\
                                leg[5],leg[6],leg[7],leg[8],\
                                leg[9],leg[10],leg[11],leg[12],leg[13]])
    '''
    
 
