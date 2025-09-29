import sys
import os
import re
from datetime import date
import ConfigParser

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from email_msg import *

class emailDBCMsg(emailMsg):

    def __init__(self,email_str):

        super(self.__class__,self).__init__(email_str)
        self.flight = ''
        self.dfrom = None
        self.dto = None

        self._parse()

    def _parse(self):

        super(emailDBCMsg,self)._parse()

    def validate(self):

        # FLIGHT: HEL-JFK-00005
        # DATE_FROM: 2010-10-01
        # DATE_TO: 2011-10-01

        # FIXME: message is indeed multipart
        # First element is taken. Should be
        # re-written to handle all parts.

        lines = self.contents[0].split('\n')
        lines = [line.strip() for line in lines if line.strip() != '']

        if not re.match('^FLIGHT:(\s)*[A-Z]{3}-[A-Z]{3}-[0-9]{5}(\s)*$',lines[0]):
            return [False,lines[0]]
        else:
            self.flight = re.findall('[A-Z]{3}-[A-Z]{3}-[0-9]{5}',lines[0].split(':')[1])[0]

        if not re.match('^DATE_FROM:(\s)*[0-9]{4}-[0-9]{2}-[0-9]{2}(\s)*$',lines[1]):
            return [False,lines[1]]
        else:
            dfrom_str = re.findall('[0-9]{4}-[0-9]{2}-[0-9]{2}',lines[1].split(':')[1])
            dfrom = dfrom_str[0].split('-')
            self.dfrom = date(int(dfrom[0]),int(dfrom[1]),int(dfrom[2]))

        if not re.match('^DATE_TO:(\s)*[0-9]{4}-[0-9]{2}-[0-9]{2}(\s)*$',lines[2]):
            return [False,lines[2]] 
        else:
            dto_str = re.findall('[0-9]{4}-[0-9]{2}-[0-9]{2}',lines[2].split(':')[1])
            dto = dto_str[0].split('-')
            self.dto = date(int(dto[0]),int(dto[1]),int(dto[2]))

        return [True,'']

    def get_flight(self):
        tmp = self.flight.split('-')
        return [tmp[0],tmp[1],tmp[2]]

    def get_dfrom(self):
        return self.dfrom

    def get_dto(self):
        return self.dto


 




