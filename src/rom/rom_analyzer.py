import pandas as pd


class ROMAnalyzer:


    def __init__(self, dt):
        """
        Constructor. Takes date in the format YYYYMMDD.
        """
        self.dt = dt
        yyyy, mm, dd = dt[:4], dt[4:6], dt[6:8] 

        # Read dataframes.
        self.min_df = pd.read_csv("s3://ay-rmp-home/nrm/rom/{}/{}/rom_min_{}.csv.gz".format(yyyy, mm, self.dt))
        self.max_df = pd.read_csv("s3://ay-rmp-home/nrm/rom/{}/{}/rom_max_{}.csv.gz".format(yyyy, mm, self.dt))
        self.act_df = pd.read_csv("s3://ay-rmp-home/nrm/rom/{}/{}/rom_act_{}.csv.gz".format(yyyy, mm, self.dt))
        self.load_df = pd.read_csv("s3://ay-rmp-home/nrm/rom/{}/{}/rom_load_{}.csv.gz".format(yyyy, mm, self.dt))

        # Aggregate and filter data.
        self.min_df = self.min_df.groupby(['GEO_OD_TS_KEY','POS','FF'], as_index = False).agg({'SOL': 'sum', 'D': 'sum'})
        self.max_df = self.max_df.groupby(['GEO_OD_TS_KEY','POS','FF'], as_index = False).agg({'SOL': 'sum', 'D': 'sum'})
        self.act_df = self.act_df[['GEO_OD_TS_KEY','POS','FF','BKG','REV']]
        self.load_df = self.load_df.groupby(['GEO_OD_TS_KEY','POS','FF'], as_index = False).agg({'SOL': 'sum', 'D': 'sum'})


    def analyze(self):
        """
        Analyzes the departure date
        """
        # Merge maximum and actual data frame.
        self.mdf = self.max_df.merge(self.act_df, how = 'outer',
                                                  left_on = ['GEO_OD_TS_KEY','POS','FF'],
                                                  right_on = ['GEO_OD_TS_KEY','POS','FF'])
        self.mdf['SOL-BKG'] = self.mdf['SOL'] - self.mdf['BKG']
        self.mdf['D-BKG'] = self.mdf['D'] - self.mdf['BKG']
        self.mdf['D'] = self.mdf['D'].fillna(0)
        assert self.mdf[self.mdf['SOL'] - self.mdf['D'] > 0].shape[0] == 0

        print("")

        # Taken more than forecasted.
        print("Taken more than forecasted")
        self.tmtf_df = self.mdf.loc[self.mdf['D-BKG'] < 0]
        print("\t# flows = {}".format(self.tmtf_df.shape[0]))  
        print("\t# bookings = {}".format(abs(self.tmtf_df['D-BKG'].sum()))) 
        print("\trevenue = {}".format(abs(self.tmtf_df['REV'].sum())))
        print("")   

        # Bookings.
        print("Bookings")
        print("\t# flows = {}".format(self.act_df.shape[0]))
        print("\t# bookings = {}".format(self.act_df['BKG'].sum()))
        print("\trevenue = {}".format(self.act_df['REV'].sum()))
        print("")  

        # Taken non-forecasted.
        print("Taken non-forecasted")
        self.tnf_df = self.mdf.loc[(self.mdf['D'] == 0) & (self.mdf['BKG'] > 0)]
        print("\t# flows = {}".format(self.tnf_df.shape[0]))
        print("\t# bookings = {}".format(self.tnf_df['BKG'].sum()))
        print("\trevenue = {}".format(self.tnf_df['REV'].sum()))
        print("")

        # Taken less than optimal.
        print("Taken less than optimal")
        self.tlto_df = self.mdf.loc[self.mdf['SOL-BKG'] > 0]
        print("\t# flows = {}".format(self.tlto_df.shape[0]))
        print("\t# bookings = {}".format(self.tlto_df['SOL-BKG'].sum()))
        print("\trevenue = {}".format(self.tlto_df['REV'].sum()))
        print("")

        # Taken more than optimal.
        print("Taken more than optimal")
        self.tmto_df = self.mdf.loc[self.mdf['SOL-BKG'] < 0]
        print("\t# flows = {}".format(self.tmto_df.shape[0]))
        print("\t# bookings = {}".format(abs(self.tmto_df['SOL-BKG'].sum())))
        print("\trevenue = {}".format(abs(self.tmto_df['REV'].sum())))
        print("")


    def get_tmtf_df(self):
        return self.tmtf_df


    def get_tnf_df(self):  
        return self.tnf_df


    def get_tlto_df(self):
        return self.tlto_df 


    def get_tmto_df(self):
        return self.tmto_df     


if __name__ == "__main__":
    ra = ROMAnalyzer("20210918")
    ra.analyze()