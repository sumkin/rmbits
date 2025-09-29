import copy
import pandas as pd
from datetime import datetime, timedelta

from defs import *

class DutiesBuilder:

    def __init__(
        self,
        depdates,
        next_depdate,
        legs,
        fleet_types,
        output_writer
    ):
        self.depdates = depdates 
        self.next_depdate = next_depdate
        self.legs = legs 
        self.fleet_types = fleet_types
        self.output_writer = output_writer
        self.duties = []
        self.leg2duty = {}
        self.duty2startend = []
        self.duty2at = {}

        # Create aircraft configuration to aircraft type mapping.
        self.acv2at = {}
        acv_df = pd.read_csv("s3://ay-emr-job/fleet_assigner/december2023/acv_subfleet.csv", sep=";")
        for k, r in acv_df.iterrows():
            self.acv2at[r["acv"].strip()] = r["subfleet"].strip()

        # Fill dataframe.
        leg_id = 0
        self.df = pd.DataFrame(columns=["LEG_ID", "ORGN", "DSTN", "FLTNUM", "DEPDT", "ARRDT",
                                        "DEPTM", "ARRTM", "AIRCRAFT_TYPE", "PROCESSED"])
        for orgn, dstn, fltnum, depdt, arrdt, deptm, arrtm, at in self.legs:
            self.df.loc[self.df.shape[0]] = [leg_id, orgn, dstn, fltnum, depdt, arrdt, deptm, arrtm, at, False]
            leg_id += 1

    def pair_legs_with_hel_orgn(self):
        for _, row in self.df[(self.df["ORGN"] == "HEL") & (~self.df["PROCESSED"])].iterrows():
            leg_id = row["LEG_ID"]
            dstn = row["DSTN"]
            if dstn == "KOK":
                # These are multi-leg flights.
                continue 
            fltnum = row["FLTNUM"]
            arrtm = row["ARRTM"]
            ret_df = self.df[(self.df["ORGN"] == dstn) &
                             (self.df["DSTN"] == "HEL") &
                             (self.df["DEPTM"] >= arrtm + MIN_GROUND_TIME_MINS) &
                             (self.df["DEPTM"] <= arrtm + MAX_GROUND_TIME_MINS) &
                             (abs(self.df["FLTNUM"] - fltnum) == 1)
                            ].sort_values(by=["DEPTM"])
            if ret_df.shape[0] == 0:
                continue
            ret_row = ret_df.iloc[0]
            ret_leg_id = ret_row["LEG_ID"]

            if self.legs[leg_id][3] == self.next_depdate:
                continue

            # Fill structures.
            acv = self.legs[leg_id][7].strip()
            at = self.acv2at[acv]
            if at not in self.fleet_types:
                print("WARNING: leg {} is skipped, because at = {}".format(self.legs[leg_id], at))
                continue
             
            duty_id = len(self.duties)
            self.duties.append([leg_id, ret_leg_id])
            self.leg2duty[leg_id] = duty_id 
            self.leg2duty[ret_leg_id] = duty_id
            duty_start = min(self.legs[leg_id][5], self.legs[leg_id][6], self.legs[ret_leg_id][5], self.legs[ret_leg_id][6])
            duty_end = max(self.legs[leg_id][5], self.legs[leg_id][6], self.legs[ret_leg_id][5], self.legs[ret_leg_id][6])
            self.duty2startend.append([duty_start, duty_end])
            self.duty2at[len(self.duties) - 1] = at

            # Marks legs processed.
            self.df.loc[self.df["LEG_ID"] == leg_id, "PROCESSED"] = True 
            self.df.loc[self.df["LEG_ID"] == ret_leg_id, "PROCESSED"] = True

    def process_3legs_duties(self):
        """
        Process duties consisting of 3 legs.
        """
        df = self.df[~self.df["PROCESSED"]]
        # Find legs where both origin and destination are not HEL.
        for _, r in df[(df["ORGN"] != "HEL") & (df["DSTN"] != "HEL")].iterrows():
            
            leg_id_1 = r["LEG_ID"]

            prev_depdt = datetime.strptime(r["DEPDT"], "%Y%m%d") - timedelta(days = 1)
            prev_depdt = int(datetime.strftime(prev_depdt, "%Y%m%d"))

            next_depdt = datetime.strptime(r["DEPDT"], "%Y%m%d") + timedelta(days = 1)
            next_depdt = int(datetime.strftime(next_depdt, "%Y%m%d"))

            # From HEL.
            sub_df = df[
                (df["ORGN"] == "HEL") & 
                (df["DSTN"] == r["ORGN"]) & 
                (df["FLTNUM"] == r["FLTNUM"]) &
                ((df["DEPDT"] == r["DEPDT"]) | (df["DEPDT"] == prev_depdt))
            ].sort_values(by="DEPDT", ascending=False)
            if sub_df.shape[0] > 0:
                from_r = sub_df.iloc[0]
            else:
                continue
            leg_id_2 = from_r["LEG_ID"]

            # To HEL. 
            sub_df = df[
                (df["ORGN"] == r["DSTN"]) &
                (df["DSTN"] == "HEL") &
                (df["FLTNUM"] == r["FLTNUM"]) &
                ((df["DEPDT"] == r["DEPDT"]) | (df["DEPDT"] == next_depdt))
            ].sort_values(by="DEPDT", ascending=False)
            if sub_df.shape[0] > 0:
                to_r = sub_df.iloc[0]
            else:
                continue
            leg_id_3 = to_r["LEG_ID"]

            if self.legs[leg_id_3][3] == self.next_depdate:
                continue

            # Fill structures.
            duty_id = len(self.duties)
            self.duties.append([leg_id_1, leg_id_2, leg_id_3])
            self.leg2duty[leg_id_1] = duty_id 
            self.leg2duty[leg_id_2] = duty_id
            self.leg2duty[leg_id_3] = duty_id
            duty_start = min(
                self.legs[leg_id_1][5], self.legs[leg_id_1][6], 
                self.legs[leg_id_2][5], self.legs[leg_id_2][6],
                self.legs[leg_id_3][5], self.legs[leg_id_3][6]
            )
            duty_end = max(
                self.legs[leg_id_1][5], self.legs[leg_id_1][6], 
                self.legs[leg_id_2][5], self.legs[leg_id_2][6],
                self.legs[leg_id_3][5], self.legs[leg_id_3][6]
            )
            self.duty2startend.append([duty_start, duty_end])
            acv = self.legs[leg_id_1][7].strip()
            assert acv == self.legs[leg_id_2][7]
            assert acv == self.legs[leg_id_3][7]
            at = self.acv2at[acv]
            self.duty2at[len(self.duties) - 1] = at

            # Marks legs processed.
            self.df.loc[self.df["LEG_ID"] == leg_id_1, "PROCESSED"] = True 
            self.df.loc[self.df["LEG_ID"] == leg_id_2, "PROCESSED"] = True
            self.df.loc[self.df["LEG_ID"] == leg_id_3, "PROCESSED"] = True

    def process_4legs_duties(self):
        """
        Process duties consisting of 4 legs.
        """
        df = self.df[~self.df["PROCESSED"]]

        # Find legs where both origin and destination are not HEL.
        for _, r in df[(df["ORGN"] != "HEL") & (df["DSTN"] != "HEL")].sort_values(by="DEPDT").iterrows():
            leg_id_1 = r["LEG_ID"]

            # Find flight with the same flight number.
            sub_df = df[
                (df["FLTNUM"] == r["FLTNUM"]) &
                (abs(df["DEPTM"] - r["DEPTM"]) <= 600) &
                (df["LEG_ID"] != r["LEG_ID"])
            ]
            if sub_df.shape[0] > 0:
                from_r = sub_df.iloc[0]
            else:
                continue
            leg_id_2 = from_r["LEG_ID"]

            if self.legs[leg_id_2][1] == "HEL":
                if self.legs[leg_id_2][3] == self.next_depdate:
                    continue

                # This is pair to HEL. Find flights from HEL.
                sub_df = df[
                    (abs(df["FLTNUM"] - r["FLTNUM"]) == 1) & 
                    (abs(df["DEPTM"] - r["DEPTM"]) < 600)
                ]
                if sub_df.shape[0] == 2:
                    r1 = sub_df.iloc[0]
                    r2 = sub_df.iloc[1]
                    leg_id_3 = r1["LEG_ID"]
                    leg_id_4 = r2["LEG_ID"]
                else:
                    continue 
            else:
                # This is pair from HEL. Find flights to HEL.
                sub_df = df[
                    (abs(df["FLTNUM"] - r["FLTNUM"]) == 1) &
                    (abs(df["DEPTM"] - r["DEPTM"]) < 600)
                ]
                if sub_df.shape[0] == 2:
                    r1 = sub_df.iloc[0]
                    r2 = sub_df.iloc[1]
                    leg_id_3 = r1["LEG_ID"]
                    leg_id_4 = r2["LEG_ID"]
                else:
                    continue

            # Fill structures.
            duty_id = len(self.duties)

            self.duties.append([leg_id_1, leg_id_2, leg_id_3, leg_id_4])
            self.leg2duty[leg_id_1] = duty_id 
            self.leg2duty[leg_id_2] = duty_id
            self.leg2duty[leg_id_3] = duty_id
            self.leg2duty[leg_id_4] = duty_id
            duty_start = min(
                self.legs[leg_id_1][5], self.legs[leg_id_1][6], 
                self.legs[leg_id_2][5], self.legs[leg_id_2][6],
                self.legs[leg_id_3][5], self.legs[leg_id_3][6],
                self.legs[leg_id_4][5], self.legs[leg_id_4][6]
            )
            duty_end = max(
                self.legs[leg_id_1][5], self.legs[leg_id_1][6], 
                self.legs[leg_id_2][5], self.legs[leg_id_2][6],
                self.legs[leg_id_3][5], self.legs[leg_id_3][6],
                self.legs[leg_id_4][5], self.legs[leg_id_4][6]
            )
            self.duty2startend.append([duty_start, duty_end])
            acv = self.legs[leg_id_1][7].strip()
            at = self.acv2at[acv]
            self.duty2at[len(self.duties) - 1] = at

            # Marks legs processed.
            self.df.loc[self.df["LEG_ID"] == leg_id_1, "PROCESSED"] = True 
            self.df.loc[self.df["LEG_ID"] == leg_id_2, "PROCESSED"] = True
            self.df.loc[self.df["LEG_ID"] == leg_id_3, "PROCESSED"] = True
            self.df.loc[self.df["LEG_ID"] == leg_id_4, "PROCESSED"] = True

    def build(self, with_write_standalone=False):

        self.pair_legs_with_hel_orgn()
        self.process_3legs_duties()
        self.process_4legs_duties()
        standalone = []
        for _, r in self.df[~self.df["PROCESSED"]].iterrows():
            standalone.append(r["LEG_ID"])

        # Sort standalone legs before printing.
        standalone = sorted(standalone, key=lambda k: str(self.legs[k][3]) + str(self.legs[k][5]))

        # Write legs to Excel.
        leg_data = {
            "ORGN": [],
            "DSTN": [],
            "FLTNUM": [],
            "DEPDATE": [],
            "ARRDATE": [],
            "DEPTM": [],
            "ARRTM": [],
            "ACTYPE": []
        }
        for leg in self.legs:
            orgn, dstn, fltnum, depdate, arrdate, deptm, arrtm, actype = leg
            leg_data["ORGN"].append(orgn)
            leg_data["DSTN"].append(dstn)
            leg_data["FLTNUM"].append(fltnum)
            leg_data["DEPDATE"].append(depdate)
            leg_data["ARRDATE"].append(arrdate)
            leg_data["DEPTM"].append(deptm)
            leg_data["ARRTM"].append(arrtm)
            leg_data["ACTYPE"].append(actype)
        self.leg_df = pd.DataFrame(leg_data)
        self.output_writer.write_leg_df(self.leg_df)

        if with_write_standalone:
            # Write standalone legs to Excel.
            standalone_data = {
                "ORGN": [],
                "DSTN": [],
                "FLTNUM": [],
                "DEPDATE": [],
                "ARRDATE": [],
                "DEPTM": [],
                "ARRTM": [],
                "ACTYPE": []
            }
            for leg_id in standalone:
                orgn, dstn, fltnum, depdate, arrdate, deptm, arrtm, actype = self.legs[leg_id]
                standalone_data["ORGN"].append(orgn)
                standalone_data["DSTN"].append(dstn)
                standalone_data["FLTNUM"].append(fltnum)
                standalone_data["DEPDATE"].append(depdate)
                standalone_data["ARRDATE"].append(arrdate)
                standalone_data["DEPTM"].append(deptm)
                standalone_data["ARRTM"].append(arrtm)
                standalone_data["ACTYPE"].append(actype)
            self.standalone_df = pd.DataFrame(standalone_data)
            self.output_writer.write_standalone_df(self.standalone_df)

        # Write duties to Excel.
        duty_2legs_data = {
            "AIRPORT1": [],
            "AIRPORT2": [],
            "AIRPORT3": [],
            "FLTNUM1": [],
            "FLTNUM2": [],
            "DEPDATE1": [],
            "DEPTM1": [],
            "ARRDATE1": [],
            "ARRTM1": [],
            "DEPDATE2": [],
            "DEPTM2": [],
            "ARRDATE2": [],
            "ARRTM2": [],
            "DUTY_START": [],
            "DUTY_END": [],
            "ACTYPE": [],
            "GROUND_TIME": []
        }
        duty_3legs_data = {
            "AIRPORT1": [],
            "AIRPORT2": [],
            "AIRPORT3": [],
            "AIRPORT4": [],
            "FLTNUM1": [],
            "FLTNUM2": [],
            "FLTNUM3": [],
            "DEPDATE1": [],
            "DEPTM1": [],
            "ARRDATE1": [],
            "ARRTM1": [],
            "DEPDATE2": [],
            "DEPTM2": [],
            "ARRDATE2": [],
            "ARRTM2": [],
            "DEPDATE3": [],
            "DEPTM3": [],
            "ARRDATE3": [],
            "ARRTM3": [],
            "DUTY_START": [],
            "DUTY_END": [],
            "ACTYPE": [],
            "GROUND_TIME1": [],
            "GROUND_TIME2": []
        }
        duty_4legs_data = {
            "AIRPORT1": [],
            "AIRPORT2": [],
            "AIRPORT3": [],
            "AIRPORT4": [],
            "AIRPORT5": [],
            "FLTNUM1": [],
            "FLTNUM2": [],
            "FLTNUM3": [],
            "FLTNUM4": [],
            "DEPDATE1": [],
            "DEPTM1": [],
            "ARRDATE1": [],
            "ARRTM1": [],
            "DEPDATE2": [],
            "DEPTM2": [],
            "ARRDATE2": [],
            "ARRTM2": [],
            "DEPDATE3": [],
            "DEPTM3": [],
            "ARRDATE3": [],
            "ARRTM3": [],
            "DEPDATE4": [],
            "DEPTM4": [],
            "ARRDATE4": [],
            "ARRTM4": [],
            "DUTY_START": [],
            "DUTY_END": [],
            "ACTYPE": [],
            "GROUND_TIME1": [],
            "GROUND_TIME2": [],
            "GROUND_TIME3": []
        }
        for duty_id in range(len(self.duties)):
            legs = self.duties[duty_id]
            actype = self.duty2at[duty_id]
            duty_start = self.duty2startend[duty_id][0]
            duty_end = self.duty2startend[duty_id][1]
            if len(legs) == 2:
                orgn1, dstn1, fltnum1, depdate1, arrdate1, deptm1, arrtm1, actype1 = self.legs[legs[0]]
                orgn2, dstn2, fltnum2, depdate2, arrdate2, deptm2, arrtm2, actype2 = self.legs[legs[1]]
                duty_2legs_data["AIRPORT1"].append(orgn1)
                duty_2legs_data["AIRPORT2"].append(dstn1)
                duty_2legs_data["AIRPORT3"].append(dstn2)
                duty_2legs_data["FLTNUM1"].append(fltnum1)
                duty_2legs_data["FLTNUM2"].append(fltnum2)
                duty_2legs_data["DEPDATE1"].append(depdate1)
                duty_2legs_data["DEPTM1"].append(deptm1)
                duty_2legs_data["ARRDATE1"].append(arrdate1)
                duty_2legs_data["ARRTM1"].append(arrtm1)
                duty_2legs_data["DEPDATE2"].append(depdate2)
                duty_2legs_data["DEPTM2"].append(deptm2)
                duty_2legs_data["ARRDATE2"].append(arrdate2)
                duty_2legs_data["ARRTM2"].append(arrtm2)
                duty_2legs_data["DUTY_START"].append(duty_start)
                duty_2legs_data["DUTY_END"].append(duty_end)
                duty_2legs_data["ACTYPE"].append(actype)
                duty_2legs_data["GROUND_TIME"].append(int(deptm2) - int(arrtm1))
            elif len(legs) == 3:
                orgn1, dstn1, fltnum1, depdate1, arrdate1, deptm1, arrtm1, actype1 = self.legs[legs[0]]
                orgn2, dstn2, fltnum2, depdate2, arrdate2, deptm2, arrtm2, actype2 = self.legs[legs[1]]
                orgn3, dstn3, fltnum3, depdate3, arrdate3, deptm3, arrtm3, actype3 = self.legs[legs[2]]
                duty_3legs_data["AIRPORT1"].append(orgn1)
                duty_3legs_data["AIRPORT2"].append(dstn1)
                duty_3legs_data["AIRPORT3"].append(dstn2)
                duty_3legs_data["AIRPORT4"].append(dstn3)
                duty_3legs_data["FLTNUM1"].append(fltnum1)
                duty_3legs_data["FLTNUM2"].append(fltnum2)
                duty_3legs_data["FLTNUM3"].append(fltnum3)
                duty_3legs_data["DEPDATE1"].append(depdate1)
                duty_3legs_data["DEPTM1"].append(deptm1)
                duty_3legs_data["ARRDATE1"].append(arrdate1)
                duty_3legs_data["ARRTM1"].append(arrtm1)
                duty_3legs_data["DEPDATE2"].append(depdate2)
                duty_3legs_data["DEPTM2"].append(deptm2)
                duty_3legs_data["ARRDATE2"].append(arrdate2)
                duty_3legs_data["ARRTM2"].append(arrtm2)
                duty_3legs_data["DEPDATE3"].append(depdate3)
                duty_3legs_data["DEPTM3"].append(deptm3)
                duty_3legs_data["ARRDATE3"].append(arrdate3)
                duty_3legs_data["ARRTM3"].append(arrtm3)
                duty_3legs_data["DUTY_START"].append(duty_start)
                duty_3legs_data["DUTY_END"].append(duty_end)
                duty_3legs_data["ACTYPE"].append(actype)
                duty_3legs_data["GROUND_TIME1"].append(int(deptm2) - int(arrtm1))
                duty_3legs_data["GROUND_TIME2"].append(int(deptm3) - int(arrtm2))
            elif len(legs) == 4:
                orgn1, dstn1, fltnum1, depdate1, arrdate1, deptm1, arrtm1, actype1 = self.legs[legs[0]]
                orgn2, dstn2, fltnum2, depdate2, arrdate2, deptm2, arrtm2, actype2 = self.legs[legs[1]]
                orgn3, dstn3, fltnum3, depdate3, arrdate3, deptm3, arrtm3, actype3 = self.legs[legs[2]]
                orgn4, dstn4, fltnum4, depdate4, arrdate4, deptm4, arrtm4, actype4 = self.legs[legs[3]]
                duty_4legs_data["AIRPORT1"].append(orgn1)
                duty_4legs_data["AIRPORT2"].append(dstn1)
                duty_4legs_data["AIRPORT3"].append(dstn2)
                duty_4legs_data["AIRPORT4"].append(dstn3)
                duty_4legs_data["AIRPORT5"].append(dstn4)
                duty_4legs_data["FLTNUM1"].append(fltnum1)
                duty_4legs_data["FLTNUM2"].append(fltnum2)
                duty_4legs_data["FLTNUM3"].append(fltnum3)
                duty_4legs_data["FLTNUM4"].append(fltnum4)
                duty_4legs_data["DEPDATE1"].append(depdate1)
                duty_4legs_data["DEPTM1"].append(deptm1)
                duty_4legs_data["ARRDATE1"].append(arrdate1)
                duty_4legs_data["ARRTM1"].append(arrtm1)
                duty_4legs_data["DEPDATE2"].append(depdate2)
                duty_4legs_data["DEPTM2"].append(deptm2)
                duty_4legs_data["ARRDATE2"].append(arrdate2)
                duty_4legs_data["ARRTM2"].append(arrtm2)
                duty_4legs_data["DEPDATE3"].append(depdate3)
                duty_4legs_data["DEPTM3"].append(deptm3)
                duty_4legs_data["ARRDATE3"].append(arrdate3)
                duty_4legs_data["ARRTM3"].append(arrtm3)
                duty_4legs_data["DEPDATE4"].append(depdate4)
                duty_4legs_data["DEPTM4"].append(deptm4)
                duty_4legs_data["ARRDATE4"].append(arrdate4)
                duty_4legs_data["ARRTM4"].append(arrtm4)
                duty_4legs_data["DUTY_START"].append(duty_start)
                duty_4legs_data["DUTY_END"].append(duty_end)
                duty_4legs_data["ACTYPE"].append(actype)
                duty_4legs_data["GROUND_TIME1"].append(int(deptm2) - int(arrtm1))
                duty_4legs_data["GROUND_TIME2"].append(int(deptm3) - int(arrtm2))
                duty_4legs_data["GROUND_TIME3"].append(int(deptm4) - int(arrtm3))
            else:
                assert False
        duty_2legs_df = pd.DataFrame(duty_2legs_data)
        duty_3legs_df = pd.DataFrame(duty_3legs_data)
        duty_4legs_df = pd.DataFrame(duty_4legs_data)
        self.output_writer.write_duties_df(duty_2legs_df, duty_3legs_df, duty_4legs_df)

        return self.duties, self.duty2startend, standalone, self.leg2duty, self.duty2at



