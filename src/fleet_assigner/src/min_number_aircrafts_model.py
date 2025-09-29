import numpy as np
import os
import uuid
from gurobipy import *
import warnings

from defs import *
from utils import time_now
from data_reader import DataReader
from excel_output_writer import ExcelOutputWriter
from debug_info_writer import DebugInfoWriter
from optimization_status_handler import OptimizationStatusHandler
from s3utils import s3copy

class MinNumberAircraftsModel:
    """
    Class implements the model, which calculates
    the minimum number of required aircrafts.
    """

    def __init__(self,
                 uuid,
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
                 optimization_status_handler,
                 excel_output_writer,
                 debug_info_writer):
        self.fcstdate = fcstdate
        self.depdates = depdates
        self.costs_file = costs_file
        self.fleet_file = fleet_file
        self.cap_file = cap_file
        self.leg_distance_file = leg_distance_file
        self.turnaround_times_file = turnaround_times_file
        self.subfleet_ranges_file = subfleet_ranges_file
        self.maintenance_file = maintenance_file
        self.airport_allowance_file = airport_allowance_file
        self.leg_pairings_file = leg_pairings_file
        self.optimization_status_handler = optimization_status_handler
        self.excel_output_writer = excel_output_writer
        self.debug_info_writer = debug_info_writer

        self.dr = None

        self.y_vars = None
        self.z_vars = None

        self.num_constrs = 0
        self.constr_name2id = {}

        self.fixed_y_vars = {}

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
                             self.leg_pairings_file,
                             self.turnaround_times_file,
                             self.excel_output_writer)
        self.dr.read()

    def create_variables(self):
        """
        Creates variables for the model.
        """
        num_duties = self.dr.get_num_duties()
        num_fleet_types = self.dr.get_num_fleet_types()
        num_products = self.dr.get_num_products()
        num_time_indices = self.dr.get_num_time_indices()

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

        m_lb = np.zeros((num_fleet_types, num_time_indices))
        self.m_vars = self.model.addMVar((num_fleet_types, num_time_indices),
                                         lb=m_lb,
                                         vtype=GRB.INTEGER,
                                         name="m")

        m_max_lb = np.zeros(num_fleet_types)
        self.m_max_vars = self.model.addMVar(num_fleet_types, lb=m_max_lb, vtype=GRB.INTEGER, name="m_max")

    def set_objective(self):
        """
        Sets the objective.
        """
        K = self.dr.get_num_fleet_types()
        self.obj = 0
        for k in range(K):
            self.obj += self.m_max_vars[k]
        self.model.setObjective(self.obj, GRB.MINIMIZE)

    def set_duty_coverage(self):
        """
        Sets duty coverage constraints.
        """
        for d in range(self.dr.get_num_duties()):
            constr = sum([self.y_vars[(d, k)] for k in range(self.dr.get_num_fleet_types())])
            name = "duty_coverage_{}".format(d)
            self.model.addConstr(constr == 1, name=name)
            self.constr_name2id[name] = self.num_constrs
            self.num_constrs += 1

    def set_aircraft_types_constr(self):
        """
        Sets fleet limit constraints.
        """
        T = self.dr.get_num_time_indices()
        K = self.dr.get_num_fleet_types()
        D = self.dr.get_num_duties()

        Alpha = np.zeros((D, T))
        for d in range(D):
            for t in range(1, T):
                Alpha[(d, t)] = self.dr.get_alpha(d, t)

        M = np.zeros((K, T))
        for k in range(K):
            for t in range(1, T):
                M[(k, t)] = self.dr.get_num_aircrafts(k, t)

        name = "aircraft_types_constraints"
        self.model.addConstr(Alpha.T @ self.y_vars <= M.T + self.m_vars.transpose(), name=name)
        self.constr_name2id[name] = self.num_constrs
        self.num_constrs += 1

    def set_fleet_range_constr(self):
        """
        Sets fleet range constraints.
        """
        for d in range(self.dr.get_num_duties()):
            # Calculate maximum leg distance for duty.
            duty = self.dr.duties[d]
            max_dist = -np.inf
            for leg_id in duty:
                orgn, dstn, _, _, _, _, _, _ = self.dr.legs[leg_id]
                dist_df = self.dr.leg_distance_df[
                    (self.dr.leg_distance_df["ORIGIN"] == orgn) &
                    (self.dr.leg_distance_df["DESTINATION"] == dstn)
                ]
                if dist_df.shape[0] == 0:
                    warnings.warn("{} {} in leg_distances.csv is not found.".format(orgn, dstn))
                    dist = 0
                else:
                    dist = dist_df["DISTANCE"].iloc[0]
                max_dist = max(max_dist, dist)
            assert max_dist > -np.inf

            # Go over aircraft types and if max leg distance exceeds range fix the variable.
            for k in range(self.dr.get_num_fleet_types()):
                fleet_type = self.dr.fleet_types[k]
                dist_range_df = self.dr.subfleet_range_df[
                    self.dr.subfleet_range_df["SUBFLEET"] == fleet_type
                ]
                assert dist_range_df.shape[0] > 0, \
                       "Fleet type {} is not found in subfleet_range_df.".format(fleet_type)
                dist_range = dist_range_df["MAX_RANGE"].iloc[0]
                if dist_range < max_dist:
                    self.fix_y_var(d, k, 0, "max_distance_range")

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
                if (d, k) not in self.fixed_y_vars.keys():
                    at = self.dr.fleet_types[k]
                    df = self.dr.airport_allowance_df[
                        (self.dr.airport_allowance_df["AIRPORT"] == airport) &
                        (self.dr.airport_allowance_df["AT"] == at)
                    ]
                    if df.shape[0] == 0:
                        self.fix_y_var(d, k, 0, "airport_allowance")

    def set_m_max_constr(self):
        """
        Sets constraints
        """
        K = self.dr.get_num_fleet_types()
        T = self.dr.get_num_time_indices()
        for k in range(K):
            for t in range(T):
                name = "m_max_constr_{}_{}".format(k, t)
                self.model.addConstr(self.m_vars[(k, t)] <= self.m_max_vars[k], name=name)
                self.constr_name2id[name] = self.num_constrs
                self.num_constrs += 1

    def set_constraints(self):
        """
        Sets constraints.
        """
        print("\t", time_now(), "Setting duty coverage constraints...")
        self.set_duty_coverage()

        print("\t", time_now(), "Setting aircraft types constraints...")
        self.set_aircraft_types_constr()

        print("\t", time_now(), "Setting fleet range constraints...")
        self.set_fleet_range_constr()

        print("\t", time_now(), "Setting airport allowance constraints...")
        self.set_airport_allowance_constr()

        print("\t", time_now(), "Setting m max cosntraints...")
        self.set_m_max_constr()

    def fix_y_var(self, d, k, val, reason=""):
        """
        Fixes y variable, i.e. sets it to zero or one.
        """
        assert val == 0 or val == 1
        self.fixed_y_vars[(d, k)] = (val, reason)

        constr = self.y_vars[(d, k)]
        name = "fixed_variable_y_{}_{}".format(d, k)
        self.model.addConstr(constr == val, name=name)
        self.constr_name2id[name] = self.num_constrs
        self.num_constrs += 1

    def build_model(self):
        # Create model.
        self.model = Model("min_number_aircrafts")

        # Create variables.
        print(time_now(), "Creating variables...")
        self.create_variables()

        # Set objective.
        print(time_now(), "Setting objective...")
        self.set_objective()

        # Set constraints.
        print(time_now(), "Setting constraints...")
        self.set_constraints()

    def solve_with_y_fixed(self):
        for d in range(self.dr.get_num_duties()):
            for k in range(self.dr.get_num_fleet_types()):
                if self.dr.duty2at[d] == k:
                    self.fix_y_var(d, k, 1)
                else:
                    self.fix_y_var(d, k, 0)
        self.model.setParam("Presolve", 2)
        self.model.setParam("MIPGap", 0.05)
        self.model.setParam("MIPFocus", 2)
        self.model.optimize()

    def solve(self):
        self.model.setParam("Presolve", 2)
        self.model.setParam("MIPGap", 0.05)
        self.model.setParam("MIPFocus", 2)
        self.model.optimize()

    def get_solution(self):
        """
        Retrieves the solution.
        """
        D = self.dr.get_num_duties()
        K = self.dr.get_num_fleet_types()
        T = self.dr.get_num_time_indices()

        y = np.zeros((D, K))
        for d in range(D):
            for k in range(K):
                val = self.y_vars[(d, k)].getAttr("x")
                y[(d, k)] = val

        m = np.zeros((K, T))
        for k in range(K):
            for t in range(T):
                val = self.m_vars[(k, t)].getAttr("x")
                m[(k, t)] = val

        return y, m

