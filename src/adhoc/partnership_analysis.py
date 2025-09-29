import pandas as pd

from s3utils import *

def main():
    # Base case.
    base_df = None
    files = gets3files("s3://ay-emr-job/nrm/partnership_base_cf/2024/03/05/")
    num = 0
    for file in files:
        num += 1
        df = pd.read_csv("s3://ay-emr-job/" + file, low_memory=False)
        df = df[["MP", "D", "LPC_D"]]
        if base_df is None:
            base_df = df
        else:
            base_df = pd.concat([base_df, df])
        if num % 10 == 0:
            print("base: ", df.shape, base_df.shape, "{}/{}".format(num, len(files)))
    base_df["UNC_REV"] = base_df["MP"] * base_df["D"]
    base_df["CONS_REV"] = base_df["MP"] * base_df["LPC_D"]
    print("Base unconstrained demand = {}".format(base_df["D"].sum()))
    print("Base constrained demand = {}".format(base_df["LPC_D"].sum()))
    print("Base unconstrained revenue = {}".format(base_df["UNC_REV"].sum()))
    print("Base constrained revenue = {}".format(base_df["CONS_REV"].sum()))
    print("")
    del base_df

    # Scenario 1.
    sce1_df = None
    files = gets3files("s3://ay-emr-job/nrm/partnership_sce1_cf/2024/03/05/")
    num = 0
    for file in files:
        num += 1
        df = pd.read_csv("s3://ay-emr-job/" + file, low_memory=False)
        df = df[["MP", "D", "LPC_D"]]
        if sce1_df is None:
            sce1_df = df
        else:
            sce1_df = pd.concat([sce1_df, df])
        if num % 10 == 0:
            print("sce1: ", df.shape, sce1_df.shape, "{}/{}".format(num, len(files)))
    sce1_df["UNC_REV"] = sce1_df["MP"] * sce1_df["D"]
    sce1_df["CONS_REV"] = sce1_df["MP"] * sce1_df["LPC_D"]
    print("Scenario 1 unconstrained demand = {}".format(sce1_df["D"].sum()))
    print("Scenario 1 constrained demand = {}".format(sce1_df["LPC_D"].sum()))
    print("Scenario 1 unconstrained revenue = {}".format(sce1_df["UNC_REV"].sum()))
    print("Scenario 1 constrained revenue = {}".format(sce1_df["CONS_REV"].sum()))
    print("")
    del sce1_df

    # Scenario 2.
    sce2_df = None
    files = gets3files("s3://ay-emr-job/nrm/partnership_sce2_cf/2024/03/05/")
    num = 0
    for file in files:
        num += 1
        df = pd.read_csv("s3://ay-emr-job/" + file, low_memory=False)
        df = df[["MP", "D", "LPC_D"]]
        if sce2_df is None:
            sce2_df = df
        else:
            sce2_df = pd.concat([sce2_df, df])
        if num % 10 == 0:
            print("sce2: ", df.shape, sce2_df.shape, "{}/{}".format(num, len(files)))
    sce2_df["UNC_REV"] = sce2_df["MP"] * sce2_df["D"]
    sce2_df["CONS_REV"] = sce2_df["MP"] * sce2_df["LPC_D"]
    print("Scenario 2 unconstrained demand = {}".format(sce2_df["D"].sum()))
    print("Scenario 2 constrained demand = {}".format(sce2_df["LPC_D"].sum()))
    print("Scenario 2 unconstrained revenue = {}".format(sce2_df["UNC_REV"].sum()))
    print("Scenario 2 constrained revenue = {}".format(sce2_df["CONS_REV"].sum()))
    print("")
    del sce2_df

if __name__ == "__main__":
    main()


