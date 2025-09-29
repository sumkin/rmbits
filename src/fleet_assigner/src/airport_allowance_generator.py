import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class AirportAllowanceGenerator:

    def __init__(self):
        self.acv2at = {}
        acv_df = pd.read_csv("s3://ay-emr-job/fleet_assigner/december2023/acv_subfleet.csv", sep=";")
        for k, r in acv_df.iterrows():
            self.acv2at[r["acv"].strip()] = r["subfleet"].strip()

    def generate(self):
        dfs = []

        dt = datetime.now()
        num = 0
        while num < 365:
            print(dt)
            year = str(dt.year)
            month = str(dt.month).zfill(2)
            day = str(dt.day).zfill(2)
            dt_s = dt.strftime("%Y%m%d")
            try:
                df = pd.read_csv("s3://ay-emr-job/nrm/bif/{}/{}/INV_{}.csv.gz".format(year, month, dt_s),
                                 low_memory=False)
                df = df[
                    df["CC"] == "AY"
                ][["ORGN", "AIRCRAFT_TYPE"]].drop_duplicates()
                dfs.append(df)
            except FileNotFoundError:
                pass

            dt = dt - timedelta(days=1)
            num += 1

        df = pd.concat(dfs, axis=0)
        df = df.drop_duplicates()

        def acv2subfleet(acv):
            if acv in self.acv2at.keys():
                return self.acv2at[acv]
            else:
                return np.nan

        df["SUBFLEET"] = df["AIRCRAFT_TYPE"].apply(acv2subfleet)
        df = df[["ORGN", "SUBFLEET"]]
        df = df[df["ORGN"] != "HEL"]
        df.columns = ["AIRPORT", "AT"]
        df = df.dropna()

        # If there is airport with 32B then add the same airport with 32G and 32L.
        airports_32B = df[df["AT"] == "32B"]["AIRPORT"].unique()
        df32G = pd.DataFrame({"AIRPORT": airports_32B, "AT": ["32G"] * len(airports_32B)})
        df32L = pd.DataFrame({"AIRPORT": airports_32B, "AT": ["32L"] * len(airports_32B)})
        df = pd.concat([df, df32G, df32L], axis=0)
        df = df.dropna()

        df.to_csv("../output/airport_allowance.csv", index=False)

if __name__ == "__main__":
    aag = AirportAllowanceGenerator()
    aag.generate()