if __name__ == "__main__":
    excel_output_writer = ExcelOutputWriter("../output/min_number_aircrafts.xlsx")
    debug_info_writer = DebugInfoWriter("../output/")
    optimization_status_handler = OptimizationStatusHandler()

    opt_id = uuid.uuid4()
    month = "may2025"
    fcstdate = "20250328"
    fcstyear, fcstmonth, fcstday = fcstdate[:4], fcstdate[4:6], fcstdate[6:]
    depdates = ["20250501", "20250502", "20250503", "20250504", "20250505", "20250506", "20250507",
                "20250508", "20250509", "20250510", "20250511", "20250512", "20250513", "20250514",
                "20250515", "20250516", "20250517", "20250518", "20250519", "20250520", "20250521",
                "20250522", "20250523", "20250524", "20250525", "20250526", "20250527", "20250528",
                "20250529", "20250530", "20250531"]
    costs_file = "s3://ay-emr-job/anaplan_costs/{}/{}/{}/{}.csv".format(fcstyear, fcstmonth, fcstday, month)
    fleet_file = "s3://ay-emr-job/fleet_assigner/input/aircraft_inventory.csv"
    cap_file = "s3://ay-emr-job/fleet_assigner/input/subfleet_capacities.csv"
    leg_distance_file = "s3://ay-emr-job/fleet_assigner/input/leg_distances.csv"
    subfleet_ranges_file = "s3://ay-emr-job/fleet_assigner/input/subfleet_ranges.csv"
    maintenance_file = "s3://ay-emr-job/fleet_assigner/input/MAY.ssim"
    airport_allowance_file = "s3://ay-emr-job/fleet_assigner/input/airport_allowance.csv"
    leg_pairings_file = "s3://ay-emr-job/fleet_assigner/input/leg_pairings_MAY.xlsx"
    turnaround_times_file = "s3://ay-emr-job/fleet_assigner/input/turnaround_times.csv"

    mnam = MinNumberAircraftsModel(opt_id,
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
                                   optimization_status_handler,
                                   excel_output_writer,
                                   debug_info_writer)
    mnam.load_data()
    mnam.build_model()
    mnam.solve()
    #mnam.solve_with_y_fixed()
    y, m = mnam.get_solution()
    debug_info_writer.write_fa_diagram(month, mnam.dr, y, m)
    s3copy("../output/min_number_aircrafts.xlsx",
           "s3://ay-emr-job/fleet_assigner/{}/output/min_number_aircrafts.xlsx".format(month))