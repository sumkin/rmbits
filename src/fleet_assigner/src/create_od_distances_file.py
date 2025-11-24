import pandas as pd

from s3utils import *
from pyairport.airport import Airport

def create_file():
    df = pd.read_csv("s3://ay-emr-job/fleet_assigner/input/airport_allowance.csv")
    res_df = pd.DataFrame(columns=["ap1", "ap2", "dist"])
    airports = list(df["AIRPORT"].unique())
    for i in range(len(airports)):
        for j in range(len(airports)):
            ap1 = airports[i]
            ap2 = airports[j]
            dist = 0
            if ap1 != ap2:
                dist = Airport(ap1).distance(Airport(ap2))
            res_df.loc[len(res_df)] = [ap1, ap2, dist]
    res_df.to_csv("../output/od_distances.csv")
    s3copy("../output/od_distances.csv", "s3://ay-emr-job/fleet_assigner/input/od_distances.csv")

if __name__ == "__main__":
    create_file()


