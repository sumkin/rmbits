import sys
import os
import re
import ConfigParser

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from cls import get_clss
from email_msg import *

class emailESPMsg(emailMsg):

    def __init__(self,email_str):

        super(self.__class__, self).__init__(email_str)
        self.flights = []
        self.dows = []
        self.split_history = ''
        self.pool_ids = []
        self.clss = []

        self._parse()

    def _parse(self):

        super(emailESPMsg,self)._parse()
 
    def validate(self):

        # FLIGHTS: HEL-JFK-00005,JFK-HEL-00006
        # DOW: 1,2,3
        # SPLIT_HISTORY: 002
        # POOL_IDS: 1,2,3
        # CLSS: X,Z

        # FIXME: message is indeed multipart
        # FIXME: First element is taken. Should be
        # FIXME: re-written to handle all parts.

        lines = self.contents[0].split('\n')
        lines = [line.strip() for line in lines if line.strip() != '']

        valid = False
        print lines

        while not valid: 

            i = 0
            valid = True
            for line in lines:

                if not re.match('^FLIGHTS:',line) and not re.match('^DOW:',line) and\
                   not re.match('^SPLIT_HISTORY:',line) and not re.match('^POOL_IDS:',line) and\
                   not re.match('^CLSS:',line):

                    valid = False
                    lines.pop(i)
                    if i != 0:
                        lines[i-1] = lines[i-1].strip().strip('=') + line.strip().strip('=')
                    break
                i = i + 1    

        print lines

        if not re.match('^FLIGHTS:(\s)*([A-Z]{3}-[A-Z]{3}-[0-9]{5}(\s)*,(\s)*)*[A-Z]{3}-[A-Z]{3}-[0-9]{5}(\s)*$',lines[0]):

            return [False,lines[0]]

        else:
       
            self.flights = re.findall('[A-Z]{3}-[A-Z]{3}-[0-9]{5}',lines[0].split(':')[1])

        if not re.match('^DOW:(\s)*([1-7](\s)*,(\s)*)*[1-7](\s)*$',lines[1]):

            return [False,lines[1]]

        else:

            self.dows = re.findall('[1-7]',lines[1].split(':')[1])

        if not re.match('^SPLIT_HISTORY:(\s)*[0-9]{3}(\s)*$',lines[2]):

            return [False,lines[2]]

        else:

            self.split_history = re.findall('[0-9]{3}',lines[2].split(':')[1])

        if not re.match('^POOL_IDS:(\s)*([0-5](\s)*,(\s)*)*[0-5](\s)*$',lines[3]):

            return [False,lines[3]]

        else:

            self.pool_ids = re.findall('[0-5]',lines[3].split(':')[1])

        if not re.match('^CLSS:(\s)*(([A-Z](\s)*,(\s)*)*[A-Z])|ALL(\s)*$',lines[4]):

            return [False,lines[4]]

        else:

            if lines[4].split(':')[1].strip() == 'ALL':

                self.clss = get_clss() 

            else:

                self.clss = re.findall('[A-Z]',lines[4].split(':')[1])

        return [True,'']

    def get_flights(self):

        ret = []

        for flight in self.flights:

            tmp = flight.split('-')
            ret.append([tmp[0],tmp[1],tmp[2]])

        return ret

    def get_dows(self):

        return [int(e) for e in self.dows]

    def get_split_history(self):

        # FIXME: one split history is 
        # supported at the moment
        return self.split_history[0]

    def get_pool_ids(self):

        return [int(e) for e in self.pool_ids]

    def get_clss(self):

        return self.clss









