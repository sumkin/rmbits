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


class FARM2PhaseModel:
    """
    Class implements the model using matrix-friendly API.
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
                 excel_output_writer,
                 debug_info_writer):
        self.fcstdate = fcstdate
        self.depdates = depdates 
        self.costs_file = costs_file
        self.fleet_file = fleet_file
        self.cap_file = cap_file
        self.leg_distance_file = leg_distance_file
        self.subfleet_ranges_file = subfleet_ranges_file
        self.maintenance_file = maintenance_file
        self.airport_allowance_file = airport_allowance_file
        self.excel_output_writer = excel_output_writer
        self.debug_info_writer = debug_info_writer

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
                             self.excel_output_writer)
        self.dr.read()

    def save_data(self):
        fname = "../output/data.pkl"
        with open(fname, "wb") as f:
            pickle.dump(self.dr, f)

    def load_data_from_pickle(self):
        fname = "../output/data.pkl"
        with open(fname, "rb") as f:
            self.dr = pickle.load(f)

    def print_indices_bounds(self):
        print("M = {}".format(len(self.dr.legs)))
        print("D = {}".format(self.dr.get_num_duties())) 
        print("N = {}".format(self.dr.get_num_products()))
        print("K = {}".format(self.dr.get_num_fleet_types()))
        print("L = 2")
        print("T = {}".format(len(self.dr.ts)))

    def create_variables(self):
        """
        Creates variables for the model.
        """
        num_duties = self.dr.get_num_duties()
        num_fleet_types = self.dr.get_num_fleet_types()
        num_products = self.dr.get_num_products()

        self.y_vars = self.model.addMVar((num_duties, num_fleet_types),
                                         vtype=GRB.BINARY,
                                         name="y")
        
        z_lb = np.zeros(num_products)
        z_ub = np.zeros(num_products)
        for j in range(num_products):
            d = self.dr.get_demand(j)
            if d <= EPS:
                z_ub[j] = 0
            else:
                z_ub[j] = self.dr.get_demand(j)
        self.z_vars = self.model.addMVar(num_products,
                                         lb=z_lb,
                                         ub=z_ub,
                                         vtype=GRB.CONTINUOUS,
                                         name="z")

        self.w_vars = self.model.addMVar(num_duties, vtype=GRB.BINARY, name="w")

        self.v_vars = self.model.addMVar((num_duties, num_fleet_types),
                                         vtype=GRB.BINARY,
                                         name="v")

    def set_objective_phase_1(self):
        """
        Sets objectivea as sum of non-cancelled duties.
        """
        print("\t", time_now(), "Settting sum of non-cancelled duties...")
        self.obj = sum(self.w_vars)

        self.model.setObjective(self.obj, GRB.MAXIMIZE)

    def set_objective_phase_2(self):
        """
        Sets objective as difference between revenue and costs.
        """
        print("\t", time_now(), "Setting revenue...")
        num_products = self.dr.get_num_products()
        fares = np.array([self.dr.get_fare(j) for j in range(num_products)])
        self.obj = fares @ self.z_vars

        print("\t", time_now(), "Setting costs...")
        num_duties = self.dr.get_num_duties()
        num_fleet_types = self.dr.get_num_fleet_types()
        costs = np.array([
            self.dr.get_duty_costs(d, k)
            for d in range(num_duties)
            for k in range(num_fleet_types)
        ]).reshape((num_duties, num_fleet_types))
        self.obj -= sum(sum(costs * self.v_vars))

        self.model.setObjective(self.obj, GRB.MAXIMIZE)
        
    def set_leg_capacities_constr(self):
        """
        Sets leg capacities constraints.
        """

        A = getA(self.dr)
        fcap = self.dr.rm_model["fcap"]
        cap = self.dr.rm_model["cap"]
        assert len(cap) == len(fcap)

        b = fcap - cap # Bookings.

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
                        # Current number of bookings is more than
                        # capacity of aircraft.
                        # Set corresponding variable to zero.
                        # TODO: how to handle overbooking. This may
                        # contradicts to other constraints,
                        # e.g. subfleet optimization.
                        pass
                    else:
                        rhs[nrow] += (c - b[nrow]) * self.v_vars[(d, k)]

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
        pass

    def set_duty_coverage(self):
        """
        Sets duty coverage constraints.
        """

        for d in range(self.dr.get_num_duties()):
            # For y variable.
            #constr = sum([self.y_vars[(d, k)] for k in range(self.dr.get_num_fleet_types())])
            #name = "duty_coverage_y_{}".format(d)
            #self.model.addConstr(constr <= 1, name=name)
            #self.constr_name2id[name] = self.num_constrs
            #self.num_constrs += 1

            # For v variable.
            constr = -self.w_vars[d]
            constr += sum([
                self.v_vars[(d, k)] for k in range(self.dr.get_num_fleet_types())
            ])
            name = "duty_coverage_v_{}".format(d)
            self.model.addConstr(constr == 0, name=name)
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
                Alpha[t, d] = self.dr.get_alpha(d, t)

        M = np.zeros((T, K))
        for t in range(1, T):
            for k in range(K):
                M[(t, k)] = self.dr.get_num_aircrafts(k, t)

        name = "aircraft_types_constraints"
        self.model.addConstr(Alpha @ self.v_vars <= M, name=name)
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
                orgn, dstn, _, _, _, _, _, _ = self.dr.legs[leg_id]
                dist_df = self.dr.leg_distance_df[
                    (self.dr.leg_distance_df["ORIGIN"] == orgn) &
                    (self.dr.leg_distance_df["DESTINATION"] == dstn)
                ]
                if dist_df.shape[0] == 0:
                    warnings.warn(f"{orgn} {dstn} in leg_distances.csv is not found.")
                    dist = 0
                else:
                    dist = dist_df["DISTANCE"].iloc[0]
                max_dist = max(max_dist, dist)
            assert max_dist > -np.inf
            for k in range(self.dr.get_num_fleet_types()):
                fleet_type = self.dr.fleet_types[k]
                dist_range_df = self.dr.subfleet_range_df[
                    self.dr.subfleet_range_df["SUBFLEET"] == fleet_type
                ]
                assert dist_range_df.shape[0] > 0, \
                       f"Fleet type {fleet_type} is not found in subfleet_range_df."
                dist_range = dist_range_df["MAX_RANGE"].iloc[0]
                if max_dist > dist_range:
                    self.fix_y_var(d, k, 0, "subfleet range")

    def set_fixed_fleet_types_constr(self):
        """
        Sets fleet types to value found in inventory file.
        """
        for d in range(self.dr.get_num_duties()):
            at = self.dr.duty2at[d]                 # Aircraft type.
            at_ind = self.dr.fleet_types.index(at)  # Aircraft type index.
            if at in self.dr.fleet_types:
                if at not in self.subfleet_to_optimize:
                    for k in range(self.dr.get_num_fleet_types()):
                        if (d, k) not in self.fixed_y_vars.keys():
                            if at_ind == k:
                                self.fix_y_var(d, k, 1, "subfleet to optimize")
                            else:
                                self.fix_y_var(d, k, 0, "subfleet to optimize")
            else:
                print("at = {}".format(at))
                print("self.dr.fleet_types = {}".format(self.dr.fleet_types))
                print("")
                assert False

    def set_relation_yvw_constr(self):
        """
        Sets relation among y,v,w variables constraints.
        """
        for d in range(self.dr.get_num_duties()):
            for k in range(self.dr.get_num_fleet_types()):
                """
                constr = self.v_vars[(d, k)] - self.w_vars[d]
                name = "relation_v_w_{}_{}".format(d, k)
                self.model.addConstr(constr <= 0, name=name)
                self.constr_name2id[name] = self.num_constrs
                self.num_constrs += 1
                """

                constr = self.v_vars[(d,k)] - self.y_vars[(d,k)]
                name = "relation_v_y_{}_{}".format(d, k)
                self.model.addConstr(constr <= 0, name=name)
                self.constr_name2id[name] = self.num_constrs
                self.num_constrs += 1

    def set_airport_allowance_constr(self):
        """
        Sets airport allowance constraints, i.e. which airprots
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
                        self.fix_y_var(d, k, 0, "airport allowance")

    def set_w_equality_constr(self, num_non_cancelled_duties):
        """
        Sets equality constraints for number of non cancelled duties.
        """
        constr = 0 
        for d in range(self.dr.get_num_duties()):
            constr += self.w_vars[d]
        name = "non_cancelled_duties"
        self.model.addConstr(constr >= num_non_cancelled_duties - 1, name=name)
        self.constr_name2id[name] = self.num_constrs
        self.num_constrs += 1

    def set_constraints_phase_1(self):
        """
        Sets constraints.
        """
        print("\t", time_now(), "Setting leg capacities constraints...")
        self.set_leg_capacities_constr()
        print("\t", time_now(), "Setting demand constraints...")
        self.set_demand_constr()
        print("\t", time_now(), "Setting duty coverage constraints...")
        self.set_duty_coverage()
        print("\t", time_now(), "Setting aircraft types constraints...")
        self.set_aircraft_types_constr()
        print("\t", time_now(), "Setting fleet range constraints...")
        self.set_fleet_range_constr()
        print("\t", time_now(), "Setting fixed fleet_types constraints...")
        self.set_fixed_fleet_types_constr()
        print("\t", time_now(), "Setting relation for y,v,w variables constraints...")
        self.set_relation_yvw_constr()
        print("\t", time_now(), "Setting airport allowance constraints...")
        self.set_airport_allowance_constr()

    def set_constraints_phase_2(self):
        """
        Sets constraints.
        """
        print("\t", time_now(), "Setting leg capacities constraints...")
        self.set_leg_capacities_constr()
        print("\t", time_now(), "Setting demand constraints...")
        self.set_demand_constr()
        print("\t", time_now(), "Setting duty coverage constraints...")
        self.set_duty_coverage()
        print("\t", time_now(), "Setting aircraft types constraints...")
        self.set_aircraft_types_constr()
        print("\t", time_now(), "Setting fleet range constraints...")
        self.set_fleet_range_constr()
        print("\t", time_now(), "Setting fixed fleet_types constraints...")
        self.set_fixed_fleet_types_constr()
        print("\t", time_now(), "Setting relation for y,v,w variables constraints...")
        self.set_relation_yvw_constr()
        print("\t", time_now(), "Setting w equality constraints...")
        #self.set_w_equality_constr(num_non_cancelled_duties)

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

    def build_model_phase_1(self):
        # Reset fixed variables.
        self.fixed_y_var = {}

        # Create model.
        self.model = Model("farm_phase_1")

        # Create variables.
        print(time_now(), "Creating variables...")
        self.create_variables()

        # Set objective.
        print(time_now(), "Setting objective...")
        self.set_objective_phase_1()

        # Set constraints.
        print(time_now(), "Setting constraints...")
        self.set_constraints_phase_1()

        self.model.update()

    def build_model_phase_2(self):
        # Reset fixed variables.
        self.fixed_y_var = {}
        self.num_constrs = 0
        self.constr_name2id = {}

        # Create model.
        self.model = Model("farm_phase_2")

        # Create variables.
        print(time_now(), "Creating variables...")
        self.create_variables()

        # Set objective.
        print(time_now(), "Setting objective...")
        self.set_objective_phase_2()

        # Set constraints.
        print(time_now(), "Setting constraints...")
        self.set_constraints_phase_2()

        self.model.update()

        #self.excel_output_writer.write_fixed_y_var_df(self.fixed_y_var)

    def set_mip_start(self):
        num_duties = self.dr.get_num_duties()
        num_fleet_types = self.dr.get_num_fleet_types()
        num_products = self.dr.get_num_products()

        y, z, w, v = self.dr.get_solution_from_inv_df()

        #
        # Check feasibility.
        #
        T = self.dr.get_num_time_indices()
        K = self.dr.get_num_fleet_types()
        D = self.dr.get_num_duties()

        Alpha = np.zeros((T, D))
        for t in range(1, T):
            for d in range(D):
                Alpha[t, d] = self.dr.get_alpha(d, t)

        M = np.zeros((T, K))
        for t in range(1, T):
            for k in range(K):
                M[(t, k)] = self.dr.get_num_aircrafts(k, t)

        # Aircraft types constraints.
        def check_aircraft_types_constr(start_t=1):
            for t in range(start_t, T):
                for k in range(K):
                    lhs = sum([Alpha[(t, d)] * v[(d, k)] for d in range(D)])
                    rhs = M[(t, k)]
                    if lhs > rhs:
                        # Find duty to cancel.
                        for dp in range(D):
                            if Alpha[(t, dp)] != 0 and w[dp] != 0:
                                # Found. Cancel it.
                                for kp in range(K):
                                    v[(dp, kp)] = 0
                                w[dp] = 0
                                print(t, T)
                                return False, t
            return True, 0

        fixed = False
        start_t = 1
        while not fixed:
            fixed, start_t = check_aircraft_types_constr(start_t)
            print("Check aircraft types constraints: duty cancelled.")

        # Set fixed y var constraints.
        def check_fix_y_var_constr():
            for d in range(D):
                for k in range(K):
                    if (d, k) in self.fixed_y_var.keys():
                        val, reason = self.fixed_y_var[(d, k)]
                        if y[(d, k)] != val:
                            # Cancel duty.
                            for kp in range(K):
                                v[(d, kp)] = 0
                            w[d] = 0
                            y[(d, k)] = val
                            if val == 1:
                                # Make all other values zero.
                                for kp in range(K):
                                    y[(d, kp)] = 0
                            return False
            return True

        fixed = False
        while not fixed:
            fixed = check_fix_y_var_constr()
            print("Check fix y var constraints: duty cancelled.")

        # Fill start solution.
        constrs_to_remove = []
        constrs_name_to_remove = []
        for d in range(num_duties):
            for k in range(num_fleet_types):
                if (d, k) in self.fixed_y_var.keys():
                    # Variable is fixed.
                    if self.fixed_y_var[(d, k)][0] != y[(d, k)]:
                        # Remove corresponding constraint.
                        # But keep variable in fixed variable,
                        # because it is needed in second phase.
                        name = "fixed_variable_y_{}_{}".format(d, k)
                        num_constrs = len(self.model.getConstrs())
                        constr_id = self.constr_name2id[name]
                        assert constr_id < num_constrs, \
                               "id = {}, num_constrs = {}".format(constr_id,
                                                                  num_constrs)
                        constrs_to_remove.append(constr_id)
                        constrs_name_to_remove.append(name)
                self.y_vars[(d, k)].Start = y[(d, k)]

        for j in range(num_products):
            self.z_vars[j].Start = z[j]

        for d in range(num_duties):
            self.w_vars[d].Start = w[d]

        for d in range(num_duties):
            for k in range(num_fleet_types):
                self.v_vars[(d, k)].Start = v[(d, k)]

        constrs_to_remove.sort(reverse=True)
        for constr_id in constrs_to_remove:
            constr = self.model.getConstrs()[constr_id]
            self.model.remove(constr)

        self.model.update()

    def read_mip_start_from_file(self, fname):
        self.model.read(fname)

    def solve(self):
        self.model.setParam("Presolve", 2)
        self.model.setParam("MIPGap", 0.05)
        #self.model.setParam("Heuristics", 0.5)
        self.model.setParam("MIPFocus", 2)
        self.model.setParam("TimeLimit", 3000)
        self.model.optimize()
        if self.model.status == GRB.INFEASIBLE:
            self._debug_print_aircraft_types_constr()
            assert False
        print("Objective = {}".format(self.model.objVal))

    def save_to_file(self, fname):
        self.model.write(fname)

    def get_solution_phase_1(self):
        num_duties = self.dr.get_num_duties()
        res = 0 
        for d in range(num_duties):
            res += self.w_vars[d].getAttr("x")        
        return res

    def get_solution_phase_2(self):
        num_products = self.dr.get_num_products()
        num_non_zero = 0
        for j in range(num_products):
            varval = self.z_vars[j].getAttr("x")
            if varval != 0:
                num_non_zero += 1 

        self.sol = {}
        for d in range(self.dr.get_num_duties()):
            for k in range(self.dr.get_num_fleet_types()):
                varval = self.v_vars[d, k].getAttr("x")
                if varval == 1:
                    assert d not in self.sol.keys()
                    self.sol[d] = k

    def revenue(self):
        """
        Calculates revenue corresponding to solution.
        """

        # Calculate remained revenue corresponding to solution.
        num_products = self.dr.get_num_products()
        z = np.zeros(num_products)
        fares = np.zeros(num_products)
        for j in range(num_products):
            varval = self.z_vars[j].getAttr("x")
            z[j] = varval
            fares[j] = self.dr.get_fare(j)
        remained_revenue = fares @ z 

        # Calculate booked revenue.
        booked_revenue = self.dr.get_booked_revenue()
        print("Remained revenue = {}".format(remained_revenue))
        print("Booked revenue = {}".format(booked_revenue))
        return remained_revenue + booked_revenue

    def costs(self):
        """
        Calculates costs corresponding to solution.
        """
        num_duties = self.dr.get_num_duties()
        num_fleet_types = self.dr.get_num_fleet_types()
        v = np.zeros((num_duties, num_fleet_types))
        for d in range(num_duties):
            sumvarval = 0.0
            for k in range(num_fleet_types):
                varval = self.v_vars[(d, k)].getAttr("x")
                v[(d, k)] = varval
                sumvarval += varval 
                assert abs(varval) <= EPS or abs(varval - 1) <= EPS, \
                       "varval = {}".format(varval)
            assert abs(sumvarval) <= EPS or abs(sumvarval - 1) <= EPS 
        costs = np.array([
            self.dr.get_duty_costs(d, k)
            for d in range(num_duties)
            for k in range(num_fleet_types)
        ]).reshape((num_duties, num_fleet_types))
        return sum(sum(costs * v))

    def get_num_non_cancelled_duties(self):
        num_duties = self.dr.get_num_duties()
        num_non_cancelled = 0
        for d in range(num_duties):
            var_val = self.w_vars[d].getAttr("x")
            if abs(var_val - 1) < EPS:
                num_non_cancelled += 1
        return num_non_cancelled

    def _debug_print_aircraft_types_constr(self):
        K = self.dr.get_num_fleet_types()
        T = self.dr.get_num_time_indices()
        for k in range(K):
            at = self.dr.fleet_types[k]
            max_fixed_sum = 0 
            min_M = np.inf 
            for t in range(1, T):
                M = self.dr.get_num_aircrafts(k, t)
                fixed_sum = 0
                for d in range(self.dr.get_num_duties()):
                    duty_start, duty_end = self.dr.duties2startend[d]
                    t_min, t_max = self.dr.ts[t-1], self.dr.ts[t]
                    if max(t_min, duty_start) <= min(t_max, duty_end):
                        if (d, k) in self.fixed_y_var.keys():
                            val = self.fixed_y_var[(d, k)][0]
                            assert val == 0 or val == 1
                            fixed_sum += val 
                max_fixed_sum = max(fixed_sum, max_fixed_sum)
                min_M = min(M, min_M)
            if max_fixed_sum > min_M:
                print(k, at, min_M, max_fixed_sum)

    def _debug_print_fixed_y_vars(self):
        num_duties = self.dr.get_num_duties()
        num_fleet_types = self.dr.get_num_fleet_types()
        print("Number of y vars = {}".format(num_duties * num_fleet_types))
        print("Number of fixed y vars = {}".format(len(self.fixed_y_var.keys())))

    def _debug_write_fleet_availability_diagram(self):
        self.debug_info_writer.write_fleet_availability_diagram(self.dr)


