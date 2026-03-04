import math
import boto
import pandas as pd
import numpy as np
from tqdm import tqdm

tqdm.pandas()

ARPT_FILE = 's3n://ay-rmp-home/static/ff_airports.csv'
MRKT_FILE = 's3n://ay-rmp-home/static/ff_markets.csv'
FMLS_FILE = 's3n://ay-rmp-home/static/ff_families.csv'


class FFMapper:


    def __init__(self, df):

        # Read CSV files to pandas dataframes.
        self.arpt_df = pd.read_csv(ARPT_FILE, sep=';')
        self.mrkt_df = pd.read_csv(MRKT_FILE, sep=';')
        self.fmls_df = pd.read_csv(FMLS_FILE, sep=';')

        # Replace empty POS with 'WORLD' value.
        self.fmls_df.loc[self.fmls_df['POS'].isnull(), 'POS'] = 'WORLD'

        # Fill airpot -> markets table.
        self.arpt2ffmap = {}
        self.fill_arpt2ffmap()

        # Fill country -> markets table.
        self.cntr2ffmap = {}
        self.fill_cntr2ffmap()

        # Fill orgn,dstn,pos,cls -> ff table.
        self.odpc = {}
        for index, row in tqdm(df.iterrows()):
            self.fill_odpc(row['ORGN'], row['DSTN'], row['POS'], row['CLS'])    


    def get_city_code(self, arpt_code):
        return self.arpt_df.loc[self.arpt_df['CODE'] == arpt_code].\
               CITY_CODE.iloc[0]


    def get_country_code(self, arpt_code):
        return self.arpt_df.loc[self.arpt_df['CODE'] == arpt_code].\
               COUNTRY_CODE.iloc[0]


    def get_region_code_airport(self, arpt_code):
        return self.arpt_df.loc[self.arpt_df['CODE'] == arpt_code].\
               REGION_CODE.iloc[0]

    
    def get_region_code_country(self, country_code):
        return self.arpt_df.loc[self.arpt_df['COUNTRY_CODE'] == country_code].\
               REGION_CODE.iloc[0]


    def get_continent_code_airport(self, arpt_code):
        return self.arpt_df.loc[self.arpt_df['CODE'] == arpt_code].\
               CONTINENT_CODE.iloc[0]


    def get_continent_code_country(self, country_code):
        return self.arpt_df.loc[self.arpt_df['COUNTRY_CODE'] == country_code].\
               REGION_CODE.iloc[0]


    def get_market_codes_airport(self, arpt_code):
        res = []
        city_code = self.get_city_code(arpt_code)
        try:
            l = self.mrkt_df.loc[self.mrkt_df['CITY'] == city_code].MARKET
            for e in l:        
                res.append(e)
        except:
            pass

        country_code = self.get_country_code(arpt_code)
        try:
            l = self.mrkt_df.loc[self.mrkt_df['COUNTRY'] == country_code].MARKET
            for e in l:
                res.append(e)
        except:
            pass

        region_code = self.get_region_code_airport(arpt_code)
        try:
            l = self.mrkt_df.loc[self.mrkt_df['REGION'] == region_code].MARKET
            for e in l:
                res.append(e)
        except:
            pass
        res.append('WORLD')
        res = list(set(res))
        return res


    def get_market_codes_country(self, country_code):
        res = []
        try:
            l = self.mrkt_df.loc[self.mrkt_df['COUNTRY'] == country_code].MARKET
            for e in l:
                res.append(e)
        except:
            pass
        region_code = self.get_region_code_country(country_code)
        try:
            l = self.mrkt_df.loc[self.mrkt_df['REGION'] == country_code].MARKET
            for e in l:
                res.append(e)
        except:
            pass
        res.append('WORLD')
        res = list(set(res))
        return res
       

    def get_ff(self, orgn, dstn, pos, cls):
        k = orgn+dstn+pos+cls
        return self.odpc[k]        
  

    def fill_odpc(self, orgn, dstn, pos, cls):
        #
        # Returns fare family corresponding 
        # to orgn, dstn, pos.
        #
        k = orgn+dstn+pos+cls

        resff = None
        resord = np.inf
        try:
            orgn_mrkts = self.arpt2ffmap[orgn]
        except:
            orgn_mrkts = ['WORLD']
        try:
            dstn_mrkts = self.arpt2ffmap[dstn]
        except:
            dstn_mrkts = ['WORLD']
        try:
            pos_mrkts = self.cntr2ffmap[pos]
        except:
            pos_mrkts = ['WORLD']

        for orgn_mrkt in orgn_mrkts:
            for dstn_mrkt in dstn_mrkts:
                for pos_mrkt in pos_mrkts:
                    ff_df = self.fmls_df.loc[(self.fmls_df['ORIGIN'] == orgn_mrkt) &\
                                             (self.fmls_df['DESTINATION'] == dstn_mrkt) &\
                                             (self.fmls_df['POS'] == pos_mrkt) &\
                                             (self.fmls_df['BOOKING_CLASS'] == cls)]
                    if ff_df.shape[0] == 0:
                        pass
                    elif ff_df.shape[0] == 1:
                        if int(ff_df.ORDER) < resord:
                            resff = ff_df.FARE_FAMILY.iloc[0]
                            resord = int(ff_df.ORDER)
                    else:
                        print ff_df
                        assert False
                   
                    # Try viceversa also.
                    ff_df = self.fmls_df.loc[(self.fmls_df['ORIGIN'] == dstn_mrkt) &\
                                             (self.fmls_df['DESTINATION'] == orgn_mrkt) &\
                                             (self.fmls_df['POS'] == pos_mrkt) &\
                                             (self.fmls_df['BOOKING_CLASS'] == cls) &\
                                             (self.fmls_df['VICEVERSA'] == 1)]
                    if ff_df.shape[0] == 0:
                        pass
                    elif ff_df.shape[0] == 1:
                        if int(ff_df.ORDER) < resord:
                            resff = ff_df.FARE_FAMILY.iloc[0]
                            resord = int(ff_df.ORDER)
                    else:
                        print ff_df
                        assert False

        if resff is None:
            assert False
        self.odpc[k] = resff
        return resff 


    def fill_arpt2ffmap(self):
        # Fill airport -> markets table.
        for arpt_code in self.arpt_df.CODE.unique():
            if isinstance(arpt_code, float):
                continue
            mrkts = self.get_market_codes_airport(arpt_code)
            self.arpt2ffmap[arpt_code] = mrkts


    def fill_cntr2ffmap(self):
        # Fill country -> markets table.
        for cntr_code in self.arpt_df.COUNTRY_CODE.unique():
            if isinstance(cntr_code, float):
                continue
            mrkts = self.get_market_codes_country(cntr_code)
            self.cntr2ffmap[cntr_code] = mrkts


if __name__ == '__main__':
    #s3fname = 's3n://ay-rmp-home/nrm/baf/2018/05/AV_OD_20180523.csv.gz'
    #print 'Reading availability...'
    #df = pd.read_csv(s3fname)
    #df2 = pd.melt(df, id_vars=['ORGN','DSTN','VIA','CC','FLTNUM',\
    #                           'OD_DEPT_DATE','OD_DEPT_DOW','SEG_DEPT_DATE',\
    #                           'POS','POSTYPE','LOCJ','LOCIJ','LOCY','LOCIY',\
    #                           'LOCJ_WOSC','LOCIJ_WOSC','LOCY_WOSC','LOCIY_WOSC',\
    #                           'SRC_DATE'], var_name='CLS', value_name='AVAIL')
    #del df
    #df3 = df2[['ORGN','DSTN','POS','CLS']]
    #df3 = df3.drop_duplicates()
    #del df2
    df3 = None
    ffm = FFMapper(df3)
    '''
    for index, row in df3.iterrows():
        print row['ORGN'],row['DSTN'],row['POS'],row['CLS'],\
              ffm.get_ff(row['ORGN'],row['DSTN'],row['POS'],row['CLS'])
    '''

