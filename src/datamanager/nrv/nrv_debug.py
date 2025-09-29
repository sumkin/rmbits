import pandas as pd

from s3utils import *

def test():
    nrv_files = gets3files("ay-emr-job/nrm/nrv/2023/12/11/")
    for nrv_file in nrv_files:
        print(nrv_file)
        df = pd.read_csv("s3://ay-emr-job/" + nrv_file)
        sub_df = df.loc[df["NRV"] < 0.0]
        if sub_df.shape[0] > 0:
            print(sub_df.head(5))
            assert False

if __name__ == "__main__":
    test()