if __name__ == "__main__":
    excel_output_writer = ExcelOutputWriter("../output/fleet_assigner.xlsx")
    debug_info_writer = DebugInfoWriter("../output/")
    month = "december2024"
    
    mode = CalcMode.FULL
    fcstdate = "20240715"
    depdates = ["20241201", "20241202", "20241203", "20241204", "20241205",
                "20241206", "20241207", "20241208", "20241209", "20241210",
                "20241211", "20241212", "20241213", "20241214", "20241215",
                "20241216", "20241217", "20241218", "20241219", "20241220",
                "20241221", "20241222", "20241223", "20241224", "20241225",
                "20241226", "20241227", "20241228", "20241229", "20241230",
                "20241231"]
    costs_file = \
        "s3://ay-emr-job/fleet_assigner/{}/costs.csv".format(month)
    fleet_file = \
        "s3://ay-emr-job/fleet_assigner/{}/aircraft_inventory.csv".format(month)
    cap_file = \
        "s3://ay-emr-job/fleet_assigner/{}/subfleet_capacities.csv".format(month)
    leg_distance_file = \
        "s3://ay-emr-job/fleet_assigner/{}/leg_distances.csv".format(month)
    subfleet_ranges_file = \
        "s3://ay-emr-job/fleet_assigner/{}/subfleet_ranges.csv".format(month)
    maintenance_file = \
        "s3://ay-emr-job/fleet_assigner/{}/W23_dec_190923.ssim".format(month)
    airport_allowance_file = \
        "s3://ay-emr-job/fleet_assigner/{}/airport_allowance.csv".format(month)

    farm = FARM2PhaseModel(fcstdate,
                           depdates,
                           costs_file,
                           fleet_file,
                           cap_file,
                           leg_distance_file,
                           subfleet_ranges_file,
                           maintenance_file,
                           airport_allowance_file,
                           excel_output_writer,
                           debug_info_writer)
    farm.load_data()
    #farm.save_data()
    #farm.load_data_from_pickle()
    #farm.debug_info_writer.write_fleet_availability_diagram(farm.dr)
    if mode == CalcMode.FIXED:
        subfleet = []
        suffix = "fixed"
    elif mode == CalcMode.PARTIAL:
        subfleet = ["319", "320", "321", "32B", "E90"]
        suffix = "partial"
    elif mode == CalcMode.FULL:
        subfleet = farm.dr.fleet_types
        suffix = "optimized"
    else:
        assert False

    farm.set_subfleet_to_optimize(subfleet)

    # Solve phase 1.
    farm.build_model_phase_1()
    farm.set_mip_start()
    farm.solve()
    num_non_cancelled_duties = farm.get_solution_phase_1()
    #farm.save_to_file("../output/farm_phase1_{}.sol".format(suffix))

    # Solve phase 2.
    farm.build_model_phase_2()
    #farm.save_to_file("../output/farm_{}.lp".format(suffix))
    #farm.read_mip_start_from_file("../output/farm_phase1_{}.sol".format(suffix))
    #farm.set_mip_start()
    farm.solve()
    farm.get_solution_phase_2()

    revenue = farm.revenue()
    costs = farm.costs()

    lb = LinesBuilder(depdates,
                      farm.dr.legs,
                      farm.dr.duties, 
                      farm.sol, 
                      farm.dr.fleet_types, 
                      farm.dr.fleet_type2fleet_ids, 
                      farm.dr.leg2duty,
                      farm.dr,
                      excel_output_writer)
    lb.build()
    lb.write_csv("../output/lines_{}.csv".format(suffix))

    # Upload output files to s3.
    s3copy("../output/lines_{}.csv".format(suffix),
           "s3://ay-emr-job/fleet_assigner/{}/output/lines_{}.csv".format(month, suffix))
    s3copy("../output/fleet_assigner.xlsx",
           "s3://ay-emr-job/fleet_assigner/{}/output/fleet_assigner.xlsx".format(month))

    #num_non_cancelled_duties = farm.get_num_non_cancelled_duties()

    print("num_duties = {}".format(farm.dr.get_num_duties()))
    print("num_non_cancelled_duties = {}".format(farm.get_num_non_cancelled_duties()))
    print("Revenue = {}".format(revenue))
    print("Costs = {}".format(costs))
    print("Profit = {}".format(revenue - costs))


