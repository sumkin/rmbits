import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from utils import time_now
from as_fleet_reader import ASFleetReader

class ASDataReader:

    def __init__(
        self,
        depdates,
        inv_file,
        costs_file,
        fleet_file,
        cap_file,
        maintenance_file,
        leg_pairings_file,
        turnaround_times_file
    ):
        self.depdates = depdates
        self.inv_file = inv_file
        self.costs_file = costs_file
        self.fleet_file = fleet_file
        self.cap_file = cap_file
        self.turnaround_times_file = turnaround_times_file

        self.legs = []
        self.orgn_dstn_fltnum_depdt2leg_id = {}  # Map to speed-up querying for leg id.
        self.leg_id2duty_id = {}
        self.duty_id2leg_id = {}

    def read(self):
        print(time_now() + " Loading inventory dataframe...")
        self.load_inv_df()

        print(time_now() + " Loading costs dataframe...")
        self.load_costs_df()

        print(time_now() + " Loading fleet dataframe...")
        self.load_fleet_df()

        print(time_now() + " Loading turnaround times..")
        self.load_turnaround_times()

        print(time_now() + " Creating cabin dataframe...")
        self.create_cabin_df()

        print(time_now() + " Creating capacities map...")
        self.create_capacities_map()

        print(time_now() + " Buidling duties...")
        self.build_duties2()

        print(time_now() + " Loading RM model...")
        self.load_rm_model()

        print(time_now() + " Loading bookings...")
        self.load_bookings()

        print(time_now() + " Building time indices...")
        self.build_time_indices()

        print(time_now() + " Calculating alphas...")
        self.calculate_alphas()

    def load_inv_df(self):
        self.inv_df = pd.read_csv(self.inv_file, sep=";")
        self.inv_df["CC"] = self.inv_df["cc"]
        self.inv_df["FLTNUM"] = self.inv_df["fltnum"]
        self.inv_df["ORGN"] = self.inv_df["orgn"]
        self.inv_df["DSTN"] = self.inv_df["dstn"]
        self.inv_df["DEPDT"] = pd.to_datetime(self.inv_df["dep_time_lt"]).dt.strftime("%Y%m%d")
        self.inv_df["DEPTM"] = pd.to_datetime(self.inv_df["dep_time_lt"]).dt.strftime("%H%M")
        self.inv_df["ARRDT"] = pd.to_datetime(self.inv_df["arr_time_lt"]).dt.strftime("%Y%m%d")
        self.inv_df["ARRTM"] = pd.to_datetime(self.inv_df["arr_time_lt"]).dt.strftime("%H%M")
        self.inv_df["DEPDT_UTC"] = pd.to_datetime(self.inv_df["dep_time_utc"]).dt.strftime("%Y%m%d")
        self.inv_df["DEPTM_UTC"] = pd.to_datetime(self.inv_df["dep_time_utc"]).dt.strftime("%H%M")
        self.inv_df["ARRDT_UTC"] = pd.to_datetime(self.inv_df["arr_time_utc"]).dt.strftime("%Y%m%d")
        self.inv_df["ARRTM_UTC"] = pd.to_datetime(self.inv_df["arr_time_utc"]).dt.strftime("%H%M")
        self.inv_df["AIRCRAFT_TYPE"] = self.inv_df["aircraft_type"]
        self.inv_df = self.inv_df.fillna(0)
        self.inv_df["DUTY_ID"] = self.inv_df["id_pair"].astype(int)
        self.inv_df["NUM_IN_DUTY"] = self.inv_df["num_in_pair"].astype(int)
        self.inv_df = self.inv_df[["CC", "FLTNUM", "ORGN", "DSTN",
                                   "DEPDT", "DEPTM", "ARRDT", "ARRTM",
                                   "DEPDT_UTC", "DEPTM_UTC", "ARRDT_UTC", "ARRTM_UTC",
                                   "AIRCRAFT_TYPE", "DUTY_ID", "NUM_IN_DUTY"]]

    def load_costs_df(self):
        self.costs_df = pd.read_csv(self.costs_file, sep=";")
        self.costs_df = self.costs_df[["departure_period", "aircraft_type", "orgn", "dstn", "cost_per_pax", "exp_1_item_flt_damper"]]
        self.costs_df.columns = ["DEPDT", "AIRCRAFT", "ORGN", "DSTN", "MARGINAL_COSTS", "PCI_COSTS"]
        self.costs_df["DEPDT"] = pd.to_datetime(self.costs_df["DEPDT"], format="%d.%m.%Y").dt.strftime("%Y%m%d")
        self.costs_df = self.costs_df[["DEPDT", "ORGN", "DSTN", "AIRCRAFT", "PCI_COSTS", "MARGINAL_COSTS"]]
        self.costs_df["ORGN"] = self.costs_df["ORGN"].astype("category")
        self.costs_df["DSTN"] = self.costs_df["DSTN"].astype("category")
        self.costs_df["DEPDT"] = self.costs_df["DEPDT"].astype("category")
        self.costs_df["AIRCRAFT"] = self.costs_df["AIRCRAFT"].astype("category")

    def load_fleet_df(self):
        self.asfr = ASFleetReader(self.depdates, self.fleet_file)
        self.asfr.read()
        self.fleet_types = self.asfr.get_fleet_types()
        self.fleet_type2fleet_ids = self.asfr.get_fleet_type2fleet_ids()

    def create_cabin_df(self):
        df = pd.read_csv(self.cap_file)
        df = df.fillna(0)
        df = df[["aircraft_code", "cabin_c", "cabin_w", "cabin_y"]]
        df.columns = ["A/C", "C", "W", "Y"]
        class_columns = ["C", "W", "Y"]
        self.cabin_df = pd.DataFrame(columns=["CABIN", "A/C"])
        for r in df["A/C"].unique():
            for cmpt in class_columns:
                i = self.cabin_df.shape[0]
                self.cabin_df.loc[i] = [cmpt, r]

    def create_capacities_map(self):
        self.capacities = {}
        self.compartments = []

        config_df = pd.read_csv(self.cap_file)
        config_df = config_df.fillna(0)
        config_df = config_df[["aircraft_code", "cabin_c", "cabin_w", "cabin_y"]]
        config_df.columns = ["A/C", "C", "W", "Y"]
        for ac_type in self.fleet_types:
            self.capacities[ac_type] = {}
            cabins = self.cabin_df.loc[self.cabin_df["A/C"] == ac_type]["CABIN"].unique()
            for cabin in cabins:
                self.capacities[ac_type][cabin] = int(config_df.loc[config_df["A/C"] == ac_type][cabin].iloc[0])
                if cabin not in self.compartments:
                    self.compartments.append(cabin)

    def load_rm_model(self):
        res = {}

        prdt_names = []
        d = []
        f = []
        cap = []
        rsrc_names = []
        bkgs = []

        self.forecast_df = pd.read_csv("/home/sumkin/rmbits/src/fleet_assigner/as_data/forecast.csv")
        self.forecast_df.columns = ["FLTNUM", "DEPDT", "ORGN", "DSTN", "AIRCRAFT", "CABIN", "BKG", "FCST", "SSP_BKG"]
        self.forecast_df["DEPDT"] = pd.to_datetime(self.forecast_df['DEPDT']).dt.strftime('%Y%m%d')

        self.revenue_df = pd.read_csv("/home/sumkin/rmbits/src/fleet_assigner/as_data/revenue.csv")
        self.revenue_df.columns = ["FLTNUM", "DEPDT", "ORGN", "AIRCRAFT", "CABIN", "REVENUE", "CANDIDATE", "SDS"]
        self.revenue_df["DEPDT"] = pd.to_datetime(self.revenue_df['DEPDT']).dt.strftime('%Y%m%d')
        self.revenue_df = self.revenue_df[self.revenue_df["AIRCRAFT"] == self.revenue_df["CANDIDATE"]]

        df = self.forecast_df.merge(self.revenue_df, how="inner", on=["FLTNUM", "DEPDT", "ORGN", "CABIN", "AIRCRAFT"])
        df = df.dropna()
        assert df.shape[0] == df[["ORGN", "DSTN", "FLTNUM", "DEPDT", "CABIN"]].drop_duplicates().shape[0]

        for _, r in df.iterrows():
            orgn, dstn, fltnum, depdt, cabin = r["ORGN"], r["DSTN"], r["FLTNUM"], r["DEPDT"], r["CABIN"]

            # Product name.
            prdt_name = orgn + dstn + "SU" + str(fltnum).zfill(4) + depdt + cabin
            prdt_names.append(prdt_name)

            # Forecast.
            dmd = r["FCST"]
            d.append(dmd)

            # Fare.
            fare = r["SDS"]
            f.append(fare)

            # Capacity.
            cap.append(100)  # FIXME: fill correctly.

            # Resource names.
            rsrc_names.append(orgn + dstn + "SU" + str(fltnum).zfill(4) + depdt + cabin)

            # Bookings.
            bkgs.append(r["BKG"])

        assert len(prdt_names) == len(d) == len(f)
        res["prdt_names"] = prdt_names
        res["d"] = d
        res["f"] = f
        res["cap"] = np.array(cap)
        res["fcap"] = np.array(cap)
        res["rsrc_names"] = rsrc_names
        res["b"] = bkgs
        res["res_Adistratiodata"] = [0] * len(bkgs)

        # Matrix A.
        Ai, Aj, Adata = [], [], []
        for i in range(len(prdt_names)):
            Ai.append(i)
            Aj.append(i)
            Adata.append(1)
        res["Ai"] = Ai
        res["Aj"] = Aj
        res["Adata"] = Adata

        self.rm_model = res

    def load_bookings(self):
        self.bkg_df = pd.read_csv("/home/sumkin/rmbits/src/fleet_assigner/as_data/forecast.csv", sep=",")

    def _create_legs(self):

        def time2mins(dt, t):
            t = t.zfill(4)
            d = (datetime.strptime(dt, "%Y%m%d") - datetime.strptime(self.depdates[0], "%Y%m%d")).days
            h = t[:2]
            m = t[2:4]
            return d * 1440 + int(h) * 60 + int(m)

        # Create list of legs.
        # Go over inventory and take all AY flights departing on given departure dates.
        for depdate in self.depdates:
            inv_df = self.inv_df[self.inv_df["DEPDT"] == depdate]
            for _, r in inv_df.iterrows():
                orgn = r["ORGN"]
                dstn = r["DSTN"]
                fltnum = r["FLTNUM"]
                depdt = r["DEPDT_UTC"]
                arrdt = r["ARRDT_UTC"]
                deptm = time2mins(r["DEPDT_UTC"], r["DEPTM_UTC"])
                arrtm = time2mins(r["ARRDT_UTC"], r["ARRTM_UTC"])
                at = r["AIRCRAFT_TYPE"]
                duty_id = r["DUTY_ID"]
                if duty_id == 0:
                    continue
                leg = [orgn, dstn, fltnum, depdt, arrdt, deptm, arrtm, at]
                if self.costs_df[(self.costs_df["ORGN"] == orgn) &
                                 (self.costs_df["DSTN"] == dstn)].shape[0] == 0:
                    print("WARNING: {}-{} not found in costs file.".format(orgn, dstn))
                    continue
                if leg not in self.legs:
                    leg_id = len(self.legs)
                    self.legs.append(leg)
                    assert leg_id not in self.leg_id2duty_id.keys()
                    self.leg_id2duty_id[leg_id] = duty_id
                    if duty_id in self.duty_id2leg_id.keys():
                        self.duty_id2leg_id[duty_id].append(leg_id)
                    else:
                        self.duty_id2leg_id[duty_id] = [leg_id]
        assert len(self.legs) != 0

        # Create mapping orgn, dstn, fltnum, depdt -> leg_id.
        for i in range(len(self.legs)):
            orgn, dstn, fltnum, depdt, _, _, _, _ = self.legs[i]
            k = orgn + "-" + dstn + "-" + str(fltnum).zfill(4) + "-" + str(depdt)
            assert k not in self.orgn_dstn_fltnum_depdt2leg_id.keys()
            self.orgn_dstn_fltnum_depdt2leg_id[k] = i

    def build_duties2(self):
        self._create_legs()

        # Clean-up. Remove duties with just one leg and remove corresponding legs.
        duty_ids = list(self.duty_id2leg_id.keys())
        for duty_id in duty_ids:
            if len(self.duty_id2leg_id[duty_id]) == 1:
                leg_ids = self.duty_id2leg_id[duty_id]
                for leg_id in leg_ids:
                    del self.leg_id2duty_id[leg_id]
                print("Deleting duty {}".format(duty_id))
                del self.duty_id2leg_id[duty_id]

        self.duty_ids, self.duties, self.duties_svc, self.duties2startend = [], [], [], []
        self.fixed_duties = []
        self.wetlease_sequences = []
        self.duty2at = {}

        for duty_id in self.duty_id2leg_id.keys():
            assert len(self.duty_id2leg_id[duty_id]) == 2
            leg_id1, leg_id2 = self.duty_id2leg_id[duty_id]
            leg1 = self.legs[leg_id1]
            leg2 = self.legs[leg_id2]
            assert leg1[7] == leg2[7]

            min_t = min(leg1[5], leg2[5])
            max_t = max(leg1[6], leg2[6])

            if leg1[0] == "SVO":
                assert leg1[1] == leg2[0]
                assert leg2[1] == "SVO"
                self.duty_ids.append(duty_id)
                self.duties.append([leg_id1, leg_id2])
                self.duties_svc.append([])
                self.duties2startend.append([min_t, max_t])
                self.duty2at[duty_id] = leg1[7]
            elif leg2[0] == "SVO":
                assert leg2[1] == leg1[0]
                assert leg1[1] == "SVO"
                self.duty_ids.append(duty_id)
                self.duties.append([leg_id2, leg_id1])
                self.duties_svc.append([min_t, max_t])
                self.duties2startend.append([min_t, max_t])
                self.duty2at[duty_id] = leg2[7]

    def load_turnaround_times(self):
        data = []
        for fleet_type in self.fleet_types:
            data.append({"Subfleet": fleet_type, "Turnaround": 30})
        self.turnaround_times_df = pd.DataFrame(data)

    def build_time_indices(self):
        # Duties.
        ts = [e[0] for e in self.duties2startend] + [e[1] for e in self.duties2startend]
        self.ts = list(set(ts))
        self.ts.sort()

    def calculate_alphas(self):

        def calc_duty_times(d, k):
            turnaround_time = self.get_turnaround_time(k)
            min_t = np.inf
            max_t = -np.inf 
            for i in self.duties[d]:
                deptm = self.legs[i][5]
                min_t = min(min_t, deptm)
                max_t = max(max_t, deptm)

                arrtm = self.legs[i][6]
                min_t = min(min_t, arrtm)
                max_t = max(max_t, arrtm)
            return min_t - turnaround_time, max_t - 1

        num = 0
        self.alphas = {}
        sys.stdout.write("\t\t    ")
        for d in range(len(self.duties)):
            num += 1
            if d % 100 == 0:
                sys.stdout.write("\b\b\b\b")
                sys.stdout.write("{:>3}%".format(int((100 * d)/num))) 
                sys.stdout.flush()
            for k in range(len(self.fleet_types)):
                min_t, max_t = calc_duty_times(d, k)
                for t in range(1, len(self.ts)):
                    t0, t1 = self.ts[t-1], self.ts[t]
                    if max(min_t, t0) <= min(max_t, t1 - 1):
                        self.alphas[(self.duty_ids[d], t, k)] = 1

        sys.stdout.write("\b\b\b\b\b\b")
        sys.stdout.write("\n")
        sys.stdout.flush()

    def get_num_legs(self):
        return len(self.legs)

    def get_num_resources(self):
        return len(self.rm_model["rsrc_names"])

    def get_num_products(self):
        return len(self.rm_model["prdt_names"])

    def get_num_fleet_types(self):
        return len(self.fleet_types)

    def get_num_duties(self):
        return len(self.duties)

    def get_num_compartments(self):
        return len(self.compartments)

    def get_demand(self, j):
        assert j >= 0 and j <= self.get_num_products()
        return self.rm_model["d"][j]

    def get_booked_revenue(self):
        return self.revenue_df["REVENUE"].sum()

    def get_booked_pax(self):
        return self.bkg_df.shape[0]

    def get_fare(self, j):
        assert j >= 0 and j <= self.get_num_products()
        return self.rm_model["f"][j]

    def get_leg_costs(self, orgn, dstn, depdt, ac_type):
        t_ac_type = ac_type

        res = 0.0
        depdt = depdt[:4] + "-" + depdt[4:6] + "-" + depdt[6:8]
        costs_df = self.costs_df[
            (self.costs_df["ORGN"] == orgn) &
            (self.costs_df["DSTN"] == dstn) &
            (self.costs_df["DEPDT"] == depdt) &
            (self.costs_df["AIRCRAFT"] == t_ac_type)
            ]["PCI_COSTS"]
        if costs_df.shape[0] == 1:
            res += costs_df.iloc[0]
        else:
            # Skip flight number and take average.
            costs_df = self.costs_df[
                (self.costs_df["ORGN"] == orgn) &
                (self.costs_df["DSTN"] == dstn) &
                (self.costs_df["DEPDT"] == depdt) &
                (self.costs_df["AIRCRAFT"] == t_ac_type)
                ]
            if costs_df.shape[0] < 1:
                costs_df = self.costs_df[
                    (self.costs_df["ORGN"] == orgn) &
                    (self.costs_df["DSTN"] == dstn) &
                    (self.costs_df["AIRCRAFT"] == t_ac_type)
                    ]
            if costs_df.shape[0] < 1:
                print("orgn, dstn, t_ac_type = {}, {}, {}".format(orgn, dstn, t_ac_type))
            if costs_df.shape[0] >= 1:
                res += costs_df["PCI_COSTS"].mean()
            else:
                res += 0.0
        return res

    def get_duty_costs(self, d, k):
        assert d in self.duty_ids
        assert k >= 0 and k <= self.get_num_fleet_types()
        ac_type = self.fleet_types[k]

        res = 0.0
        for leg_id in self.duties[self.duty_ids.index(d)]:
            orgn, dstn, _, depdt, _, _, _, _ = self.legs[leg_id]
            res += self.get_leg_costs(orgn, dstn, depdt, ac_type)
        return res

    def get_leg_id_by_rsrc_name(self, rsrc_name):
        """
        Returns index in the list self.legs for resource.
        """
        cc = rsrc_name[:2]
        orgn = rsrc_name[2:5]
        dstn = rsrc_name[5:8]
        fltnum = rsrc_name[8:12]
        cmpt = rsrc_name[12]
        depdt = rsrc_name[13:21]
        k = orgn + "-" + dstn + "-" + str(fltnum).zfill(4) + "-" + str(depdt)
        if k in self.orgn_dstn_fltnum_depdt2leg_id.keys():
            return self.orgn_dstn_fltnum_depdt2leg_id[k]
        else:
            return None

    def get_rsrc_name_indices_by_leg(self, orgn, dstn, fltnum, depdt):
        res = []
        for idx in range(len(self.rm_model["rsrc_names"])):
            rsrc_name = self.rm_model["rsrc_names"][idx]
            r_orgn = rsrc_name[2:5]
            r_dstn = rsrc_name[5:8]
            r_fltnum = rsrc_name[8:12]
            r_depdt = rsrc_name[13:21]
            if orgn == r_orgn and dstn == r_dstn and int(fltnum) == int(r_fltnum) and int(depdt) == int(r_depdt):
                res.append(idx)
        return res

    def get_leg_id(self, orgn, dstn, fltnum, depdt):
        """
        Returns index in the list of self.legs resource.
        """
        k = orgn + "-" + dstn + "-" + str(fltnum).zfill(4) + "-" + str(depdt)
        if k in self.orgn_dstn_fltnum_depdt2leg_id.keys():
            return self.orgn_dstn_fltnum_depdt2leg_id[k]
        else:
            return None

    def get_leg_by_id(self, idx):
        """
        Returns the leg corresponding to id.
        """
        assert idx < len(self.legs)
        return self.legs[idx]

    def get_fleet_type_by_id(self, idx):
        """
        Returns the fleet type corresponding to id.
        """
        assert idx < len(self.fleet_types)
        return self.fleet_types[idx]

    def get_duty_id_by_leg_id(self, leg_id):
        """
        Find duty id for given leg id.
        """
        if leg_id in self.leg_id2duty_id.keys():
            return self.leg_id2duty_id[leg_id]
        else:
            return None

    def get_cmpt_id(self, rsrc_name):
        cmpt = rsrc_name[20]
        return self.compartments.index(cmpt)

    def get_capacity(self, k, l):
        ac_type = self.fleet_types[k]
        assert ac_type in self.capacities.keys()
        assert l < len(self.compartments)
        cmpt = self.compartments[l]
        if cmpt in self.capacities[ac_type].keys():
            res = self.capacities[ac_type][cmpt]
            return res
        else:
            return 0

    def get_num_time_indices(self):
        return len(self.ts) 

    def get_alpha(self, d, t, k):
        if (d, t, k) in self.alphas.keys():
            return self.alphas[(d, t, k)]
        else:
            return 0

    def get_num_aircrafts(self, k, t):
        assert t > 0  # Index defines time interval [T[t-1],T[t]].
        ac_type = self.fleet_types[k]
        t0_min, t1_min = self.ts[t-1], self.ts[t]
        return self.asfr.get_num_aircrafts(ac_type, t0_min, t1_min)

    def get_solution_from_inv_df(self):
        y = {}
        for d in range(self.get_num_duties()):
            for k in range(self.get_num_fleet_types()):
                if self.duty2at[d] == self.fleet_types[k]:
                    y[(d, k)] = 1
                else:
                    y[(d, k)] = 0

        z = {}
        for j in range(self.get_num_products()):
            z[j] = 0

        w = {}
        for d in range(self.get_num_duties()):
            w[d] = 1

        v = {}
        for d in range(self.get_num_duties()):
            for k in range(self.get_num_fleet_types()):
                if self.duty2at[d] == self.fleet_types[k]:
                    v[(d, k)] = 1
                else:
                    v[(d, k)] = 0

        return y, z, w, v

    def get_solution_from_pairings(self):
        y = {}
        for d in range(self.get_num_duties()):
            for k in range(self.get_num_fleet_types()):
                if self.duty2at[d] == self.fleet_types[k]:
                    y[(d, k)] = 1
                else:
                    y[(d, k)] = 0

        z = {}
        for j in range(self.get_num_products()):
            z[j] = 0

        return y, z

    def get_turnaround_time(self, k):
        ac = self.fleet_types[k]
        res = self.turnaround_times_df[
            self.turnaround_times_df["Subfleet"] == ac
        ]["Turnaround"].iloc[0]
        return res

    def duty_contains(self, duty_id, ap):
        for leg_id in self.duties[duty_id]:
            leg = self.legs[leg_id]
            orgn, dstn = leg[0], leg[1]
            if orgn == ap or dstn == ap:
                return True
        return False

if __name__ == "__main__":
    depdates = ["20251219", "20251220"]
    inv_file = "/home/sumkin/rmbits/src/fleet_assigner/as_data/inv2.csv"
    costs_file = "/home/sumkin/rmbits/src/fleet_assigner/as_data/costs.csv"
    fleet_file = "/home/sumkin/rmbits/src/fleet_assigner/as_data/aircraft_inventory.csv"
    cap_file = "/home/sumkin/rmbits/src/fleet_assigner/as_data/capacities.csv"
    maintenance_file = ""
    leg_pairings_file = "s3://ay-emr-job/fleet_assigner/input/leg_pairings.xlsx"
    turnaround_times_file = "s3://ay-emr-job/fleet_assigner/input/turnaround_times.csv"

    asdr = ASDataReader(depdates,
                        inv_file,
                        costs_file,
                        fleet_file,
                        cap_file,
                        maintenance_file,
                        leg_pairings_file,
                        turnaround_times_file)
    asdr.read()



