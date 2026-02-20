import pandas as pd 
from datetime import datetime 

from maintenance_reader import MaintenanceReader

class FleetReader:

    def __init__(self, depdates, fleet_fname, cap_fname, maintenance_fname, turnaround_times_df):
        self.depdates = depdates
        self.fleet_fname = fleet_fname
        self.cap_fname = cap_fname
        self.maintenance_fname = maintenance_fname
        self.turnaround_times_df = turnaround_times_df

    def read(self):
        # Read fleet dataframe.
        self.fleet_df = pd.read_csv(self.fleet_fname, sep=",")
        self.fleet_df.columns = ["res_model",
                                 "owner",
                                 "subfleet",
                                 "eff_date",
                                 "dis_date",
                                 "num_aircrafts",
                                 "updated",
                                 "updated_by"]
        self.fleet_df = self.fleet_df.loc[
            (self.fleet_df["owner"] == "AY") |
            (self.fleet_df["owner"] == "N7") |
            (self.fleet_df["owner"] == "IB") |
            (self.fleet_df["owner"] == "JP")
        ]
        self.fleet_df = self.fleet_df.loc[
            (self.fleet_df["subfleet"] != "ERJ") &
            (self.fleet_df["subfleet"] != "A7B") &
            (self.fleet_df["subfleet"] != "33D") &
            (self.fleet_df["subfleet"] != "33U") &
            (self.fleet_df["subfleet"] != "33R")
        ]
        self.fleet_df = self.fleet_df.loc[~self.fleet_df["subfleet"].str.contains("ERR:")]
        self.fleet_df = self.fleet_df[["subfleet", "eff_date", "dis_date", "num_aircrafts"]]
        self.fleet_df["eff_date"] = pd.to_datetime(self.fleet_df["eff_date"], format="%d/%m/%Y")
        self.fleet_df["dis_date"] = pd.to_datetime(self.fleet_df["dis_date"], format="%d/%m/%Y")

        # Filter based on overlap with departure dates.
        min_depdate = datetime.strptime(min(self.depdates), "%Y%m%d")
        max_depdate = datetime.strptime(max(self.depdates), "%Y%m%d")
        self.fleet_df = self.fleet_df[
            self.fleet_df.apply(lambda x: max(x["eff_date"], min_depdate) <= min(x["dis_date"], max_depdate), axis=1)
        ]
        self.fleet_df.columns = ["SUBFLEET", "EFF_DATE", "DIS_DATE", "NUM_AIRCRAFTS"]
        self.fleet_df["EFF_DATE"] = self.fleet_df["EFF_DATE"].astype(str).str.replace("-","")
        self.fleet_df["DIS_DATE"] = self.fleet_df["DIS_DATE"].astype(str).str.replace("-","")

        self.maint_df = MaintenanceReader(self.maintenance_fname, self.depdates[0], self.turnaround_times_df).load()

    def get_fleet_types(self):
        res = list(self.fleet_df["SUBFLEET"].unique())
        return res

    def get_fleet_type2fleet_ids(self):
        res = {}
        fleet_types = self.get_fleet_types()
        for fleet_type in fleet_types:
            df = self.fleet_df[self.fleet_df["SUBFLEET"] == fleet_type]
            res[fleet_type] = [fleet_type + "_" + str(e) for e in list(range(df["NUM_AIRCRAFTS"].iloc[0]))]
        return res

    def get_num_aircrafts(self, ac_type, t0_min, t1_min, _t0, _t1, wetlease_sequences):
        assert _t0 <= _t1
        t0 = datetime.strftime(_t0, "%Y%m%d")
        t1 = datetime.strftime(_t1, "%Y%m%d")
        df = self.fleet_df[self.fleet_df.apply(lambda x: x["EFF_DATE"] <= t0 and t1 <= x["DIS_DATE"], axis=1)]
        res = df[df["SUBFLEET"] == ac_type]["NUM_AIRCRAFTS"].sum()

        mdf = self.maint_df[self.maint_df.apply(lambda x: max(t0_min, x["from_mins"]) < min(t1_min - 1, x["to_mins"]), axis=1)]
        mres = mdf[mdf["actype"] == ac_type].drop_duplicates().shape[0]  # FIXME: drop_duplicates() should be done earlier.
        """
        This is shit.
        froms, tos = [], []
        for k, r in mdf.iterrows():
            froms.append(r["from_mins"])
            tos.append(r["to_mins"])
            if max(froms) > min(tos) and mres == 2: # FIXME: this is special case. Probably should be done more generally.
                # If maintenance blocks do not intersect then substract only one aircraft.
                mres = 1
        """
        wsres = 0
        for sequence in wetlease_sequences:
            ac = sequence[0][20:-1]
            if ac == ac_type:
                wsres += 1
        if res - mres - wsres < 0:
            print("WARNING: get_num_aircrafts(): ac_type = {}, res = {}, mres = {}, wsres = {}".format(ac_type, res, mres, wsres))
        return max(0, res - mres - wsres)

if __name__ == "__main__":
    depdates = ["20220401", "20220402"]
    fname = "s3://ay-emr-job/fleet_assigner/aircraft_inventory.csv"
    cap_file = "s3://ay-emr-job/fleet_assigner/subfleet_capacities.csv"
    maintenance_file = "s3://ay-emr-job/fleet_assigner/december2023/W23_dec_190923.ssim"
    fr = FleetReader(depdates, fname, cap_file, maintenance_file)
    fr.read()
    fleet_types = fr.get_fleet_types()
    fleet_type2fleet_ids = fr.get_fleet_type2fleet_ids()
    print(f"fleet_types = {fleet_types}")
    #print(f"fleet_type2fleet_ids = {fleet_type2fleet_ids}")



