import os
import uuid
import dill
import pickle
import numpy as np
from scipy import sparse
from gurobipy import *
import warnings
from datetime import datetime, timedelta

from defs import *
from utils import time_now
from data_reader import DataReader
from excel_output_writer import ExcelOutputWriter
from debug_info_writer import DebugInfoWriter
from s3utils import s3copy
from farm_helpers import *
from lines_builder import LinesBuilder
from CsvToSsimConverter import Converter

class FARMWoCancellations:
    """
    Class implements profit maximization without cancellations.
    """

    def __init__(self,
                 fcstdate,
                 month,
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
                 excel_output_writer,
                 debug_info_writer,
                 subfleets_to_fix):
        self.fcstdate = fcstdate
        self.month = month
        self.depdates = depdates
        self.costs_file = costs_file
        self.fleet_file = fleet_file
        self.cap_file = cap_file
        self.leg_distance_file = leg_distance_file
        self.turnaround_times_file = turnaround_times_file
        self.restrictions_file = restrictions_file
        self.subfleet_ranges_file = subfleet_ranges_file
        self.maintenance_file = maintenance_file
        self.airport_allowance_file = airport_allowance_file
        self.leg_pairings_file = leg_pairings_file
        #self.optimization_status_handler = optimization_status_handler
        self.excel_output_writer = excel_output_writer
        self.debug_info_writer = debug_info_writer
        self.subfleets_to_fix = subfleets_to_fix

        self.dr = None
        self.y_vars = None
        self.z_vars = None
        self.num_constrs = 0
        self.constr_name2id = {}
        self.fixed_y_vars = {}

    def load_data(self):
        #pkl_dr_fname = "../cache/dr_{}_{}.pkl".format(self.month, self.fcstdate)
        #if os.path.exists(pkl_dr_fname):
        #    with open(pkl_dr_fname, "rb") as f:
        #        dr = pickle.load(f)
        #else:
        dr = DataReader(self.fcstdate,
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
                        self.restrictions_file,
                        self.excel_output_writer)
        dr.read()
        #with open(pkl_dr_fname, "wb") as f:
        #    pickle.dump(dr, f)
        self.dr = dr

    def create_variables(self):
        """
        Creates variables for the model.
        """
        num_duties = self.dr.get_num_duties()
        num_fleet_types = self.dr.get_num_fleet_types()
        num_products = self.dr.get_num_products()
        num_time_indices = self.dr.get_num_time_indices()

        # Assignment variables.
        self.y_vars = self.model.addMVar((num_duties, num_fleet_types), vtype=GRB.BINARY, name="y")

        # Revenue variables.
        z_lb = np.zeros(num_products)
        z_ub = np.zeros(num_products)
        for j in range(num_products):
            d = self.dr.get_demand(j)
            if d <= EPS:
                z_ub[j] = 0
            else:
                z_ub[j] = self.dr.get_demand(j)
        self.z_vars = self.model.addMVar(num_products, lb=z_lb, ub=z_ub, vtype=GRB.CONTINUOUS, name="z")

        # Change variables.
        self.s_vars = self.model.addMVar((num_duties, num_fleet_types), vtype=GRB.BINARY, name="s")

        if self.min_extra_planes:
            m_lb = np.zeros((num_fleet_types, num_time_indices))
            self.m_vars = self.model.addMVar((num_fleet_types, num_time_indices),
                                             lb=m_lb,
                                             vtype=GRB.INTEGER,
                                             name="m")
            m_max_lb = np.zeros(num_fleet_types)
            self.m_max_vars = self.model.addMVar(num_fleet_types, lb=m_max_lb, vtype=GRB.INTEGER, name="m_max")

    def set_objective(self):
        """
        Sets the objective of optimization.
        """
        if self.min_extra_planes:
            K = self.dr.get_num_fleet_types()
            self.obj = 0
            for k in range(K):
                self.obj += self.m_max_vars[k]
            self.model.setObjective(self.obj, GRB.MINIMIZE)
        else:
            num_products = self.dr.get_num_products()
            fares = np.array([self.dr.get_fare(j) for j in range(num_products)])
            self.obj = fares @ self.z_vars

            num_duties = self.dr.get_num_duties()
            num_fleet_types = self.dr.get_num_fleet_types()
            costs = np.array([
                self.dr.get_duty_costs(d, k)
                for d in range(num_duties)
                for k in range(num_fleet_types)
            ]).reshape((num_duties, num_fleet_types))
            self.obj -= sum(sum(costs * self.y_vars))
            self.model.setObjective(self.obj, GRB.MAXIMIZE)

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
                curr_at = self.dr.duty2at[d]
                curr_k = self.dr.fleet_types.index(curr_at)
                for k in range(self.dr.get_num_fleet_types()):
                    assert b[nrow] >= 0
                    c = self.dr.get_capacity(k, l)
                    if c < b[nrow]:
                        # Current number of bookings is more than
                        # capacity of aircraft.
                        # If it is not current aircraft forbid usage of aircraft.
                        if k != curr_k:
                            self.fix_y_var(d, k, 0, "overbooking")
                    else:
                        rhs[nrow] += (c - b[nrow]) * self.y_vars[(d, k)]

        lhs = (A @ self.z_vars)
        for nrow in range(nrows):
            name = "leg_capacities_{}".format(nrow)
            self.model.addConstr(lhs[nrow] <= rhs[nrow], name=name)
            assert name not in self.constr_name2id
            self.constr_name2id[name] = self.num_constrs
            self.num_constrs += 1

    def set_duty_coverage(self):
        """
        Sets duty coverage constraints.
        """
        for d in range(self.dr.get_num_duties()):
            constr = -1
            constr += sum([
                self.y_vars[(d, k)] for k in range(self.dr.get_num_fleet_types())
            ])
            name = "duty_coverage_{}".format(d)
            self.model.addConstr(constr == 0, name=name)
            assert name not in self.constr_name2id
            self.constr_name2id[name] = self.num_constrs
            self.num_constrs += 1

    def set_aircraft_types_constr(self):
        """
        Sets fleet limit constraints.
        """
        T = self.dr.get_num_time_indices()
        K = self.dr.get_num_fleet_types()
        D = self.dr.get_num_duties()

        for k in range(K):
            Alpha = sparse.lil_matrix((D, T))
            for d in range(D):
                for t in range(1, T):
                    alpha = self.dr.get_alpha(d, t, k)
                    if abs(alpha) > 0.000001:
                        Alpha[(d, t)] = alpha
            Alpha = Alpha.tocsr()

            M = np.zeros(T)
            for t in range(1, T):
                M[t] = self.dr.get_num_aircrafts(k, t)

            name = "aircraft_types_constraints_{}".format(k)
            LHS = Alpha.T.dot(self.y_vars[:, k])
            if self.min_extra_planes:
                self.model.addConstr(LHS <= M.T + self.m_vars.transpose(), name=name)
            else:
                self.model.addConstr(LHS <= M.T, name=name)

            assert name not in self.constr_name2id
            self.constr_name2id[name] = self.num_constrs
            self.num_constrs += 1

    def set_fleet_range_constr(self):
        """
        Sets fleet range constraints.
        """
        # Precompute max range per fleet type once (same for all duties)
        fleet_max_ranges = [
            self.dr.get_subfleet_max_range(self.dr.fleet_types[k])
            for k in range(self.dr.get_num_fleet_types())
        ]

        for d in range(self.dr.get_num_duties()):
            # Calculate maximum leg distance for duty.
            duty = self.dr.duties[d]
            max_dist = -np.inf
            for leg_id in duty:
                orgn, dstn, _, _, _, _, _, _, _ = self.dr.legs[leg_id]
                dist = self.dr.get_leg_distance(orgn, dstn)
                max_dist = max(max_dist, dist)
            assert max_dist > -np.inf

            # Go over aircraft types and if max leg distance exceeds range fix the variable.
            num = 0
            for k, dist_range in enumerate(fleet_max_ranges):
                if dist_range < max_dist:
                    if (d, k) not in self.fixed_y_vars:
                        self.fix_y_var(d, k, 0, "max_distance_range")
                    num += 1
            assert num < self.dr.get_num_fleet_types()

    def set_jet_not_jet_constr(self):
        """
        Sets the constraints that jet and propellers (A7A, A70) could not be swapped.
        """
        def is_jet(ac_type):
            if ac_type == "A7A" or ac_type == "A70":
                return False
            else:
                return True

        for d in range(self.dr.get_num_duties()):
            at = self.dr.duty2at[d]
            at_ind = self.dr.fleet_types.index(at)
            jet = is_jet(at)
            if at in self.dr.fleet_types:
                for new_at_ind in range(self.dr.get_num_fleet_types()):
                    new_at = self.dr.fleet_types[new_at_ind]
                    new_jet = is_jet(new_at)
                    if jet != new_jet:
                        # Swaps between jet and propellers are not allowed.
                        if (d, new_at_ind) not in self.fixed_y_vars:
                            self.fix_y_var(d, new_at_ind, 0, "Jet-not-jet_swaps_not_allowed.")

    def set_restrict_narrow_vs_wide_body_constr(self):
        """
        Sets constraints which do not allow change narrow to wide body.
        """
        def is_narrow_body(ac_type):
            if "33" in ac_type or "35" in ac_type:
                return False
            return True

        for d in range(self.dr.get_num_duties()):
            at = self.dr.duty2at[d]
            narrow = is_narrow_body(at)
            if at in self.dr.fleet_types:
                for new_at_ind in range(self.dr.get_num_fleet_types()):
                    new_at = self.dr.fleet_types[new_at_ind]
                    new_narrow = is_narrow_body(new_at)
                    if narrow and not new_narrow:
                        if (d, new_at_ind) not in self.fixed_y_vars:
                            self.fix_y_var(d, new_at_ind, 0, "narrow_vs_wide_body_restriction.")
                    if not narrow and new_narrow:
                        if (d, new_at_ind) not in self.fixed_y_vars:
                            self.fix_y_var(d, new_at_ind, 0, "narrow_vs_wide_body_restriction.")

    def set_airport_allowance_constr(self):
        """
        Sets airport allowance constraints, i.e. which airports
        are allowed to fly by which aircract type.
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
                if (d, k) not in self.fixed_y_vars:
                    at = self.dr.fleet_types[k]
                    if not self.dr.is_airport_allowed(airport, at):
                        self.fix_y_var(d, k, 0, "airport_allowance")

    def set_m_max_constr(self):
        """
        Sets constraints.
        """
        K = self.dr.get_num_fleet_types()
        T = self.dr.get_num_time_indices()
        for k in range(K):
            for t in range(T):
                name = "m_max_constr_{}_{}".format(k, t)
                self.model.addConstr(self.m_vars[(k, t)] <= self.m_max_vars[k], name=name)
                assert name not in self.constr_name2id
                self.constr_name2id[name] = self.num_constrs
                self.num_constrs += 1

    def set_y_s_rel_constr(self):
        """
        Sets constraints which relates y and s variables.
        """
        for d in range(self.dr.get_num_duties()):
            for k in range(self.dr.get_num_fleet_types()):
                at = self.dr.fleet_types[k]
                y_bar = (1 if self.dr.duty2at[d] == at else 0)

                constr = self.s_vars[(d, k)] - y_bar - self.y_vars[(d, k)]
                name = "s_y_rel_1_{}_{}".format(d, k)
                self.model.addConstr(constr <= 0, name=name)
                self.constr_name2id[name] = self.num_constrs
                self.num_constrs += 1

                constr = self.s_vars[(d, k)] - y_bar + self.y_vars[(d, k)]
                name = "s_y_rel_2_{}_{}".format(d, k)
                self.model.addConstr(constr >= 0, name=name)
                self.constr_name2id[name] = self.num_constrs
                self.num_constrs += 1
                
                constr = self.s_vars[(d, k)] - self.y_vars[(d, k)] + y_bar 
                name = "s_y_rel_3_{}_{}".format(d, k)
                self.model.addConstr(constr >= 0, name=name)
                self.constr_name2id[name] = self.num_constrs
                self.num_constrs += 1

                constr = self.s_vars[(d, k)] - 2 + y_bar + self.y_vars[(d, k)]
                name = "s_y_rel_4_{}_{}".format(d, k)
                self.model.addConstr(constr <= 0, name=name)
                self.constr_name2id[name] = self.num_constrs
                self.num_constrs += 1

    def set_max_num_changes_constr(self, max_num_changes):
        """
        Sets maximum number of swaps constraints.
        """
        constr = 0
        for d in range(self.dr.get_num_duties()):
            for k in range(self.dr.get_num_fleet_types()):
                constr += self.s_vars[(d, k)]
        self.model.addConstr(constr <= max_num_changes, name="max_num_changes")
        self.constr_name2id[name] = self.num_constrs
        self.num_constrs += 1

    def set_fixed_duties_constr(self):
        """
        Sets fixed duties constraints.
        """
        for d in self.dr.fixed_duties:
            ac = self.dr.fixed_duties[d]
            k = self.dr.fleet_types.index(ac)
            self.fix_y_var(d, k, 1, "fixed_duties")

    def set_restrictions_constr(self):
        """
        Sets restrictions constraints.
        """
        #print(self.dr.restrictions_df.head(5))
        for _, r in self.dr.restrictions_df.iterrows():
            type = str(r["Type"]).strip()
            fltnum = str(r["Flight number"]).strip()
            orgn = str(r["Origin"]).strip()
            dstn = str(r["Destination"]).strip()
            effdate = str(r["Effective Date"]).strip()
            discdate = str(r["Discontinuing Date"]).strip()
            dow = str(r["DOW"]).strip()
            sfgroup = str(r["Subfleet group"]).strip()
            #print(type, fltnum, orgn, dstn, effdate, discdate, dow, sfgroup)
            effdate = datetime.strptime(effdate, "%Y%m%d")
            discdate = datetime.strptime(discdate, "%Y%m%d")
            curdate = effdate
            while curdate <= discdate:
                if str(curdate.isoweekday()) == dow:
                    curdt = curdate.strftime("%Y%m%d")
                    k = orgn + "-" + dstn + "-" + str(fltnum).zfill(4) + "-" + curdt
                    if k in self.dr.orgn_dstn_fltnum_depdt2leg_id.keys():
                        leg_id = self.dr.orgn_dstn_fltnum_depdt2leg_id[k]
                        if leg_id in self.dr.leg2duty.keys():
                            duty_id = self.dr.leg2duty[leg_id]
                            at = self.dr.duty2at[duty_id]
                            assert at in self.dr.fleet_types
                            if type == "Freeze":
                                kk = self.dr.fleet_types.index(at)
                                self.fix_y_var(duty_id, kk, 1, "freeze_restrictions")
                            elif type == "Limit subfleet":
                                allowed_ats = sfgroup.split(",")
                                allowed_ats = [e.strip() for e in allowed_ats]
                                for at in self.dr.fleet_types:
                                    if at not in allowed_ats:
                                        kk = self.dr.fleet_types.index(at)
                                        self.fix_y_var(duty_id, kk, 0, "limit_subfleet_restrictions")
                curdate += timedelta(days=1)

    def set_330_350_rule_constraints(self):
        """
        Sets 330 and 350s rule.
        """
        for duty_id in range(len(self.dr.duties)):
            at = self.dr.duty2at[duty_id]
            assert at in self.dr.fleet_types
            if at == "33S":
                if not self.dr.duty_contains(duty_id, "AMS"):
                    k = self.dr.fleet_types.index(at)
                    self.fix_y_var(duty_id, k, 1, "330_350_rule")

    def set_subfleets_to_fix_constraints(self):
        """
        Sets subfleets to fix constraints.
        """
        for subfleet in self.subfleets_to_fix:
            for duty_id in range(len(self.dr.duties)):
                if self.dr.duty2at[duty_id] == subfleet:
                    k = self.dr.fleet_types.index(subfleet)
                    self.fix_y_var(duty_id, k, 1, "subfleets_to_fix")
                    print("Duty {} fixed for {}".format(duty_id, subfleet))
                else:
                    k = self.dr.fleet_types.index(subfleet)
                    self.fix_y_var(duty_id, k, 0, "subfleets_to_fix")
                    print("Subfleet {} is excluded for duty_id = {}.".format(subfleet, duty_id))

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

        print("\t", time_now(), "Setting fleet range_constraints...")
        self.set_fleet_range_constr()

        print("\t", time_now(), "Setting jet-not-jet constraints...")
        self.set_jet_not_jet_constr()

        print("\t", time_now(), "Setting narrow to wide body constraints...")
        self.set_restrict_narrow_vs_wide_body_constr()

        print("\t", time_now(), "Setting airport allowance constraints...")
        self.set_airport_allowance_constr()

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

        print("\t", time_now(), "Setting restrictions constraints...")
        self.set_restrictions_constr()

        print("\t", time_now(), "Setting 330_350 rule constraints...")
        self.set_330_350_rule_constraints()

        print("\t", time_now(), "Setting subfleets to fix constraints...")
        self.set_subfleets_to_fix_constraints()

    def fix_y_var(self, d, k, val, reason=""):
        """
        Fixes y variable, i.e. sets it to zero or one.
        """
        assert val == 0 or val == 1
        name = "fixed_variable_y_{}_{}_{}".format(d, k, reason)

        set = True
        if (d, k) in self.fixed_y_vars:
            old_val, old_reason = self.fixed_y_vars[(d, k)]
            if old_val != val:
                if val == 1 and reason == "solve_with_y_fixed" and old_val == 0 and old_reason == "max_distance_range":
                    # Current solution violates maximum distance range. Overwrite constraint.

                    # Remove old constraint.
                    self.model.update()  # Update before querying.
                    c = self.model.getConstrByName(name)
                    self.model.remove(c)
                    del self.constr_name2id[name]
                    self.num_constrs -= 1
                elif val == 1 and reason == "solve_with_y_fixed" and old_val == 0 and old_reason == "airport_allowance":
                    # Current solution violates airport allowance. Overwrite constraint.

                    # Remove old constraint.
                    self.model.update()  # Update before querying.
                    c = self.model.getConstrByName(name)
                    try:
                        self.model.remove(c)
                        del self.constr_name2id[name]
                        self.num_constrs -= 1
                    except:
                        print("Try to remove constraint, which is missing, name = {}".format(name))
                else:
                    set = False
                    print("d = {}".format(d))
                    print("k = {}".format(k))
                    print("ac = {}".format(self.dr.fleet_types[k]))
                    duty = self.dr.duties[d]
                    print([self.dr.legs[l] for l in duty])
                    print("old_val, old_reason = {}, {}".format(old_val, old_reason))
                    print("val, reason = {}, {}".format(val, reason))

                    assert False
            else:
                # Same value. Only reason could be different.
                set = False
        if set:
            self.fixed_y_vars[(d, k)] = (val, reason)
            constr = self.y_vars[(d, k)]
            self.model.addConstr(constr == val, name=name)
            assert name not in self.constr_name2id
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
        for d in range(self.dr.get_num_duties()):
            for k in range(self.dr.get_num_fleet_types()):
                if self.dr.duty2at[d] == self.dr.fleet_types[k]:
                    y[(d, k)] = 1
                else:
                    y[(d, k)] = 0

        for constr in self.model.getConstrs():
            name = constr.ConstrName
            sense = constr.Sense
            rhs = constr.RHS
            expr = self.model.getRow(constr)

            # Ignore constraints containing other than y variables.
            to_continue = False
            for i in range(expr.size()):
                var = expr.getVar(i)
                if var.VarName[0] != "y":
                    to_continue = True
                    break
            if to_continue:
                continue

            lhs = 0
            ds, ks = [], []
            for i in range(expr.size()):
                var = expr.getVar(i)
                c = expr.getCoeff(i)
                d, k = var.VarName.strip("y[").strip("]").split(",")
                d, k = int(d), int(k)
                val = y[(d, k)]
                if val != 0:
                    assert val == 1
                    ds.append(d)
                    ks.append(k)
                lhs += c * val
            ac_types = [self.dr.fleet_types[k] for k in ks]
            duties = [[self.dr.legs[l] for l in self.dr.duties[d]] for d in ds]
            duties_ac_types = [self.dr.duty2at[d] for d in ds]
            assert len(duties) == len(ds)
            assert len(self.dr.duties) == len(self.dr.duties2startend), "{}, {}".format(len(self.dr.duties), len(self.dr.duties2startend))
            if sense == "<":
                if lhs > rhs:
                    print("VIOLATION: {}: {} <= {}".format(name, lhs, rhs))
                    print("ds = {}".format(ds))
                    print("len(self.dr.duties) = {}".format(len(self.dr.duties)))
                    print("len(self.dr.duties2startend) = {}".format(len(self.dr.duties2startend)))
                    print("ks = {}".format(ks))
                    print(self.dr.ts[13], self.dr.ts[14], self.dr.ts[15])
                    print("ac_types = {}".format(ac_types))
                    print("duties_ac_types = {}".format(duties_ac_types))
                    print("fleet_types = {}".format(self.dr.fleet_types))
                    print("duties")
                    for i, duty in enumerate(duties):
                        duty = [[l[0], l[1], l[2], l[3], l[4], l[5], l[6], l[7]] for l in duty]
                        duty_start_mins, duty_end_mins = self.dr.duties2startend[ds[i]]
                        duty_start_dt = datetime.strptime(self.depdates[0], "%Y%m%d") + timedelta(minutes=duty_start_mins)
                        duty_end_dt = datetime.strptime(self.depdates[0], "%Y%m%d") + timedelta(minutes=duty_end_mins)
                        print("\t{}, {} {}".format(duty, duty_start_dt.strftime("%Y-%m-%d %H:%M:%S"), duty_end_dt.strftime("%Y-%m-%d %H:%M:%S")))
                    print(self.dr.maint_df[self.dr.maint_df["actype"] == ac_types[0]].head(20))
                    print("")
                    assert False
            elif sense == "=":
                if lhs != rhs:
                    print("VIOLATION: {}: {} == {}".format(name, lhs, rhs))
                    print("ds = {}".format(ds))
                    print("ks = {}".format(ks))
                    print("ac_types = {}".format(ac_types))
                    print("duties")
                    for duty in duties:
                        duty = [[l[0], l[1], l[2], l[3], l[4],
                                 datetime.strptime(self.depdates[0], "%Y%m%d") + timedelta(minutes=l[5]),
                                 datetime.strptime(self.depdates[0], "%Y%m%d") + timedelta(minutes=l[6]), l[7]] for l in duty]
                        print("\t{}".format(duty))
                    print("")
            elif sense == ">":
                if lhs < rhs:
                    print("VIOLATION: {}: {} >= {}".format(name, lhs, rhs))
                    print("ds = {}".format(ds))
                    print("ks = {}".format(ks))
                    print("")
            else:
                print(lhs, sense, rhs, name)
                assert False

    def solve_with_y_fixed(self):
        for d in range(self.dr.get_num_duties()):
            sm = 0  # Sum of ones in values of y variables.
            for k in range(self.dr.get_num_fleet_types()):
                if self.dr.duty2at[d] == self.dr.fleet_types[k]:
                    self.fix_y_var(d, k, 1, "solve_with_y_fixed")
                    sm += 1
                else:
                    self.fix_y_var(d, k, 0, "solve_with_y_fixed")
            assert sm == 1, "sm = {}".format(sm)
        self.model.setParam("Presolve", 2)
        self.model.setParam("MIPGap", 0.05)
        self.model.setParam("MIPFocus", 2)
        self.model.optimize()

    def solve(self):
        self.model.setParam("Presolve", 2)
        self.model.setParam("MIPGap", 0.05)
        self.model.setParam("MIPFocus", 2)
        self.model.setParam("Heuristics", 0.95)
        self.model.optimize()

    def get_solution(self):
        """
        Retrieves the solution.
        """
        D = self.dr.get_num_duties()
        K = self.dr.get_num_fleet_types()
        M = self.dr.get_num_resources()
        N = self.dr.get_num_products()
        T = self.dr.get_num_time_indices()

        y = np.zeros((D, K))
        self.sol_y = {}
        for d in range(D):
            for k in range(K):
                val = self.y_vars[(d, k)].getAttr("x")
                if val == 1:
                    assert d not in self.sol_y.keys()
                    self.sol_y[d] = k
                    y[(d, k)] = val

        z = np.zeros(N)
        self.sol_z = {}
        for n in range(N):
            val = self.z_vars[n].getAttr("x")
            self.sol_z[n] = val
            z[n] = val

        m = np.zeros((K, T))
        self.sol_m = {}
        if self.min_extra_planes:
            for k in range(K):
                for t in range(T):
                    val = self.m_vars[(k, t)].getAttr("x")
                    self.sol_m[(k, t)] = val
                    m[(k, t)] = val

        self.sol_z = []
        for j in range(N):
            val = self.z_vars[j].getAttr("x")
            self.sol_z.append(val)

        # Calculate pax.
        pax = 0.0
        for j in range(N):
            pax += self.sol_z[j]

        # Calculate revenue.
        rev = 0.0
        for j in range(N):
            rev += self.dr.get_fare(j) * self.sol_z[j]

        # Booked revenue.
        booked_rev = self.dr.get_booked_revenue()

        # Booked pax.
        booked_pax = self.dr.get_booked_pax()

        # Calculate costs.
        costs = 0.0
        for d in range(D):
            for k in range(K):
                if d in self.sol_y.keys():
                    if self.sol_y[d] == k:
                        costs += self.dr.get_duty_costs(d, k)

        # Calculate number of changes.
        duties_changed_ac = 0
        for d in range(D):
            for k in range(K):
                duties_changed_ac += self.s_vars[(d, k)].getAttr("x")

        res = {
            "pax": pax,
            "booked_pax": booked_pax,
            "rev": rev,
            "booked_rev": booked_rev,
            "costs": costs,
            "duties_changed_ac": duties_changed_ac,
            "prdt_names": self.dr.rm_model["prdt_names"],
            "rsrc_names": self.dr.rm_model["rsrc_names"],
            "M": M,
            "N": N,
            "y": y,
            "z": z,
            "m": m,
            "d": self.dr.rm_model["d"],
            "b": self.dr.rm_model["b"],
            "f": self.dr.rm_model["f"],
            "Ai": self.dr.rm_model["Ai"],
            "Aj": self.dr.rm_model["Aj"],
            "Adata": self.dr.rm_model["Adata"],
            "Adistratiodata": self.dr.rm_model["res_Adistratiodata"]
        }
        return res

    def write_output_excel(self, sol_y_fixed, sol, y, dr):
        self.excel_output_writer.write_summary(sol_y_fixed, sol)
        self.excel_output_writer.write_info_per_leg_df(self.dr.inv_df, sol_y_fixed, sol, y, dr)
        #self.excel_output_writer.write_costs_df(self.dr.costs_df)
        #self.excel_output_writer.write_leg_distance_df(self.dr.leg_distance_df)
        #self.excel_output_writer.write_subfleet_range_df(self.dr.subfleet_range_df)
        #self.excel_output_writer.write_maint_df(self.dr.maint_df)


if __name__ == "__main__":
    fcstdate = "20251006"
    month = "february2026"

    excel_fname = "fa_{}_{}.xlsx".format(fcstdate, month)
    excel_output_writer = ExcelOutputWriter("../output/{}".format(excel_fname))
    debug_info_writer = DebugInfoWriter("../output/")

    fcstyear, fcstmonth, fcstday = fcstdate[:4], fcstdate[4:6], fcstdate[6:]
    depdates = ["20260131",
                "20260201", "20260202", "20260203", "20260204", "20260205", "20260206", "20260207",
                "20260208", "20260209", "20260210", "20260211", "20260212", "20260213", "20260214",
                "20260215", "20260216", "20260217", "20260218", "20260219", "20260220", "20260221",
                "20260222", "20260223", "20260224", "20260225", "20260226", "20260227", "20260228",
                "20260301"]
    costs_file = "s3://ay-rmp-home/anaplan_costs/{}/{}/{}/{}.csv".format(fcstyear, fcstmonth, fcstday, month)
    fleet_file = "s3://ay-rmp-home/fleet_assigner/input/aircraft_inventory.csv"
    cap_file = "s3://ay-rmp-home/fleet_assigner/input/subfleet_capacities.csv"
    leg_distance_file = "s3://ay-rmp-home/fleet_assigner/input/leg_distances.csv"
    subfleet_ranges_file = "s3://ay-rmp-home/fleet_assigner/input/subfleet_ranges.csv"
    maintenance_file = "s3://ay-rmp-home/fleet_assigner/input/SSIM_FEB2days.ssim"
    airport_allowance_file = "s3://ay-rmp-home/fleet_assigner/input/airport_allowance.csv"
    leg_pairings_file = "s3://ay-rmp-home/fleet_assigner/input/FEB_Report.xlsx"
    turnaround_times_file = "s3://ay-rmp-home/fleet_assigner/input/turnaround_times.csv"
    restrictions_file = "s3://ay-rmp-home/fleet_assigner/input/restrictions.csv"

    dill_fwoc_fname = "../cache/fwoc_{}_{}.dill".format(month, fcstdate)
    mps_fname = "../cache/model_{}_{}.mps".format(month, fcstdate)
    if os.path.exists(dill_fwoc_fname) and os.path.exists(mps_fname):
        with open(dill_fwoc_fname, "rb") as f:
            fwoc = dill.load(f)
        fwoc.model = read(mps_fname)
        vars = fwoc.model.getVars()

        y_vars = [var for var in vars if "y" in var.VarName]
        fwoc.y_vars = {}
        for y_var in y_vars:
            var_name = y_var.VarName
            d, k = var_name.split(",")
            d, k = int(d.lstrip("y[")), int(k.rstrip("]"))
            fwoc.y_vars[(d, k)] = y_var

        z_vars = [var for var in vars if "z" in var.VarName]
        fwoc.z_vars = {}
        for z_var in z_vars:
            var_name = z_var.VarName
            j = int(var_name.strip("z[").strip("]"))
            fwoc.z_vars[j] = z_var

        s_vars = [var for var in vars if "s" in var.VarName]
        fwoc.s_vars = {}
        for s_var in s_vars:
            var_name = s_var.VarName
            d, k = var_name.split(',')
            d, k = int(d.lstrip("s[")), int(k.rstrip("]"))
            fwoc.s_vars[(d, k)] = s_var
        fwoc.obj = fwoc.model.getObjective()
    else:
        subfleets_to_fix = ["A7A", "A70", "33S"]
        fwoc = FARMWoCancellations(fcstdate,
                                   month,
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
                                   excel_output_writer,
                                   debug_info_writer,
                                   subfleets_to_fix)
        fwoc.load_data()
        fwoc.build_model(max_num_changes=100000)
        fwoc.model.write(mps_fname)

        model = fwoc.model
        y_vars = fwoc.y_vars
        z_vars = fwoc.z_vars
        s_vars = fwoc.s_vars
        obj = fwoc.obj

        fwoc.model = None
        fwoc.y_vars = None
        fwoc.z_vars = None
        fwoc.s_vars = None
        fwoc.obj = None
        with open(dill_fwoc_fname, "wb") as f:
            dill.dump(fwoc, f)
        fwoc.model = model

        fwoc.y_vars = y_vars
        fwoc.z_vars = z_vars
        fwoc.s_vars = s_vars
        fwoc.obj = obj

    fwoc.make_feasible()
    #fwoc.solve_with_y_fixed()
    fwoc.solve()
    sol = fwoc.get_solution()

    debug_info_writer.write_fa_diagram(month, fwoc.dr, sol["y"], sol["m"])
    fwoc.write_output_excel(sol)
    print("Revenue = {}".format(sol["rev"]))
    print("Booked revenue = {}".format(sol["booked_rev"]))
    print("Costs = {}".format(sol["costs"]))
    print("Profit = {}".format(sol["rev"] - sol["costs"]))
    print("Number of duties with changed aircraft = {}".format(sol["duties_changed_ac"]))

    lb = LinesBuilder(depdates,
                      fwoc.dr.legs,
                      fwoc.dr.duties,
                      fwoc.sol_y,
                      fwoc.dr.fleet_types,
                      fwoc.dr.fleet_type2fleet_ids,
                      fwoc.dr.leg2duty,
                      fwoc.dr,
                      excel_output_writer)
    lb.build()
    lb.write_csv("../output/lines.csv")
    s3copy("../output/lines.csv", "s3://ay-rmp-home/fleet_assigner/{}/output/lines.csv".format(month))

    conv = Converter("../output/lines.csv", "../output/lines.ssim")
    conv.convert()
    s3copy("../output/lines.ssim", "s3://ay-rmp-home/fleet_assigner/{}/output/lines.ssim".format(month))

    s3copy("../output/{}".format(excel_fname), "s3://ay-rmp-home/fleet_assigner/{}/output/{}".format(month, excel_fname))