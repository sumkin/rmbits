import random
import pandas as pd
from time import sleep


class AirportS3:

    def __init__(self):
        for i in range(5):
            try:
                self.df = pd.read_csv('s3://ay-emr-job/static/ff_airports.csv', sep=';')
                break
            except:
                sleep(random.randint(0,5))
     
        self.df['CODE'] = self.df['CODE'].astype('category')
        self.df.set_index('CODE')
        # Caches for country, region.
        self.m = {}
        self.aym = {}

        # Cache for region.
        self.r = {}


    def get_cr(self, ap):
        try:
            return self.m[ap]
        except:
            pass
        dfres = self.df.loc[self.df['CODE'] == ap]
        res =  dfres['COUNTRY_CODE'].iloc[0], dfres['REGION_CODE'].iloc[0]
        self.m[ap] = res
        return res


    def get_aycr(self, ap):
        try:
            return self.aym[ap]
        except:
            pass
        dfres = self.df.loc[self.df['CODE'] == ap]

        region, country, ayregion = '', '', ''
        try:         
            country = dfres['COUNTRY_CODE'].iloc[0]
            region = dfres['REGION_CODE'].iloc[0]
            ayregion = self.get_ayregion(region)
        except:
            print('ap = ', ap)
            print('region = ', region)
        self.aym[ap] = country, ayregion
        return country, ayregion


    def get_ayr(self, cntr):
        try:
            return self.r[cntr]
        except:
            pass
        dfres = self.df.loc[self.df['COUNTRY_CODE'] == cntr]
        try:
            region = dfres['REGION_CODE'].iloc[0]
        except:
            region = ''
        ayregion = self.get_ayregion(region)
        self.r[cntr] = ayregion
        return ayregion


    def get_ayregion(self, region):
        if region == 'EUROP':
            ayregion = 'EUROPE'
        elif region == 'SEASI':
            ayregion = 'ASIA'
        elif region == 'EEURO':
            ayregion = 'EUROPE'
        elif region == 'ASIA':
            ayregion = 'ASIA'
        elif region == 'MEAST':
            ayregion = 'MEAST'
        elif region == 'CARIB':
            ayregion = 'NAMER'
        elif region == 'NAMER':
            ayregion = 'NAMER'
        elif region == 'EURAS':
            ayregion = 'EUROPE'
        elif region == 'IOCEA':
            ayregion = 'ASIA'
        elif region == 'AUSTL':
            ayregion = 'AUSTL'
        elif region == 'AFRIC':
            ayregion = 'AFRIC'
        elif region == 'PACIF':
            ayregion = 'PACIF'
        elif region == 'SAMER':
            ayregion = 'SAMER'
        elif region == 'CAMER':
            ayregion = 'CAMER'
        else:
            ayregion = ''
            print('region = ', region)
        return ayregion


if __name__ == "__main__":
    ap = AirportS3()
    print(ap.get_aycr('TLL'))




