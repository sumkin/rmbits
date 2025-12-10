import pandas as pd 
from datetime import datetime 

class ASFleetReader:

    def __init__(self, depdates, fleet_fname):
        self.depdates = depdates
        self.fleet_fname = fleet_fname

    def read(self):
        # Read fleet dataframe.
        self.fleet_df = pd.read_csv(self.fleet_fname, sep=";")
        self.fleet_df.columns = ["aircraft_type",
                                 "park",
                                 "dplg",
                                 "reserve",
                                 "MAX",
                                 "schedule",
                                 "free_aircraft"]

    def get_fleet_types(self):
        res = list(self.fleet_df["aircraft_type"].unique())
        return res

    def get_fleet_type2fleet_ids(self):
        res = {}
        fleet_types = self.get_fleet_types()
        for fleet_type in fleet_types:
            df = self.fleet_df[self.fleet_df["aircraft_type"] == fleet_type]
            res[fleet_type] = [fleet_type + "_" + str(e) for e in list(range(df["schedule"].iloc[0]))]
        return res

    def get_num_aircrafts(self, ac_type, _t0, _t1):
        assert _t0 <= _t1
        res = df[df["aircraft_type"] == ac_type]["schedule"].sum()
        return res

if __name__ == "__main__":
    depdates = ["20220401", "20220402"]
    fleet_fname = "/home/sumkin/rmbits/src/fleet_assigner/as_data/aircraft_inventory.csv"
    asfr = ASFleetReader(depdates, fleet_fname)
    asfr.read()
    fleet_types = asfr.get_fleet_types()
    fleet_type2fleet_ids = asfr.get_fleet_type2fleet_ids()
    print(f"fleet_types = {fleet_types}")
    print(f"fleet_type2fleet_ids = {fleet_type2fleet_ids}")



