import re

STATE_UNKNOWN = 0
STATE_TD = 1 
STATE_DATA = 2

SUBSTATE_UNKNOWN = 0
SUBSTATE_SKIP = -1

# Tag definition substates of SM
SUBSTATE_TD_01 = 1
SUBSTATE_TD_02 = 2
SUBSTATE_TD_03 = 3
SUBSTATE_TD_04 = 4
SUBSTATE_TD_11 = 5
SUBSTATE_TD_12 = 6
SUBSTATE_TD_13 = 7
SUBSTATE_TD_14 = 8


# Data processing substates of SM
SUBSTATE_DATA_01 = 1
SUBSTATE_DATA_02 = 2
SUBSTATE_DATA_03 = 3
SUBSTATE_DATA_04 = 4
SUBSTATE_DATA_11 = 5
SUBSTATE_DATA_12 = 6
SUBSTATE_DATA_13 = 7
SUBSTATE_DATA_14 = 8

# Output states in SM
FLUSH_IS_NOT_DONE = 0
FLUSH_IS_DONE = 1

DATA_SEPARATOR = ','

GO_AHEAD = 0
FLUSH = 1

class StateMachine:

    def __init__(self):
        self.state = STATE_UNKNOWN
        self.substate = SUBSTATE_UNKNOWN
        self.outstate = FLUSH_IS_DONE

        self.leg_tags_indices = { 'Crr':    None,
                                  'FltNum': None,
                                  'DOW':    None,
                                  'Orgn':   None,
                                  'Dstn':   None,
                                  'DptDt':  None }
        self.seg_tags_indices = { 'Crr':    None,
                                  'FltNum': None,
                                  'DOW':    None,
                                  'Orgn':   None,
                                  'Dstn':   None,
                                  'DptDt':  None }
        self.legcls_tags_indices = { 'CmpSym':     None,
                                     'ClsSym':     None,
                                     'InvCorFare': None,
                                     'PseudoFare': None,
                                     'NetTTCFare': None }
        self.segcls_tags_indices = { 'CmpSym':     None,
                                     'ClsSym':     None,
                                     'InvCorFare': None,
                                     'PseudoFare': None,
                                     'NetTTCFare': None }
        self.num_leg_tags_done = 0
        self.num_seg_tags_done = 0
        self.num_legcls_tags_done = 0
        self.num_segcls_tags_done = 0

        self.leg = {'Crr':    None,
                    'FltNum': None,
                    'DOW':    None,
                    'Orgn':   None,
                    'Dstn':   None,
                    'DptDt':  None }
        self.seg = {'Crr':    None,
                    'FltNum': None,
                    'DOW':    None,
                    'Orgn':   None,
                    'Dstn':   None,
                    'DptDt':  None }
        self.legcls = {}
        self.segcls = {}

    def move(self,line):
        [state_new, substate_new] = self._define_state(line)

        if SUBSTATE_UNKNOWN == substate_new:
            pass 
        else:
            self.state = state_new
            self.substate = substate_new

        # define tag indices
        if STATE_TD == self.state:
            if SUBSTATE_TD_01 == self.substate:
                self.fill_leg_indices(line)
            if SUBSTATE_TD_11 == self.substate:
                self.fill_seg_indices(line)  
        if STATE_TD == self.state:
            if SUBSTATE_TD_03 == self.substate:
                self.fill_legcls_indices(line)
            if SUBSTATE_TD_13 == self.substate:
                self.fill_segcls_indices(line) 

        if STATE_DATA == self.state:
            if SUBSTATE_DATA_01 == self.substate:
                if FLUSH_IS_NOT_DONE == self.outstate:
                    self.outstate = FLUSH_IS_DONE
                    return FLUSH
                else:
                    self.outstate = FLUSH_IS_NOT_DONE
                    self.fill_leg(line)
            if SUBSTATE_DATA_11 == self.substate:
                if FLUSH_IS_NOT_DONE == self.outstate:
                    self.outstate = FLUSH_IS_DONE
                    return FLUSH
                else:
                    self.outstate = FLUSH_IS_NOT_DONE
                    self.fill_seg(line)
        if STATE_DATA == self.state:
            if SUBSTATE_DATA_03 == self.substate: 
                self.fill_legcls(line)
            if SUBSTATE_DATA_13 == self.substate:
                self.fill_segcls(line)             
        return GO_AHEAD

    def get_leg_str(self):
        keys = self.legcls.keys()
        keys.sort()
        for cls in keys:
            ret = self.leg['Crr'] + '; ' + self.leg['FltNum'] + '; ' + self.leg['Orgn'] + '; ' + \
                  self.leg['Dstn'] + '; ' + self.leg['DptDt'] + '; ' + self.leg['DOW'] + '; '
            ret = ret + self.legcls[cls][0] + '; ' 
            ret = ret + cls + '; '
            ret = ret + self.legcls[cls][1] + '; '
            ret = ret + self.legcls[cls][2] + '; '
            ret = ret + self.legcls[cls][3]
            yield ret
        for key in self.leg.keys():
            self.leg[key] = None
        self.legcls = {} 

    def get_seg_str(self):
        keys = self.segcls.keys()
        keys.sort()
        for cls in keys:
            ret = self.seg['Crr'] + '; ' + self.seg['FltNum'] + '; ' + self.seg['Orgn'] + '; ' + \
                  self.seg['Dstn'] + '; ' + self.seg['DptDt'] + '; ' + self.seg['DOW'] + '; '
            ret = ret + self.segcls[cls][0] + '; '
            ret = ret + cls + '; '
            ret = ret + self.segcls[cls][1] + '; '
            ret = ret + self.segcls[cls][2] + '; '
            ret = ret + self.segcls[cls][3]
            yield ret
        for key in self.seg.keys():
            self.seg[key] = None
        self.segcls = {}

    def _define_state(self,line):
        if line.find('REM') != -1:
            state = STATE_TD
        else:
            state = STATE_DATA

        if STATE_TD == state:
            if line.find('REM <01') == 0:
                substate = SUBSTATE_TD_01
            elif line.find('REM <02') == 0:
                substate = SUBSTATE_TD_02
            elif line.find('REM <03') == 0:
                substate = SUBSTATE_TD_03
            elif line.find('REM <04') == 0:
                substate = SUBSTATE_TD_04
            elif line.find('REM <11') == 0:
                substate = SUBSTATE_TD_11
            elif line.find('REM <12') == 0:
                substate = SUBSTATE_TD_12
            elif line.find('REM <13') == 0:
                substate = SUBSTATE_TD_13
            elif line.find('REM <14') == 0:
                substate = SUBSTATE_TD_14
            else:
                substate = SUBSTATE_UNKNOWN
        elif STATE_DATA == state:
            if line.find(' 01') == 0:
                substate = SUBSTATE_DATA_01
            elif line.find(' 02') == 0:
                substate = SUBSTATE_DATA_02
            elif line.find(' 03') == 0:
                substate = SUBSTATE_DATA_03
            elif line.find(' 04') == 0:
                substate = SUBSTATE_DATA_04
            elif line.find(' 11') == 0:
                substate = SUBSTATE_DATA_11
            elif line.find(' 12') == 0:
                substate = SUBSTATE_DATA_12
            elif line.find(' 13') == 0:
                substate = SUBSTATE_DATA_13
            elif line.find(' 14') == 0:
                substate = SUBSTATE_DATA_14
            else:
                substate = SUBSTATE_UNKNOWN
        return [state, substate]

 
    def fill_leg_indices(self, line):
        res = re.findall('<[a-zA-Z]+>', line)
        for key, value in self.leg_tags_indices.iteritems():
            tmp = '<' + key + '>'
            if tmp in res:
                self.leg_tags_indices[key] = self.num_leg_tags_done + res.index(tmp) + 1
        self.num_leg_tags_done = self.num_leg_tags_done + len(res)

    def fill_seg_indices(self, line):
        # FIXME: fill_leg_indices() and fill_seg_indices()
        # should be one function.
        res = re.findall('<[a-zA-Z]+>', line)
        for key, value in self.seg_tags_indices.iteritems():
            tmp = '<' + key + '>'
            if tmp in res:
                self.seg_tags_indices[key] = self.num_seg_tags_done + res.index(tmp) + 1
        self.num_seg_tags_done = self.num_seg_tags_done + len(res)

    def fill_legcls_indices(self, line):
        res = re.findall('<[a-zA-Z]+>', line)
        for key, value in self.legcls_tags_indices.iteritems():
            tmp = '<' + key + '>'
            if tmp in res:
                self.legcls_tags_indices[key] = self.num_legcls_tags_done + res.index(tmp) + 1
        self.num_legcls_tags_done = self.num_legcls_tags_done + len(res)

    def fill_segcls_indices(self, line):
        res = re.findall('<[a-zA-Z]+>', line)
        for key, value in self.segcls_tags_indices.iteritems():
            tmp = '<' + key + '>'
            if tmp in res:
                self.segcls_tags_indices[key] = self.num_segcls_tags_done + res.index(tmp) + 1
        self.num_segcls_tags_done = self.num_segcls_tags_done + len(res)

    def fill_leg(self, line):
        res = line.split(DATA_SEPARATOR)
        #print line
        #print 'state: ' + str(self.state)
        #print 'substate: ' + str(self.substate)
        for key, value in self.leg_tags_indices.iteritems():
            #print key, value
            #if value is None:
            #    self.leg[key] = '-1'
            #else:
            self.leg[key] = res[value].strip()

    def fill_seg(self, line):
        res = line.split(DATA_SEPARATOR)
        for key, value in self.seg_tags_indices.iteritems():
            if value is None:
                self.seg[key] = '-1'
            else:
                self.seg[key] = res[value].strip()

    def fill_legcls(self, line):
        #print 'line: ' + line
        #print 'legcls_tags_indices: ',
        #print self.legcls_tags_indices
        res = line.split(DATA_SEPARATOR)
        if self.legcls_tags_indices['InvCorFare'] is None:
            inv_cor_fare_res = '-1'
        else:
            inv_cor_fare_res = res[self.legcls_tags_indices['InvCorFare']].strip()
        self.legcls[res[self.legcls_tags_indices['ClsSym']].strip()] = [ \
             res[self.legcls_tags_indices['CmpSym']].strip(), \
             res[self.legcls_tags_indices['NetTTCFare']].strip(), \
             res[self.legcls_tags_indices['PseudoFare']].strip(), \
             inv_cor_fare_res ]

    def fill_segcls(self, line):
        res = line.split(DATA_SEPARATOR)
        if self.legcls_tags_indices['InvCorFare'] is None:
            inv_cor_fare_res = '-1'
        else:
            inv_cor_fare_res = res[self.legcls_tags_indices['InvCorFare']].strip()
        self.segcls[res[self.segcls_tags_indices['ClsSym']].strip()] = [ \
            res[self.segcls_tags_indices['CmpSym']].strip(), \
            res[self.segcls_tags_indices['NetTTCFare']].strip(), \
            res[self.segcls_tags_indices['PseudoFare']].strip(), \
            inv_cor_fare_res ]


 
