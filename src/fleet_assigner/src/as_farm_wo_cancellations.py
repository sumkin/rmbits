import os
import uuid
import pickle
import numpy as np
from scipy import sparse
import warnings
from datetime import datetime, timedelta
from pyscipopt import Model, quicksum

from defs import *
from utils import time_now
from as_data_reader import ASDataReader
from farm_helpers import *
from as_lines_builder import ASLinesBuilder

class ASFARMWoCancellations:
    """
    Class implements profit maximization without cancellations.
    """

    def __init__(self,
                 depdates,
                 inv_file,
                 costs_file,
                 fleet_file,
                 cap_file,
                 maintenance_file,
                 leg_pairings_file,
                 turnaround_times_file):
        self.depdates = depdates
        self.inv_file = inv_file
        self.costs_file = costs_file
        self.fleet_file = fleet_file
        self.cap_file = cap_file
        self.maintenance_file = maintenance_file
        self.leg_pairings_file = leg_pairings_file
        self.turnaround_times_file = turnaround_times_file

        self.dr = None
        self.y_vars = None
        self.z_vars = None
        self.num_constrs = 0
        self.constr_name2id = {}
        self.fixed_y_vars = {}

    def load_data(self):
        asdr = ASDataReader(self.depdates,
                            self.inv_file,
                            self.costs_file,
                            self.fleet_file,
                            self.cap_file,
                            self.maintenance_file,
                            self.leg_pairings_file,
                            self.turnaround_times_file)
        asdr.read()
        self.asdr = asdr

    def create_variables(self):
        """
        Creates variables for the model.
        """
        num_duties = self.asdr.get_num_duties()
        num_fleet_types = self.asdr.get_num_fleet_types()
        num_products = self.asdr.get_num_products()
        num_time_indices = self.asdr.get_num_time_indices()

        # Assignment variables - binary matrix.
        self.y_vars = {}
        for d in self.asdr.duty_ids:
            for k in range(num_fleet_types):
                var_name = f"y_{d}_{k}"
                self.y_vars[(d, k)] = self.model.addVar(vtype="B", name=var_name)

        # Revenue variables - continuous.
        self.z_vars = []
        for j in range(num_products):
            d = self.asdr.get_demand(j)
            if d <= EPS:
                z_ub = 0
            else:
                z_ub = self.asdr.get_demand(j)
            var_name = f"z_{j}"
            self.z_vars.append(self.model.addVar(lb=0, ub=z_ub, vtype="C", name=var_name))

        # Change variables - binary matrix.
        self.s_vars = {}
        for d in self.asdr.duty_ids:
            for k in range(num_fleet_types):
                var_name = f"s_{d}_{k}"
                self.s_vars[(d, k)] = self.model.addVar(vtype="B", name=var_name)

        if self.min_extra_planes:
            self.m_vars = {}
            for k in range(num_fleet_types):
                for t in range(num_time_indices):
                    var_name = f"m_{k}_{t}"
                    self.m_vars[(k, t)] = self.model.addVar(lb=0, vtype="I", name=var_name)

            self.m_max_vars = []
            for k in range(num_fleet_types):
                var_name = f"m_max_{k}"
                self.m_max_vars.append(self.model.addVar(lb=0, vtype="I", name=var_name))

    def set_objective(self):
        """
        Sets the objective of optimization.
        """
        if self.min_extra_planes:
            K = self.asdr.get_num_fleet_types()
            obj_expr = quicksum(self.m_max_vars[k] for k in range(K))
            self.model.setObjective(obj_expr, "minimize")
        else:
            num_products = self.asdr.get_num_products()
            num_duties = self.asdr.get_num_duties()
            num_fleet_types = self.asdr.get_num_fleet_types()

            # Revenue part
            #revenue_expr = quicksum(
            #    self.asdr.get_fare(j) * self.z_vars[j]
            #    for j in range(num_products)
            #)

            revenue_terms = [self.asdr.get_fare(j) * self.z_vars[j] for j in range(num_products)]
            revenue_expr = quicksum(revenue_terms)

            # Cost part
            cost_expr = quicksum(
                self.asdr.get_duty_costs(d, k) * self.y_vars[(d, k)]
                for d in self.asdr.duty_ids
                for k in range(num_fleet_types)
            )

            # Profit = Revenue - Costs
            self.model.setObjective(revenue_expr - cost_expr, "maximize")

    def set_leg_capacities_constr(self):
        """
        Sets leg capacities constraints.
        """
        A = getA(self.asdr).tocsr()
        fcap = self.asdr.rm_model["fcap"]
        cap = self.asdr.rm_model["cap"]
        assert len(cap) == len(fcap)

        b = fcap - cap  # Bookings.

        nrows = len(cap)
        assert len(self.asdr.rm_model["rsrc_names"]) == nrows

        # Right-hand side constraints.
        rhs = [0] * len(fcap)
        for nrow in range(nrows):
            rsrc_name = self.asdr.rm_model["rsrc_names"][nrow]
            i = self.asdr.get_leg_id_by_rsrc_name(rsrc_name)
            d = self.asdr.get_duty_id_by_leg_id(i)
            l = self.asdr.get_cmpt_id(rsrc_name)

            # Build LHS: sum of z variables for this resource
            lhs_expr = quicksum(
                A[nrow, j] * self.z_vars[j]
                for j in range(len(self.z_vars))
                if abs(A[nrow, j]) > 1e-10
            )

            # Build RHS: capacity based on aircraft assignment
            rhs_expr = 0
            if d is not None:
                rhs_terms = []
                for k in range(self.asdr.get_num_fleet_types()):
                    assert b[nrow] >= 0
                    c = self.asdr.get_capacity(k, l)
                    if c >= b[nrow]:
                        rhs_terms.append((c - b[nrow]) * self.y_vars[(d, k)])

                if rhs_terms:
                    rhs_expr = quicksum(rhs_terms)

            name = f"leg_capacities_{nrow}"
            self.model.addCons(lhs_expr <= rhs_expr, name=name)
            self.constr_name2id[name] = self.num_constrs
            self.num_constrs += 1

    def set_duty_coverage(self):
        """
        Sets duty coverage constraints.
        """
        for d in self.asdr.duty_ids:
            constr_expr = quicksum(
                self.y_vars[(d, k)]
                for k in range(self.asdr.get_num_fleet_types())
            )

            name = f"duty_coverage_{d}"
            self.model.addCons(constr_expr == 1, name=name)
            self.constr_name2id[name] = self.num_constrs
            self.num_constrs += 1

    def set_aircraft_types_constr(self):
        """
        Sets fleet limit constraints.
        """
        T = self.asdr.get_num_time_indices()
        K = self.asdr.get_num_fleet_types()
        D = len(self.asdr.duty_ids)

        for k in range(K):
            Alpha = sparse.lil_matrix((D, T))
            for d in range(D):
                for t in range(1, T):
                    alpha = self.asdr.get_alpha(self.asdr.duty_ids[d], t, k)
                    if abs(alpha) > 0.000001:
                        Alpha[(d, t)] = alpha
            Alpha = Alpha.tocsr()

            M = np.zeros(T)
            for t in range(1, T):
                M[t] = self.asdr.get_num_aircrafts(k, t)

            # For each time period
            for t in range(1, T):
                lhs_terms = []
                for d in range(D):
                    if abs(Alpha[d, t]) > 1e-10:
                        lhs_terms.append(Alpha[d, t] * self.y_vars[(self.asdr.duty_ids[d], k)])

                if lhs_terms:
                    lhs_expr = quicksum(lhs_terms)
                    name = f"aircraft_types_constraints_{k}_{t}"

                    if self.min_extra_planes:
                        self.model.addCons(lhs_expr <= M[t] + self.m_vars[(k, t)], name=name)
                    else:
                        self.model.addCons(lhs_expr <= M[t], name=name)

                    self.constr_name2id[name] = self.num_constrs
                    self.num_constrs += 1

    def set_m_max_constr(self):
        """
        Sets constraints.
        """
        K = self.asdr.get_num_fleet_types()
        T = self.asdr.get_num_time_indices()
        for k in range(K):
            for t in range(T):
                name = f"m_max_constr_{k}_{t}"
                self.model.addCons(self.m_vars[(k, t)] <= self.m_max_vars[k], name=name)
                self.constr_name2id[name] = self.num_constrs
                self.num_constrs += 1

    def set_y_s_rel_constr(self):
        """
        Sets constraints which relates y and s variables.
        """
        for d in self.asdr.duty_ids:
            for k in range(self.asdr.get_num_fleet_types()):
                at = self.asdr.fleet_types[k]
                y_bar = (1 if self.asdr.duty2at[d] == at else 0)

                # s >= y_bar - y
                name = f"s_y_rel_1_{d}_{k}"
                self.model.addCons(self.s_vars[(d, k)] >= y_bar - self.y_vars[(d, k)], name=name)

                # s >= y - y_bar
                name = f"s_y_rel_2_{d}_{k}"
                self.model.addCons(self.s_vars[(d, k)] >= self.y_vars[(d, k)] - y_bar, name=name)

                # s <= 1 - y_bar + y
                name = f"s_y_rel_3_{d}_{k}"
                self.model.addCons(self.s_vars[(d, k)] <= 1 - y_bar + self.y_vars[(d, k)], name=name)

                # s <= y_bar + 1 - y
                name = f"s_y_rel_4_{d}_{k}"
                self.model.addCons(self.s_vars[(d, k)] <= y_bar + 1 - self.y_vars[(d, k)], name=name)

    def set_max_num_changes_constr(self, max_num_changes):
        """
        Sets maximum number of swaps constraints.
        """
        constr_expr = quicksum(
            self.s_vars[(d, k)]
            for d in self.asdr.duty_ids
            for k in range(self.asdr.get_num_fleet_types())
        )
        self.model.addCons(constr_expr <= max_num_changes, name="max_num_changes")

    def set_fixed_duties_constr(self):
        """
        Sets fixed duties constraints.
        """
        for d in self.asdr.fixed_duties:
            ac = self.asdr.fixed_duties[d]
            k = self.asdr.fleet_types.index(ac)
            self.fix_y_var(d, k, 1, "fixed_duties")

    def set_constraints(self, max_num_changes=None):
        """
        Sets constraints.
        """
        print("\t", time_now(), "Setting leg capacities constraints...")
        self.set_leg_capacities_constr()

        print("\t", time_now(), "Setting duty coverage constraints...")
        self.set_duty_coverage()

        print("\t", time_now(), "Setting aircraft types constraints...")
        self.set_aircraft_types_constr()

        if self.min_extra_planes:
            print("\t", time_now(), "Setting m max constraints...")
            self.set_m_max_constr()

        print("\t", time_now(), "Setting y and s variables relation constraints...")
        self.set_y_s_rel_constr()

        if max_num_changes is not None:
            print("\t", time_now(), "Setting maximum number of swaps constraints...")
            self.set_max_num_changes_constr(max_num_changes)

        print("\t", time_now(), "Setting fixed duites constraints...")
        self.set_fixed_duties_constr()

    def fix_y_var(self, d, k, val, reason=""):
        """
        Fixes y variable, i.e. sets it to zero or one.
        """
        assert val == 0 or val == 1
        name = f"fixed_variable_y_{d}_{k}_{reason}"

        set_constraint = True
        if (d, k) in self.fixed_y_vars:
            old_val, old_reason = self.fixed_y_vars[(d, k)]
            if old_val != val:
                if val == 1 and reason == "solve_with_y_fixed" and old_val == 0 and old_reason in ["max_distance_range",
                                                                                                   "airport_allowance"]:
                    # Remove old constraint
                    old_name = f"fixed_variable_y_{d}_{k}_{old_reason}"
                    cons = self.model.getConss()
                    for c in cons:
                        if c.name == old_name:
                            self.model.delCons(c)
                            del self.constr_name2id[old_name]
                            self.num_constrs -= 1
                            break
                else:
                    set_constraint = False
                    print(f"old_val, old_reason = {old_val}, {old_reason}")
                    print(f"val, reason = {val}, {reason}")
                    assert False
            else:
                set_constraint = False

        if set_constraint:
            self.fixed_y_vars[(d, k)] = (val, reason)
            self.model.addCons(self.y_vars[(d, k)] == val, name=name)
            self.constr_name2id[name] = self.num_constrs
            self.num_constrs += 1


    def build_model(self, max_num_changes=None, min_extra_planes=False):
        self.max_num_changes = max_num_changes
        self.min_extra_planes = min_extra_planes

        # Create model.
        self.model = Model("farm_wo_cancellations")

        # Create variables.
        print(time_now(), "Creating variables...")
        self.create_variables()

        # Set objective.
        print(time_now(), "Setting objective...")
        self.set_objective()

        # Set constraints.
        print(time_now(), "Setting constraints...")
        self.set_constraints(max_num_changes)

    def make_feasible(self):
        y = {}
        for d in self.asdr.duty_ids:
            for k in range(self.asdr.get_num_fleet_types()):
                if self.asdr.duty2at[d] == self.asdr.fleet_types[k]:
                    y[(d, k)] = 1
                else:
                    y[(d, k)] = 0

        for constr in self.model.getConss():
            name = constr.name

            # Get constraint data
            lhs_const = self.model.getLhs(constr)
            rhs_const = self.model.getRhs(constr)

            # Get variables and coefficients from the constraint
            vars_dict = self.model.getValsLinear(constr)

            # Ignore constraints containing other than y variables
            to_continue = False
            for var in vars_dict.keys():
                if var[0] != "y":
                    to_continue = True
                    break
            if to_continue:
                continue

            lhs = 0
            ds, ks = [], []

            for var, coeff in vars_dict.items():
                d, k = var.strip("y_").split("_")
                d, k = int(d), int(k)
                val = y[(d, k)]

                if val != 0:
                    assert val == 1
                    ds.append(d)
                    ks.append(k)
                lhs += coeff * val

            ac_types = [self.asdr.fleet_types[k] for k in ks]
            duties = [[self.asdr.legs[l] for l in self.asdr.duties[self.asdr.duty_ids.index(d)]] for d in ds]
            assert len(duties) == len(ds)
            assert len(self.asdr.duties) == len(self.asdr.duties2startend), "{}, {}".format(
                len(self.asdr.duties), len(self.asdr.duties2startend))

            # Determine constraint sense and check violations
            # SCIP uses -inf for <= constraints (no LHS bound) and inf for >= constraints (no RHS bound)
            if rhs_const < self.model.infinity():  # Has upper bound (<=)
                if lhs > rhs_const:
                    print("VIOLATION: {}: {} <= {}".format(name, lhs, rhs_const))
                    print("ds = {}".format(ds))
                    print("len(self.dr.duties) = {}".format(len(self.asdr.duties)))
                    print("len(self.dr.duties2startend) = {}".format(len(self.asdr.duties2startend)))
                    print("ks = {}".format(ks))
                    print("ac_types = {}".format(ac_types))
                    print("duties")
                    for i, duty in enumerate(duties):
                        duty = [[l[0], l[1], l[2], l[3], l[4], l[5], l[6], l[7]] for l in duty]
                        print("\t{}, {}".format(duty, self.asdr.duties2startend[self.asdr.duty_ids.index(ds[i])]))
                    #print(self.asdr.maint_df[self.dr.maint_df["actype"] == "A7A"].head(10))
                    print("")
                    assert False

            if lhs_const > -self.model.infinity():  # Has lower bound (>=)
                if lhs < lhs_const:
                    print("VIOLATION: {}: {} >= {}".format(name, lhs, lhs_const))
                    print("ds = {}".format(ds))
                    print("ks = {}".format(ks))
                    print("")

            # Check for equality constraint (both bounds are equal and finite)
            if (abs(lhs_const - rhs_const) < 1e-6 and
                    lhs_const > -self.model.infinity() and
                    rhs_const < self.model.infinity()):
                if abs(lhs - rhs_const) > 1e-6:
                    print("VIOLATION: {}: {} == {}".format(name, lhs, rhs_const))
                    print("ds = {}".format(ds))
                    print("ks = {}".format(ks))
                    print("ac_types = {}".format(ac_types))
                    print("duties")
                    for duty in duties:
                        duty = [[l[0], l[1], l[2], l[3], l[4],
                                 datetime.strptime(self.depdates[0], "%Y%m%d") + timedelta(minutes=l[5]),
                                 datetime.strptime(self.depdates[0], "%Y%m%d") + timedelta(minutes=l[6]), l[7]] for l in
                                duty]
                        print("\t{}".format(duty))
                    print("")


    def solve_with_y_fixed(self):
        """
        Solves with y variables fixed to baseline.
        """
        for d in range(self.asdr.get_num_duties()):
            sm = 0  # Sum of ones in values of y variables.
            for k in range(self.asdr.get_num_fleet_types()):
                if self.asdr.duty2at[d] == self.asdr.fleet_types[k]:
                    self.fix_y_var(d, k, 1, "solve_with_y_fixed")
                    sm += 1
                else:
                    self.fix_y_var(d, k, 0, "solve_with_y_fixed")
            assert sm == 1, "sm = {}".format(sm)

        # Set SCIP parameters
        self.model.setParam("presolving/maxrounds", -1)  # Aggressive presolving
        self.model.setParam("limits/gap", 0.05)  # 5% MIP gap
        self.model.setParam("emphasis/optimality", True)
        self.model.optimize()

    def solve(self):
        """
        Solves the optimization problem.
        """
        # Set SCIP parameters (equivalents to Gurobi params)
        #self.model.setParam("presolving/maxrounds", -1)  # Aggressive presolving
        #self.model.setParam("limits/gap", 0.05)  # 5% MIP gap
        #self.model.setParam("emphasis/optimality", True)
        #self.model.setParam("heuristics/emphasis", "aggressive")

        self.model.optimize()

    def get_solution(self):
        """
        Retrieves the solution.
        """
        D = len(self.asdr.duty_ids)
        K = self.asdr.get_num_fleet_types()
        M = self.asdr.get_num_resources()
        N = self.asdr.get_num_products()
        T = self.asdr.get_num_time_indices()

        # Get best solution.
        sol = self.model.getBestSol()

        # Extract y variables.
        y = np.zeros((D, K))
        self.sol_y = {}
        for d in range(D):
            for k in range(K):
                val = self.model.getSolVal(sol, self.y_vars[(self.asdr.duty_ids[d], k)])
                if val > 0.5:  # Binary variable threshold
                    assert d not in self.sol_y.keys()
                    self.sol_y[d] = k
                    y[(d, k)] = 1

        # Extract z variables.
        z = np.zeros(N)
        self.sol_z = []
        for n in range(N):
            val = self.model.getSolVal(sol, self.z_vars[n])
            self.sol_z.append(val)
            z[n] = val

        # Extract m variables if applicable.
        m = np.zeros((K, T))
        self.sol_m = {}
        if self.min_extra_planes:
            for k in range(K):
                for t in range(T):
                    val = self.model.getSolVal(sol, self.m_vars[(k, t)])
                    self.sol_m[(k, t)] = val
                    m[(k, t)] = val

        # Calculate pax.
        pax = sum(self.sol_z)

        # Calculate revenue.
        rev = sum(self.asdr.get_fare(j) * self.sol_z[j] for j in range(N))

        # Booked revenue and pax.
        booked_rev = self.asdr.get_booked_revenue()
        booked_pax = self.asdr.get_booked_pax()

        # Calculate costs.
        costs = 0.0
        for d in range(D):
            if d in self.sol_y:
                k = self.sol_y[d]
                costs += self.asdr.get_duty_costs(self.asdr.duty_ids[d], k)

        # Calculate number of changes.
        duties_changed_ac = 0
        for d in range(D):
            for k in range(K):
                val = self.model.getSolVal(sol, self.s_vars[(self.asdr.duty_ids[d], k)])
                duties_changed_ac += val

        res = {
            "pax": pax,
            "booked_pax": booked_pax,
            "rev": rev,
            "booked_rev": booked_rev,
            "costs": costs,
            "duties_changed_ac": duties_changed_ac,
            "rsrc_names": self.asdr.rm_model["rsrc_names"],
            "M": M,
            "N": N,
            "y": y,
            "z": z,
            "m": m,
            "b": self.asdr.rm_model["b"],
            "f": self.asdr.rm_model["f"],
            "Ai": self.asdr.rm_model["Ai"],
            "Aj": self.asdr.rm_model["Aj"],
            "Adata": self.asdr.rm_model["Adata"],
            "Adistratiodata": self.asdr.rm_model["res_Adistratiodata"]
        }
        return res

