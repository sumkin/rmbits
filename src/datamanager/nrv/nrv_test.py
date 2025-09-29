import pandas as pd
from datetime import datetime, timedelta

from defs import *

def main():
    dt = datetime(2024, 10, 14)
    while True:
        year = str(dt.year).zfill(2)
        month = str(dt.month).zfill(2)
        day = str(dt.day).zfill(2)
        fname = "s3://ay-emr-job/nrm/nrv_exp/2024/10/14/nrv_exp_20241014_{}.csv.gz".format(dt.strftime("%Y%m%d"))
        try:
            df = pd.read_csv(fname)
            nrv_min = df["NRV"].min()
            nrv_max = df["NRV"].max()
            assert nrv_min >= -EPS and nrv_max < 10e6
        except:
            break
        print(dt)
        dt = dt + timedelta(days=1)

if __name__ == "__main__":
    main()

