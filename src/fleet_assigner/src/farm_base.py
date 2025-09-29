import pickle
from gurobipy import *
import warnings

from defs import *
from utils import time_now
from s3utils import s3copy
from data_reader import DataReader
from lines_builder import LinesBuilder
from farm_helpers import *
from excel_output_writer import ExcelOutputWriter
from debug_info_writer import DebugInfoWriter

class CalcMode:
    FIXED = 1
    PARTIAL = 2
    FULL = 3

class FARMBase:
    """
    Class implements the base model for fleet assignment with revenue optimization.
    """
    def __init__(self,
                fcstdate,
                depdates,
                costs_file,
                fleet_file,
                cap_file,
                leg_distance_file,
                subfleet_ranges_file,
                maintenance_file,
                airport_allowance_file,
                excel_output_writer):
        self.fcstdate = fcstdate
        self.depdates = depdates
        self.costs_file = costs_file
        self.fleet_file = fleet_file
        self.cap_file = cap_file
        self.leg_distance_file = leg_distance_file
        self.subfleet_ranges_file = subfleet_ranges_file
        self.maintenance_file = maintenance_file
        self.airport_allowance_file = airport_allowance_file
        self.output_writer = output_writer

        self.dr = None
        self.subfleet_to_optimize = []

        self.y_vars = None
        self.z_vars = None
        self.v_vars = None
        self.w_vars = None

        self.num_constrs = 0
        self.constr_name2id = {}

        self.fixed_y_vars = {}

    def set_subfleet_to_optimize(self, subfleet_to_optimize):
        self.subfleet_to_optimize = subfleet_to_optimize

    def load_data(self):
        self.dr = DataReader(self.fcstdate,
                             self.depdates,
                             self.costs_file,
                             self.fleet_file,
                             self.cap_file,
                             self.leg_distance_file,
                             self.subfleet_ranges_file,
                             self.maintenance_file,
                             self.airport_allowance_file,
                             self.output_writer)
        self.dr.read()

    def save_data(self):
        fname = "../output/data.pkl"
        with open(fname, "wb") as f:
            pickle.dump(self.dr, f)

    def load_data_from_pickle(self):
        fname = "../output/data.pkl"
        with open(fname, "rb") as f:
            self.dr = pickle.load(f)

    def create_variables(self):
        """
        Creates variables for the model.
        """
        num_duties = self.dr.get_num_duties()
        num_fleet_types = self.dr.get_num_fleet_types()
        num_products = self.dr.get_num_products()

        self.y_vars = self.model.addMVar((num_duties, num_fleet_types), vtype=GRB.BINARY, name="y")

        z_lb = np.zeros(num_products)
        z_ub = np.zeros(num_products)
        for j in range(num_products):
            d = self.dr.get_demand(j)
            if d <= EPS:
                z_ub[j] = 0
            else:
                z_ub[j] = self.dr.get_demand(j)
        self.z_vars = self.model.addMVar(num_products, lb=z_lb, ub=z_ub, vtype=GRB.CONTINUOUS, name="z")

    def set_leg_capacities_constr(self):
        """
        Sets leg capacities constraints.
        """
        A = getA(self.dr)
        fcap = self.dr.rm_model["fcap"]
        cap = self.dr.rm_model["cap"]
        assert len(cap) == len(fcap)

        b = fcap - cap  # Bookings.

        nrows = len(cap)
        assert len(self.dr.rm_model["rsrc_names"]) == nrows

        # Right-hand side constraints.
        rhs = [0] * len(fcap)
        for nrow in range(nrows):
            rsrc_name = self.dr.rm_model["rsrc_names"][nrow]
            i = self.dr.get_leg_id_by_rsrc_name(rsrc_name)
            d = self.dr.get_duty_id_by_leg_id(i)
            l = self.dr.get_cmpt_id(rsrc_name)

            if d is None:
                pass
            else:
                for k in range(self.dr.get_num_fleet_types()):
                    assert b[nrow] >= 0
                    c = self.dr.get_capacity(k, l)
                    if c < b[nrow]:
                        print("bookings more than capacity.")
                    else:
                        rhs[nrow] += (c - b[nrow]) * self.y_vars[(d, k)]

        lhs = (A @ self.z_vars)
        for nrow in range(nrows):
            name = "leg_capacities_{}".format(nrow)
            self.model.addConstr(lhs[nrow] <= rhs[nrow], name=name)
            self.constr_name2id[name] = self.num_constrs
            self.num_constrs += 1

    def set_demand_constr(self):
        """
        Sets demand constraints.
        """
        # Demand constraints 0 <= z <= d set when variables are defined.
        pass

    def set_duty_coverage(self):
        """
        Sets duty coverage constraints.
        """
        for d in range(self.dr.get_num_duties()):
            constr = sum([self.y_vars[(d, k)] for k in range(self.dr.get_num_fleet_types())])
            name = "duty_coverage_y_{}".format(d)
            self.model.addConstr(constr <= 1, name=name)
            self.constr_name2id[name] = self.num_constrs
            self.num_constrs += 1

    def set_aircraft_types_constr(self):
        """
        Sets fleet limits constraints.
        """
        T = self.dr.get_num_time_indices()
        K = self.dr.get_num_fleet_types()
        D = self.dr.get_num_duties()

        Alpha = np.zeros((T, D))
        for t in range(1, T):
            for d in range(D):
                Alpha[(t, d)] = self.dr.get_alpha(d, t)

        M = np.zeros((T, K))
        for t in range(1, T):
            for k in range(K):
                M[(t, k)] = self.dr.get_num_aircrafts(k, t)

        name = "aircraft_types_constraints"
        self.model.addConstr(Alpha @ self.y_vars <= M, name="aircraft_types_constraints")
        self.constr_name2id[name] = self.num_constrs
        self.num_constrs += 1

    def set_fleet_range_constr(self):
        """
        Sets fleet range constraints.
        """
        for d in range(self.dr.get_num_duties()):
            duty = self.dr.duties[d]
            max_dist = -np.inf
            for leg_id in duty:
                orgn, dstn, _, _, _, _, _ = self.dr.legs[leg_id]
                dist_df = self.dr.leg_distance_df[
                    (self.dr.leg_distance_df["ORGN"] == orgn) &
                    (self.dr.leg_distance_df["DESTINATION"] == dstn)
                ]
                if dist_df.shape[0] == 0:
                    warnings.warn("{} {} in leg_distances.csv is not found.")
                else:
                    dist = dist_df["DISTANCE"].iloc[0]
                max_dist = max(max_dist, dist)
            assert max_dist > -np.inf
            for k in range(self.dr.get_num_fleet_types()):
                fleet_type = self.dr.fleet_types[k]
                dist_range_df = self.dr.subfleet_range_df[
                    self.dr.subfleet_range_df["SUBFLEET"] == fleet_type
                ]
                assert dist_range_df.shape[0] > 0, "Fleet type {} is not found in subfleet_range_df".format(fleet_type)
                dist_range = dist_range_df["MAX_RANGE"].iloc[0]

    def set_airport_allowance_constr(self):
        """
        Sets airport allowance constraints, i.e. which airports
        are allowed to fly by which aircraft type.
        """
        for d in range(self.dr.get_num_duties()):
            # Determine airports.
            duty = self.dr.duties[d]
            airports = set()
            for i in duty:
                orgn, dstn = self.dr.legs[i][0], self.dr.legs[i][1]
                if orgn != "HEL":
                    airports.add(orgn)
                if dstn != "HEL":
                    airports.add(dstn)

            # TODO: it is unclear how to handle many airports.
            if len(airports) > 1:
                continue
            airport = list(airports)[0]

            # Apply airport allowance constraints.
            for k in range(self.dr.get_num_fleet_types()):
                at = self.dr.fleet_types[k]
                df = self.dr.airport_allowance_df[
                    (self.dr.airport_allowance_df["AIRPORT"] == airport) &
                    (self.dr.airport_allowance_df["AT"] == at)
                ]
                if df.shape[0] == 0:
                    self.fix_y_var(d, k, 0, "airport_allowance_{}_{}".format(d, k))

    def fix_y_var(self, d, k, val, reason=""):
        """
        Fixes y variable, i.e. sets it to zero or none.
        """
        assert val == 0 or val == 1
        self.fixed_y_vars[(d, k)] = (val, reason)

        constr = self.y_vars[(d, k)]
        name = "fixed_variable_y_{}_{}".format(d, k)
        self.model.addConstr(constr == val, name=name)
        self.constr_name2id[name] = self.num_constrs
        self.num_constrs += 1

