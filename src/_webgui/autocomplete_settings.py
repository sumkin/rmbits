import sys
import os
import ConfigParser

config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))

from autocomplete.views import autocomplete, AutocompleteSettings
from db_connector import dbConnector
from demand_shift.models import ClassUsage

class PlacesAutocomplete(AutocompleteSettings):
    def view(request,term):
        curs = dbConnector.get_ads_curs()
        term = request.GET.get('term',None)  
        q = "(SELECT DISTINCT airport_nm FROM ads_airport WHERE airport_nm LIKE '"+term+"%')\
             UNION ALL\
             (SELECT DISTINCT city FROM ads_airport WHERE city LIKE 'H%')\
             UNION ALL\
             (SELECT DISTINCT region FROM ads_airport where region LIKE 'H%')\
             UNION ALL\
             (SELECT DISTINCT continent FROM ads_airport where continent LIKE 'H%')" 
        curs.execute(q)
        row = curs.fetchone()
        idd = 1
        data = []
        while row is not None:
            data.append(dict(id=idd,value=row[0],label=row[0]))
        return data

#autocomplete.register(ClassUsage.orgn,PlacesAutocomplete)

