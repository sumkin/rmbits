import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings

from utils import time_now
from lpmodelmultiloader import LPModelMultiLoader 
from duties_builder import DutiesBuilder
from duties_builder2 import DutiesBuilder2
from fleet_reader import FleetReader
from maintenance_reader import MaintenanceReader
from wetlease_reader import WetleaseReader
from excel_output_writer import ExcelOutputWriter

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

class DataReader:

    def __init__(
        self,
        fcstdate,
        depdates,
        costs_file,
        fleet_file,
        cap_file,
        leg_distance_file,
        subfleet_ranges_file,
        maintenance_file,
        airport_allowance_file,
        leg_pairings_file,
        turnaround_times_file,
        restrictions_file,
        output_writer
    ):
        self.fcstdate = fcstdate 
        self.depdates = depdates
        self.costs_file = costs_file
        self.fleet_file = fleet_file
        self.cap_file = cap_file
        self.leg_distance_file = leg_distance_file
        self.subfleet_ranges_file = subfleet_ranges_file
        self.maintenance_file = maintenance_file
        self.airport_allowance_file = airport_allowance_file
        self.leg_pairings_file = leg_pairings_file
        self.turnaround_times_file = turnaround_times_file
        self.restrictions_file = restrictions_file
        self.output_writer = output_writer

        self.legs = []
        self.missing_fcst_legs = []
        self.orgn_dstn_fltnum_depdt2leg_id = {}  # Map to speed-up querying for leg id.
        self.leg2deparrtm = {}
        self.leg2svc = {}

    def read(self):
        print(time_now() + " Loading inventory dataframe...")
        self.load_inv_df()

        print(time_now() + " Loading costs dataframe...")
        self.load_costs_df()

        print(time_now() + " Loading turnaround times..")
        self.load_turnaround_times()

        print(time_now() + " Loading restrictions...")
        self.load_restrictions()

        print(time_now() + " Loading fleet dataframe...")
        self.load_fleet_df()

        print(time_now() + " Loading leg distance dataframe...")
        self.load_leg_distance_df()

        print(time_now() + " Loading subfleet range dataframe...")
        self.load_subfleet_range_df()

        print(time_now() + " Creating cabin dataframe...")
        self.create_cabin_df()

        print(time_now() + " Creating capacities map...")
        self.create_capacities_map()

        print(time_now() + " Loading RM model...")
        self.load_rm_model()

        print(time_now() + " Loading bookings...")
        self.load_bookings()

        print(time_now() + " Loading maintenance...")
        self.load_maintenance()

        print(time_now() + " Loading airport allowance...")
        self.load_airport_allowance()

        print(time_now() + " Loading pairings...")
        self.load_pairings()

        print(time_now() + " Buidling duties...")
        self.build_duties2()

        print(time_now() + " Building time indices...")
        self.build_time_indices()

        print(time_now() + " Calculating alphas...")
        self.calculate_alphas()

    def load_inv_df(self):
        fcstyear, fcstmonth = self.fcstdate[:4], self.fcstdate[4:6]
        self.inv_df = pd.read_csv("s3://ay-rmp-home/nrm/bif/{}/{}/INV_{}.csv.gz".format(fcstyear, fcstmonth, self.fcstdate),
                                   dtype={"ARRDT": str, "DEPTM": str, "ARRTM": str})
        self.next_depdate = datetime.strptime(self.depdates[len(self.depdates) - 1], "%Y%m%d") + timedelta(days=1)
        self.next_depdate = datetime.strftime(self.next_depdate, "%Y%m%d")
        self.inv_df["DEPDT"] = self.inv_df["DEPDT"].astype(str) 
        self.inv_df = self.inv_df.loc[self.inv_df["DEPDT"].isin(self.depdates + [self.next_depdate])]
        self.inv_df = self.inv_df[["CC", "FLTNUM", "ORGN", "DSTN", "CABIN",
                                   "DEPDT", "DEPTM", "ARRDT", "ARRTM",
                                   "DEPDT_UTC", "DEPTM_UTC", "ARRDT_UTC", "ARRTM_UTC", "AIRCRAFT_TYPE", "BKC"]]
        self.inv_df = self.inv_df.drop_duplicates()

        self.inv_df["DEPDT"] = self.inv_df["DEPDT"].astype(str)
        self.inv_df["DEPTM"] = self.inv_df["DEPTM"].astype(str)
        self.inv_df["ARRDT"] = self.inv_df["ARRDT"].astype(str)
        self.inv_df["ARRTM"] = self.inv_df["ARRTM"].astype(str)

        self.inv_df["DEPDT_UTC"] = self.inv_df["DEPDT_UTC"].astype(str)
        self.inv_df["DEPTM_UTC"] = self.inv_df["DEPTM_UTC"].astype(str)
        self.inv_df["ARRDT_UTC"] = self.inv_df["ARRDT_UTC"].astype(str)
        self.inv_df["ARRTM_UTC"] = self.inv_df["ARRTM_UTC"].astype(str)
        self.inv_df = self.inv_df[["CC", "FLTNUM", "ORGN", "DSTN", "CABIN",
                                   "DEPDT", "DEPTM", "ARRDT", "ARRTM",
                                   "DEPDT_UTC", "DEPTM_UTC", "ARRDT_UTC",
                                   "ARRTM_UTC", "AIRCRAFT_TYPE", "BKC"]]
        self.inv_df = self.inv_df[
            (
                self.inv_df["FLTNUM"] <= 1999
            ) |
            (
                (self.inv_df["FLTNUM"] >= 7000) &
                (self.inv_df["FLTNUM"] <= 7999)
            ) |
            (  # C flights
                (self.inv_df["FLTNUM"] >= 2001) &
                (self.inv_df["FLTNUM"] <= 2500)
            ) |
            (  # P flights.
                (self.inv_df["FLTNUM"] >= 8881) &
                (self.inv_df["FLTNUM"] <= 8996)
            ) |
            (  # K flights.
                (self.inv_df["FLTNUM"] == 9971) |
                (self.inv_df["FLTNUM"] == 9951)
            )
        ]
        self.inv_df = self.inv_df.drop_duplicates()
        self._build_inv_lookup()

    def _build_inv_lookup(self):
        self._inv_keys = set(zip(
            self.inv_df["CC"].astype(str),
            self.inv_df["ORGN"].astype(str),
            self.inv_df["DSTN"].astype(str),
            self.inv_df["FLTNUM"].astype(int),
            self.inv_df["DEPDT_UTC"].astype(str),
        ))

    def load_costs_df(self):
        self.costs_df = pd.read_csv(self.costs_file)
        self.costs_df.columns = ["DEPDT", "FLTNUM", "ORGN", "DSTN", "AIRCRAFT", "PCI_COSTS", "MARGINAL_COSTS"]
        self.costs_df["ORGN"] = self.costs_df["ORGN"].astype("category")
        self.costs_df["DSTN"] = self.costs_df["DSTN"].astype("category")
        self.costs_df["DEPDT"] = self.costs_df["DEPDT"].astype("category")
        self.costs_df["AIRCRAFT"] = self.costs_df["AIRCRAFT"].astype("category")
        self._build_costs_lookup()

    def _build_costs_lookup(self):
        df = self.costs_df.copy()
        df["ORGN"] = df["ORGN"].astype(str)
        df["DSTN"] = df["DSTN"].astype(str)
        df["DEPDT"] = df["DEPDT"].astype(str)
        df["AIRCRAFT"] = df["AIRCRAFT"].astype(str)
        self._costs_exact = df.groupby(["ORGN", "DSTN", "DEPDT", "AIRCRAFT"])["PCI_COSTS"].mean().to_dict()
        self._costs_no_date = df.groupby(["ORGN", "DSTN", "AIRCRAFT"])["PCI_COSTS"].mean().to_dict()

    def load_fleet_df(self):
        self.fr = FleetReader(self.depdates,
                              self.fleet_file,
                              self.cap_file,
                              self.maintenance_file,
                              self.turnaround_times_df)
        self.fr.read()
        self.fleet_types = self.fr.get_fleet_types()
        self.fleet_type2fleet_ids = self.fr.get_fleet_type2fleet_ids()

    def load_leg_distance_df(self):
        self.leg_distance_df = pd.read_csv(self.leg_distance_file, sep=",")
        self._build_leg_distance_lookup()

    def _build_leg_distance_lookup(self):
        self._leg_distance = {}
        for _, row in self.leg_distance_df.iterrows():
            key = (str(row["ORIGIN"]), str(row["DESTINATION"]))
            if key not in self._leg_distance:
                self._leg_distance[key] = row["DISTANCE"]

    def get_leg_distance(self, orgn, dstn):
        key = (orgn, dstn)
        if key in self._leg_distance:
            return self._leg_distance[key]
        warnings.warn("{} {} in leg_distance.csv is not found".format(orgn, dstn))
        return 0

    def load_subfleet_range_df(self):
        self.subfleet_range_df = pd.read_csv(self.subfleet_ranges_file, sep=";")
        self.subfleet_range_df.columns = ["OWNER", "SUBFLEET", "MAX_RANGE"]
        self.subfleet_range_df = self.subfleet_range_df[
            (self.subfleet_range_df["OWNER"] == "AY") |
            (self.subfleet_range_df["OWNER"] == "N7") |
            (self.subfleet_range_df["OWNER"] == "IB") |
            (self.subfleet_range_df["OWNER"] == "JP")
        ]
        self._build_subfleet_range_lookup()

    def _build_subfleet_range_lookup(self):
        self._subfleet_max_range = {}
        for _, row in self.subfleet_range_df.iterrows():
            sf = str(row["SUBFLEET"])
            if sf not in self._subfleet_max_range:
                self._subfleet_max_range[sf] = row["MAX_RANGE"]

    def get_subfleet_max_range(self, fleet_type):
        assert fleet_type in self._subfleet_max_range, \
            "Fleet type {} is not found in subfleet_range_df.".format(fleet_type)
        return self._subfleet_max_range[fleet_type]

    def create_cabin_df(self):
        df = pd.read_csv(self.cap_file)
        self.cabin_df = pd.DataFrame(columns=["CABIN", "A/C"])
        class_columns = []
        for column in df.columns:
            if len(column) == 1: # Class column has one symbol.
                class_columns.append(column)
        for r in df["Subfleet"].unique():
            for cmpt in class_columns:
                if pd.notna(df.loc[df["Subfleet"] == r][cmpt].iloc[0]):
                    i = self.cabin_df.shape[0]
                    self.cabin_df.loc[i] = [cmpt, r]

    def create_capacities_map(self):
        self.capacities = {}
        self.compartments = []

        config_df = pd.read_csv(self.cap_file)
        for ac_type in self.fleet_types:
            self.capacities[ac_type] = {}
            cabins = self.cabin_df.loc[self.cabin_df["A/C"] == ac_type]["CABIN"].unique()
            for cabin in cabins:
                self.capacities[ac_type][cabin] = config_df.loc[config_df["Subfleet"] == ac_type][cabin].iloc[0]
                if cabin not in self.compartments:
                    self.compartments.append(cabin)

    def load_rm_model(self):
        loader = LPModelMultiLoader(self.fcstdate, self.depdates)
        self.rm_model = loader.get()

    def load_bookings(self):
        self.bkg_df = pd.read_csv("s3://ay-rmp-home/nrm/bof/{}/{}/BKG_OD_{}.csv.gz".format(self.fcstdate[:4], self.fcstdate[4:6], self.fcstdate), low_memory = False)
        self.bkg_df = self.bkg_df[self.bkg_df["BASE_OD_DEPT_DATE"].isin([int(depdate) for depdate in self.depdates])]

    def load_maintenance(self):
        self.maint_df = MaintenanceReader(self.maintenance_file, self.depdates[0], self.turnaround_times_df).load()
        self.wetlease_df = WetleaseReader(self.maintenance_file, self.depdates[0]).load()

    def load_airport_allowance(self):
        self.airport_allowance_df = pd.read_csv(self.airport_allowance_file)
        self._build_airport_allowance_lookup()

    def _build_airport_allowance_lookup(self):
        self._airport_allowance = set(
            zip(self.airport_allowance_df["AIRPORT"].astype(str),
                self.airport_allowance_df["AT"].astype(str))
        )

    def is_airport_allowed(self, airport, at):
        return (airport, at) in self._airport_allowance

    def load_pairings(self):
        self.pairings_df = pd.read_excel(self.leg_pairings_file, sheet_name="Data")
        for i, r in self.pairings_df.iterrows():
            if r["A/C"] == "32V":
                # This is wetlease. Should be ignored.
                print("WARNING: r = {} is ignored (wetlease).".format(r))
                continue

            if r["Svc"].strip() == "Z":
                # This is maintenance. Ignore such entries for duty builder.
                print("WARNING: r = {} is ignored (maintenance).".format(r))
                continue

            flids = r["FlId"].strip().split()
            flids = [e for e in flids if e != ""]
            assert len(flids) == 2, "flids = {}".format(flids)

            cc, fltnum = flids[0], flids[1]
            orgn = r["Orig"].strip()
            dstn = r["Dest"].strip()
            depdate_utc = datetime.strftime(r["Date"], "%Y%m%d")
            deptm_utc = r["STD"]
            arrtm_utc = r["STA"]
            k = (cc, orgn, dstn, int(fltnum), depdate_utc)
            self.leg2deparrtm[k] = (deptm_utc, arrtm_utc)
            self.leg2svc[k] = r["Svc"]

    def _create_legs(self):

        def time2mins(dt, t):
            t = t.zfill(4)
            d = (datetime.strptime(dt, "%Y%m%d") - datetime.strptime(self.depdates[0], "%Y%m%d")).days
            h = t[:2]
            m = t[2:4]
            return d * 1440 + int(h) * 60 + int(m)

        # Create list of legs.
        for i, r in self.pairings_df.iterrows():
            flids = r["FlId"].strip().split()
            flids = [e for e in flids if e != ""]
            assert len(flids) == 2, "flids = {}".format(flids)

            cc = flids[0] #r["Own"].strip()
            fltnum = flids[1]
            orgn = r["Orig"].strip()
            dstn = r["Dest"].strip()
            depdt = datetime.strftime(r["Date"], "%Y%m%d")
            arrdt = datetime.strftime(r["ArrDate"], "%Y%m%d")
            deptm = r["STD"].strftime("%H%M")
            arrtm = r["STA"].strftime("%H%M")
            dep_mins = time2mins(depdt, deptm)
            arr_mins = time2mins(arrdt, arrtm)
            at = r["A/C"]
            leg = [orgn, dstn, fltnum, depdt, arrdt, dep_mins, arr_mins, at, cc]

            if orgn == "HEL" and dstn == "HEL":
                # Skip HEL maintenance blocks. They are read from SSIM file.
                # TLL maintenance blocks should be there.
                continue

            # Check that leg is in costs dataframe.
            if self.costs_df[
                (self.costs_df["ORGN"] == orgn) &
                (self.costs_df["DSTN"] == dstn)
            ].shape[0] == 0:
                print("WARNING: {}-{} not found in costs file.".format(orgn, dstn))

            # Check that leg is in inventory.
            #print("fltnum = {}".format(fltnum))
            if fltnum.isdigit() and (cc, orgn, dstn, int(fltnum), depdt) not in self._inv_keys:
                print("WARNING: {}-{}-{}-{}-{} not found in inventory.".format(cc, orgn, dstn, int(fltnum), depdt))
                if leg not in self.missing_fcst_legs:
                    self.missing_fcst_legs.append(leg)
            else:
                if leg not in self.legs:
                    self.legs.append(leg)

        assert len(self.legs) != 0
        s1 = {tuple(e) for e in self.legs}
        s2 = {tuple(e) for e in self.missing_fcst_legs}
        assert len(s1) == len(self.legs)
        assert len(s2) == len(self.missing_fcst_legs)
        assert s1.isdisjoint(s2)

        # Update rm_model.
        cap = list(self.rm_model["cap"])
        fcap = list(self.rm_model["fcap"])
        for m_leg in self.missing_fcst_legs:
            orgn, dstn, fltnum, depdt, _, _, _, _, _ = m_leg
            rsrc_name = "AY" + orgn + dstn + str(fltnum).zfill(4) + "Y" + depdt
            self.legs.append(m_leg)
            cap.append(0)
            fcap.append(0)
            self.rm_model["rsrc_names"].append(rsrc_name)
            k = str(int(fltnum)) + "Y" + depdt
            self.rm_model["rownumd"][k] = max(self.rm_model["rownumd"].values())
            self.rm_model["cap"] = np.array(cap)
            self.rm_model["fcap"] = np.array(fcap)

        # Create mapping orgn, dstn, fltnum, depdt -> leg_id.
        for i in range(len(self.legs)):
            orgn, dstn, fltnum, depdt, _, _, _, _, _ = self.legs[i]
            if isinstance(fltnum, int) or fltnum.isdigit():
                k = orgn + "-" + dstn + "-" + str(fltnum).zfill(4) + "-" + str(depdt)
            else:
                k = orgn + "-" + dstn + "-" + fltnum.strip() + "-" + str(depdt)
            assert k not in self.orgn_dstn_fltnum_depdt2leg_id.keys(), "k = {}".format(k)
            self.orgn_dstn_fltnum_depdt2leg_id[k] = i

        """
        for leg in self.legs:
            fltnum = leg[2]
            if fltnum.isdigit():
                if int(fltnum) == 8921 or int(fltnum) == 8922:
                    print(leg)
            else:
                print(leg)
        assert False
        """

    def build_duties2(self):
        self._create_legs()

        db = DutiesBuilder2(self,
                            self.leg_pairings_file,
                            self.depdates,
                            self.next_depdate,
                            self.legs,
                            self.fleet_types,
                            self.output_writer)
        (self.duties,
         self.duties_svc,
         self.duties2startend,
         standalone,
         self.leg2duty,
         self.duty2at,
         self.fixed_duties,
         self.wetlease_sequences) = db.build()
        assert len(self.duties) == len(self.duties_svc) == len(self.duties2startend), "{}, {}, {}".format(len(self.duties), len(self.duties_svc), len(self.duties2startend))

    def load_turnaround_times(self):
        self.turnaround_times_df = pd.read_csv(self.turnaround_times_file)

    def load_restrictions(self):
        self.restrictions_df = pd.read_csv(self.restrictions_file)

    def build_time_indices(self):
        # Duties.
        ts = [e[0] for e in self.duties2startend] + [e[1] for e in self.duties2startend]

        # Maintenance.
        ts += list(self.maint_df["from_mins"])
        ts += list(self.maint_df["to_mins"])
        self.ts = list(set(ts))
        self.ts.sort()

    def calculate_alphas(self):
        # Precompute turnaround times once — avoids a DataFrame filter per (d, k)
        turnaround_times = [self.get_turnaround_time(k) for k in range(len(self.fleet_types))]

        ts_arr = np.array(self.ts)
        t0s = ts_arr[:-1]        # ts[t-1] for each interval
        t1s_m1 = ts_arr[1:] - 1  # ts[t] - 1 for each interval

        D = len(self.duties)
        self.alphas = {}
        sys.stdout.write("\t\t    ")
        for d in range(D):
            if d % 100 == 0:
                sys.stdout.write("\b\b\b\b")
                sys.stdout.write("{:>3}%".format(d * 100 // D))
                sys.stdout.flush()

            # Compute base leg times once per duty — shared across all fleet types
            leg_times = []
            for i in self.duties[d]:
                leg_times.append(self.legs[i][5])  # dep_mins
                leg_times.append(self.legs[i][6])  # arr_mins
            base_min = min(leg_times)
            base_max = max(leg_times)
            max_t = base_max - 1  # same for every k

            for k, tt in enumerate(turnaround_times):
                min_t = base_min - tt
                # vectorised interval check: max(min_t, t0) <= min(max_t, t1-1)
                active = np.where((min_t <= t1s_m1) & (max_t >= t0s))[0]
                for idx in active:
                    self.alphas[(d, int(idx) + 1, k)] = 1

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
        return self.bkg_df["YIELD"].sum()

    def get_booked_pax(self):
        return self.bkg_df.shape[0]

    def get_fare(self, j):
        assert j >= 0 and j <= self.get_num_products()
        return self.rm_model["f"][j]

    def get_leg_costs(self, orgn, dstn, depdt, ac_type):

        def transform_ac_type(ac_type):
            if ac_type == "29A":
                ac_type = None
            elif ac_type == "319":
                pass
            elif ac_type == "320":
                pass
            elif ac_type == "321":
                pass
            elif ac_type == "32B":
                pass
            elif ac_type == "32G":
                ac_type = "321"
            elif ac_type == "32I":
                ac_type = "321"
            elif ac_type == "32L":
                ac_type = "321"
            elif ac_type == "33B":
                ac_type = "333"
            elif ac_type == "33S":
                ac_type = "333"
            elif ac_type == "35A":
                ac_type = "359"
            elif ac_type == "35B":
                ac_type = "359"
            elif ac_type == "35L":
                ac_type = "359"
            elif ac_type == "35S":
                ac_type = "359"
            elif ac_type == "A70":
                ac_type = "AT7"
            elif ac_type == "A7A":
                ac_type = "AT7"
            elif ac_type == "DH4":
                ac_type = None
            elif ac_type == "E90":
                pass
            elif ac_type == "31E":
                pass
            elif ac_type == "73Z":
                pass
            else:
                ac_type = None
            return ac_type

        t_ac_type = transform_ac_type(ac_type)
        if t_ac_type is None:
            print(f"ac_type = {ac_type}")
            assert False

        depdt_fmt = depdt[:4] + "-" + depdt[4:6] + "-" + depdt[6:8]
        key = (orgn, dstn, depdt_fmt, t_ac_type)
        if key in self._costs_exact:
            return self._costs_exact[key]
        key2 = (orgn, dstn, t_ac_type)
        if key2 in self._costs_no_date:
            return self._costs_no_date[key2]
        print("orgn, dstn, t_ac_type = {}, {}, {}".format(orgn, dstn, t_ac_type))
        return 0.0

    def get_duty_costs(self, d, k):
        assert d >= 0 and d <= self.get_num_duties()
        assert k >= 0 and k <= self.get_num_fleet_types()
        ac_type = self.fleet_types[k]

        res = 0.0
        for leg_id in self.duties[d]:
            orgn, dstn, _, depdt, _, _, _, _, _ = self.legs[leg_id]
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
        if isinstance(fltnum, int) or fltnum.isdigit():
            k = orgn + "-" + dstn + "-" + str(fltnum).zfill(4) + "-" + str(depdt)
        else:
            k = orgn + "-" + dstn + "-" + fltnum.strip() + "-" + str(depdt)
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

    def get_duty_id_by_leg_id(self, leg_idx):
        """
        Find duty id for given leg id.
        """
        if leg_idx in self.leg2duty.keys():return self.leg2duty[leg_idx]
        else:
            return None

    def get_cmpt_id(self, rsrc_name):
        cmpt = rsrc_name[12]
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
        t0 = datetime.strptime(self.depdates[0], "%Y%m%d") + timedelta(minutes=t0_min)
        t1 = datetime.strptime(self.depdates[0], "%Y%m%d") + timedelta(minutes=t1_min-1)
        debug = False
        return self.fr.get_num_aircrafts(ac_type, t0_min, t1_min, t0, t1, self.wetlease_sequences)

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
    excel_output_writer = ExcelOutputWriter("../output/fleet_assigner.xlsx")

    fcstdate = "20250421"
    month = "august2025"
    fcstyear, fcstmonth, fcstday = fcstdate[:4], fcstdate[4:6], fcstdate[6:]
    depdates = ["20250801", "20250802", "20250803", "20250804", "20250805", "20250806", "20250807",
                "20250808", "20250809", "20250810", "20250811", "20250812", "20250813", "20250814",
                "20250815", "20250816", "20250817", "20250818", "20250819", "20250820", "20250821",
                "20250822", "20250823", "20250824", "20250825", "20250826", "20250827", "20250828",
                "20250829", "20250830", "20250831"]
    costs_file = "s3://ay-rmp-home/anaplan_costs/{}/{}/{}/{}.csv".format(fcstyear, fcstmonth, fcstday, month)
    fleet_file = "s3://ay-rmp-home/fleet_assigner/input/aircraft_inventory.csv"
    cap_file = "s3://ay-rmp-home/fleet_assigner/input/subfleet_capacities.csv"
    leg_distance_file = "s3://ay-rmp-home/fleet_assigner/input/leg_distances.csv"
    subfleet_ranges_file = "s3://ay-rmp-home/fleet_assigner/input/subfleet_ranges.csv"
    maintenance_file = "s3://ay-rmp-home/fleet_assigner/input/AUG.ssim"
    airport_allowance_file = "s3://ay-rmp-home/fleet_assigner/input/airport_allowance.csv"
    leg_pairings_file = "s3://ay-rmp-home/fleet_assigner/input/leg_pairings.xlsx"
    turnaround_times_file = "s3://ay-rmp-home/fleet_assigner/input/turnaround_times.csv"
    restrictions_file = "s3://ay-rmp-home/fleet_assigner/input/restrictions.csv"

    dr = DataReader(fcstdate,
                    depdates,
                    costs_file,
                    fleet_file,
                    cap_file,
                    leg_distance_file,
                    subfleet_ranges_file,
                    maintenance_file,
                    airport_allowance_file,
                    leg_pairings_file,
                    turnaround_times_file,
                    restrictions_file,
                    excel_output_writer)
    dr.read()
    print(dr.fleet_types)
    print(dr.get_duty_costs(20, 4))
    print(dr.get_duty_costs(21, 4))