if __name__ == "__main__":
    depdates = ["20251219", "20251220"]
    inv_file = "/home/sumkin/rmbits/src/fleet_assigner/as_data/inv2.csv"
    costs_file = "/home/sumkin/rmbits/src/fleet_assigner/as_data/costs.csv"
    fleet_file = "/home/sumkin/rmbits/src/fleet_assigner/as_data/aircraft_inventory.csv"
    cap_file = "/home/sumkin/rmbits/src/fleet_assigner/as_data/capacities.csv"
    maintenance_file = ""
    leg_pairings_file = ""
    turnaround_times_file = ""

    asfwoc = ASFARMWoCancellations(depdates,
                                   inv_file,
                                   costs_file,
                                   fleet_file,
                                   cap_file,
                                   maintenance_file,
                                   leg_pairings_file,
                                   turnaround_times_file)
    asfwoc.load_data()
    asfwoc.build_model(max_num_changes=100000)
    asfwoc.model.write(mps_fname)
    asfwoc.make_feasible()
    asfwoc.solve()
    sol = asfwoc.get_solution()

    print("Revenue = {}".format(sol["rev"]))
    print("Booked revenue = {}".format(sol["booked_rev"]))
    print("Costs = {}".format(sol["costs"]))
    print("Profit = {}".format(sol["rev"] - sol["costs"]))
    print("Number of duties with changed aircraft = {}".format(sol["duties_changed_ac"]))

    aslb = ASLinesBuilder(depdates,
                          asfwoc.asdr.legs,
                          asfwoc.asdr.duty_ids,
                          asfwoc.asdr.duties,
                          asfwoc.sol_y,
                          asfwoc.asdr.fleet_types,
                          asfwoc.asdr.fleet_type2fleet_ids,
                          asfwoc.asdr.leg2duty,
                          asfwoc.asdr,
                          excel_output_writer)
    aslb.build()
    aslb.write_csv("../output/lines.csv")