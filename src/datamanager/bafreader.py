import json
from datetime import datetime

from edifacter import *
from cls import *
from airport import Airport


class BAFReader:
    '''
    Class implements reader for BAF EDIFACT file.

    Format:
    =======

    UNB+...                                                // header of the file. 
    UNH+<unh-key>+...                                      // contains unh-key and some other stuff.
    IRV++<irv-key>'                                        // contains irv-key.
    ORG++++++<pos>'                                        // contains point-of-sale information.
    TVL+<dep-date>:<dep-time>:<arr-date>:<arr-time>+       // contains info on segment.
        <seg-orig>+<seg-dstn>+<cc>+<fltnum>++<segrank>+..' 
    TVL...
    TVL...
    PDI++<cls>:<avail>+<cls>:<avail>+...                   // availability.
    '''


    def __init__(self, fname, dt):
        self.fname = fname
        self.dt = dt
        self.edifacter = Edifacter(self.fname)

        self.unh  = '' # holds current unh key value.
        self.irv  = '' # holds current irv key value.
        self.org  = '' # holds current pos value.
        self.tvls = [] # 

        self.ap2cntrmap = {} # Mapping to speed airport to country mapping.


    def ods(self):
        '''
        Returns next od info.
        '''
        for line in self.edifacter.next_line():
          line_code = line[:3]
          if line_code == 'UNB' or line_code == 'UNT' or line_code == 'ERC':
              # UNB and UNT some other stuff...
              # ERC is error or warning code.
              pass # ignore
          elif line_code == 'UNH':
              self.unh = line.split('+')[1]
          elif line_code == 'IRV':
              self.irv = line.split('++')[1].strip("'\n")
          elif line_code == 'ORG':
              try:
                  self.org = line.split('++++++')[1].strip("'\n")
              except:
                  try:
                      self.org = line.split('++++')[1].strip("'\n")
                  except:
                      pass
          elif line_code == 'TVL':
              tvl = self.parse_tvl(line)
              self.tvls.append(tvl)
          elif line_code == 'PDI':
              pdi = BAFReader.parse_pdi(line)
              # Yield the result.
              yield self.tvls,self.org,pdi 

              # Clean-up
              self.unh = self.irv = self.org = ''
              self.tvls = []
          else:
              print("WARN: Unrecognized line code ", line_code)

          line = self.edifacter.next_line()


    def parse_tvl(self, line):
        _, deparrs, orig, dstn, cc, fltnum, _, segrank, _ = line.split('+')
        depd, _, arrd, _ = deparrs.split(':')
        fltnum = fltnum.split(':')[0] # Saw example when fltnum was 0708::D 

        origcntr = None
        if orig in self.ap2cntrmap.keys():
            origcntr = self.ap2cntrmap[orig]
        else:
            try:
                ap = Airport(orig)
                origcntr = ap.get_country_code() #self.ap.get_aycr(orig)[0]
                self.ap2cntrmap[orig] = origcntr
            except Exception as e:
                print("No country for airport", orig)
                print(e)


        dstncntr = None
        if dstn in self.ap2cntrmap.keys():
            dstncntr = self.ap2cntrmap[dstn]
        else:
            try:
                ap = Airport(dstn)
                dstncntr = ap.get_country_code() #self.ap.get_aycr(dstn)[0]
            except Exception as e:
                print("Can't get country destination for airport", dstn)
                print(e)
               
            self.ap2cntrmap[dstn] = dstncntr

        return [orig,dstn,origcntr,dstncntr,depd,arrd,cc,fltnum,int(segrank)]


    @staticmethod
    def parse_pdi(line):
        code,rest = line.strip("'\n").split('++')
        clsp = rest.split('+')
        cls_l = [e.split(':') for e in clsp]
        clsd = {}
        for e in cls_l:
            clsd[e[0]] = int(e[1]) if e[1].isdigit() else 0
        return clsd


    @staticmethod
    def loc(av):
        '''
        Returns last open class for J and Y cabins.
        '''
        bus_clss = get_bus_clss()
        econ_clss = get_econ_clss()
        
        num, num_wosc = 1,1
        locj, locij = '', 0
        locj_wosc, locij_wosc = '', 0 # wosc - without special classes.
        for c in bus_clss:
            if c in av.keys() and av[c] > 0:
                if not is_special_cls(c):
                    locj_wosc = c
                    locij_wosc = num_wosc
                locj = c
                locij = num
            num += 1 
            if not is_special_cls(c):
                num_wosc += 1    
        
        num, num_wosc = 1,1
        locy, lociy = '', 0
        locy_wosc, lociy_wosc = '', 0 # wosc - without special clssses.
        for c in econ_clss:
            if c in av.keys() and av[c] > 0:
                if not is_special_cls(c):
                    locy_wosc = c
                    lociy_wosc = num_wosc
                locy = c
                lociy = num
            num += 1
            if not is_special_cls(c):
                num_wosc += 1

        return locj, locij, locy, lociy, locj_wosc, locij_wosc, locy_wosc, lociy_wosc


    def get_csv_line(self,od):

        def get_pos_type(origcntr,dstncntr,pos):
            if origcntr == pos:
                return 'ON'
            elif dstncntr == pos:
                return 'OFF'
            else:
                return 'ROW'

        def cnvrt_date(d):
            return datetime(int('20'+d[4:]), int(d[2:4]), int(d[:2]))


        if len(od[0]) == 1:
            tvl = od[0][0]

            res = []
            res.append(tvl[0]) # ORIG
            res.append(tvl[1]) # DSTN
            res.append('') # VIA
            res.append(tvl[6]) # CC
            res.append(str(int(tvl[7]))) # FLTNUM
            dt = cnvrt_date(tvl[4])
            res.append(dt.strftime("%Y%m%d")) # OD_DEPT_DATE
            res.append(dt.weekday()) # OD_DEPT_DOW
            res.append(dt.strftime("%Y%m%d")) # SEG_DEPT_DATE
            if od[1] == 'ZZ':
                res.append('ROW')
            else:
                res.append(od[1]) # POS
            res.append(get_pos_type(tvl[2],tvl[3],od[1])) # POSTYPE
            av = od[2]         
            for c in classes: 
                if c in av.keys():
                    res.append(av[c])
                else:
                    res.append(0)
            # LOCJ,LOCIJ,LOCY,LOCIY,LOCJ_WOSC,LOCIJ_WOSC,LOCY_WOSC,LOCIY_WOSC
            LOCJ,LOCIJ,LOCY,LOCIY,\
            LOCJ_WOSC,LOCIJ_WOSC,LOCY_WOSC,\
            LOCIY_WOSC = BAFReader.loc(av) 
            res.append(LOCJ)
            res.append(LOCIJ)
            res.append(LOCY)
            res.append(LOCIY)
            res.append(LOCJ_WOSC)
            res.append(LOCIJ_WOSC)
            res.append(LOCY_WOSC)
            res.append(LOCIY_WOSC)
            res.append(self.dt.strftime('%Y%m%d')) # SRC_DATE
            return res
        elif len(od[0]) > 1:
            tvls = od[0]

            res = []
            res.append(tvls[0][0]) # ORIG
            res.append(tvls[len(tvls)-1][1]) # DSTN
            res.append('-'.join([tvl[0] for tvl in tvls[1:]])) # VIA     
            res.append('-'.join([tvl[6] for tvl in tvls])) # CC
            try:
                res.append('-'.join([str(int(tvl[7])) for tvl in tvls])) # FLTNUM
            except Exception as e:
                print([tvl for tvl in tvls])
                raise e
            dt = cnvrt_date(tvls[0][4])
            res.append(dt.strftime("%Y%m%d")) # OD_DEPT_DATE
            res.append(dt.weekday()) # OD_DEPT_DOW
            res.append('-'.join([cnvrt_date(tvl[4]).strftime("%Y%m%d") for tvl in tvls])) # SEG_DEPT_DATE
            if od[1] == 'ZZ':
                res.append('ROW')
            else:
                res.append(od[1]) # POS
            res.append(get_pos_type(tvls[0][2], tvls[len(tvls)-1][3], od[1])) # POSTYPE
            av = od[2]
            for c in classes:
                if c in av.keys():
                    res.append(av[c])
                else:
                    res.append(0)
            # LOCJ,LOCIJ,LOCY,LOCIY,LOCJ_WOSC,LOCIJ_WOSC,LOCY_WOSC,LOCIY_WOSC
            LOCJ,LOCIJ,LOCY,LOCIY,\
            LOCJ_WOSC,LOCIJ_WOSC,LOCY_WOSC,\
            LOCIY_WOSC = BAFReader.loc(av)
            res.append(LOCJ)
            res.append(LOCIJ)
            res.append(LOCY)
            res.append(LOCIY)
            res.append(LOCJ_WOSC)
            res.append(LOCIJ_WOSC)
            res.append(LOCY_WOSC)
            res.append(LOCIY_WOSC)
            res.append(self.dt.strftime('%Y%m%d')) # SRC_DATE
            return res
        else:
            assert False
            
          
if __name__ == "__main__":
    '''
    sys.argv[1] is input file.
    sys.argv[2] is date in format YYYYMMDD.
    sys.argv[3] is output file.
    '''
    if len(sys.argv) == 4:
        dt = datetime.strptime(sys.argv[2], '%Y%m%d')
        bafReader = BAFReader(sys.argv[1], dt)
        with open(sys.argv[3],'w') as fout:
            csvwriter = csv.writer(fout)
            csvwriter.writerow(['ORIG','DSTN','VIA','CC','FLTNUM',\
                                'OD_DEPT_DATE','OD_DEPT_DOW','SEG_DEPT_DATE',\
                                'POS','POSTYPE','LOCJ','LOCIJ','LOCY','LOCIY',\
                                'J','C','D','I','F','U',\
                                'Y','B','H','K','M','P',\
                                'T','L','V','S','N','G',\
                                'A','Q','O','Z','R','W',\
                                'X','E',\
                                'LOCJ_WOSC','LOCIJ_WOSC','LOCY_WOSC',\
                                'LOCIY_WOSC','SRC_DATE'])
            for od in bafReader.ods():
                csvline = bafReader.get_csv_line(od)
                csvwriter.writerow(csvline)
    else:
        print("Wrong number of arguments")

    
 