if __name__ == "__main__":
    excel_output_writer = ExcelOutputWriter("../output/fleet_assigner.xlsx")
    debug_info_writer = DebugInfoWriter("../output/")
    month = "december2023"

    mode = CalcMode.FULL
    fcstdate = "20230801"
    depdates = ["20231201", "20231202", "20231203", "20231204", "20231205", "20231206", "20231207",
                "20231208", "20231209", "20231210", "20231211", "20231212", "20231213", "20231214",
                "20231215", "20231216", "20231217", "20231218", "20231219", "20231220", "20231221",
                "20231222", "20231223", "20231224", "20231225", "20231226", "20231227", "20231228",
                "20231229", "20231230", "20231231"]
    costs_file = "s3://ay-emr-job/fleet_assigner/{}/costs.csv".format(month)
    fleet_file = "s3://ay-emr-job/fleet_assigner/{}/aircraft_inventory.csv".format(month)
    cap_file = "s3://ay-emr-job/fleet_assigner/{}/subfleet_capacities.csv".format(month)
    leg_distance_file = "s3://ay-emr-job/fleet_assigner/{}/leg_distances.csv".format(month)
    subfleet_ranges_file = "s3://ay-emr-job/fleet_assigner/{}/subfleet_ranges.csv".format(month)
    maintenance_file = "s3://ay-emr-job/fleet_assigner/{}/W23_dec_190923.ssim".format(month)
    airport_allowance_file = "s3://ay-emr-job/fleet_assigner/{}/airport_allowance.csv".format(month)

    farm_base = FARMBase(fcstdate,
                          depdates,
                          costs_file,
                          fleet_file,
                          cap_file,
                          leg_distance_file,
                          subfleet_ranges_file,
                          maintenance_file,
                          airport_allowance_file,
                          excel_output_writer)
    farm_base.load_data_from_pickle()
    if mode == "CalcMode.FIXED":
        subfleet = []
        suffix = "fixed"
    elif mode == CalcMode.PARTIAL:
        subfleet = ["319", "320", "321", "32B", "E90"]
        suffix = "partial"
    elif mode == CalcMode.FULL:
        subfleet = ["319", "320", "321", "32B", "E90"]
        suffix = "partial"
    else:
        assert False

    farm_base.set_subfleet_to_optimize(subfleet)
