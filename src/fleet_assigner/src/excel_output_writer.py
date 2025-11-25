import os
import pandas as pd
from datetime import datetime
from scipy.sparse import csc_matrix

class ExcelOutputWriter:

    def __init__(self, fname):
        self.fname = fname
        self.created_dt = datetime.now().strftime("%Y-%m-%d %H:%M")
        if os.path.exists(self.fname):
            mode = "a"
            if_sheet_exists = "replace"
        else:
            mode = "w"
            if_sheet_exists = None
        with pd.ExcelWriter(self.fname, mode=mode, if_sheet_exists=if_sheet_exists) as writer:
            # This creates Excel. Content will be overwritten later.
            data = [
                ["Created", self.created_dt]
            ]
            df = pd.DataFrame(data)
            df.to_excel(writer, header=False, index=False, sheet_name="info")

    def write_info(self, sol_y_fixed, sol):
        data = [
            ["Created", self.created_dt, ""],
            ["", "", ""],
            ["", "Before optimization", "After optimization"],
            ["Pax", sol_y_fixed["pax"], sol["pax"]],
            ["Booked pax", sol_y_fixed["booked_pax"], sol["booked_pax"]],
            ["Revenue", sol_y_fixed["rev"], sol["rev"]],
            ["Booked revenue", sol_y_fixed["booked_rev"], sol["booked_rev"]],
            ["Costs", sol_y_fixed["costs"], sol["costs"]],
            ["Duties changed aircraft", sol_y_fixed["duties_changed_ac"], sol["duties_changed_ac"]]
        ]
        df = pd.DataFrame(data)
        with pd.ExcelWriter(self.fname, mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, header=False, index=False, sheet_name="info")

    def write_inv_df(self, inv_df, sol_y_fixed, sol, dr):
        before_paxes_vals = []
        after_paxes_vals = []
        before_rev_vals = []
        after_rev_vals = []
        before_at_vals = []
        after_at_vals = []
        at_change_vals = []
        before_costs = []
        after_costs = []

        # Calculate pax before and after.
        Ai_fixed, Aj_fixed, Adata_fixed = sol_y_fixed["Ai"], sol_y_fixed["Aj"], sol_y_fixed["Adata"]
        Ai, Aj, Adata = sol["Ai"], sol["Aj"], sol["Adata"]

        A_fixed = csc_matrix((Adata_fixed, (Ai_fixed, Aj_fixed)), shape=(sol_y_fixed["M"], sol_y_fixed["N"]))
        A = csc_matrix((Adata, (Ai, Aj)), shape=(sol["M"], sol["N"]))

        paxes_fixed = A_fixed.dot(sol_y_fixed["z"])
        paxes = A.dot(sol["z"])

        rev_fixed = A_fixed.dot(sol_y_fixed["f"] * sol_y_fixed["z"])
        rev = A.dot(sol["f"] * sol["z"])

        for k, r in inv_df.iterrows():
            orgn = r["ORGN"]
            dstn = r["DSTN"]
            fltnum = r["FLTNUM"]
            depdt = r["DEPDT_UTC"]

            before_at = None
            after_at = None

            leg_id = dr.get_leg_id(orgn, dstn, fltnum, depdt)
            if leg_id is None:
                before_paxes_vals.append(0.0)
                after_paxes_vals.append(0.0)
                before_rev_vals.append(0.0)
                after_rev_vals.append(0.0)
            else:
                rsrc_name_idxs = dr.get_rsrc_name_indices_by_leg_id(leg_id)

                before_paxes = round(sum([paxes_fixed[i] for i in range(len(paxes_fixed)) if i in rsrc_name_idxs]))
                after_paxes = round(sum([paxes[i] for i in range(len(paxes)) if i in rsrc_name_idxs]))

                before_rev = sum([rev_fixed[i] for i in range(len(rev_fixed)) if i in rsrc_name_idxs])
                after_rev = sum([rev[i] for i in range(len(rev)) if i in rsrc_name_idxs])

                before_paxes_vals.append(before_paxes)
                after_paxes_vals.append(after_paxes)

                before_rev_vals.append(before_rev)
                after_rev_vals.append(after_rev)

            duty_id = dr.get_duty_id_by_leg_id(leg_id)

            if duty_id is not None:
                before_at = dr.duty2at[duty_id]
                after_at = None
                for kk in range(len(dr.fleet_types)):
                    if sol["y"][(duty_id, kk)] == 1:
                        after_at = dr.fleet_types[kk]
                        break
            before_at_vals.append(before_at)
            after_at_vals.append(after_at)
            if before_at != after_at:
                at_change_vals.append(True)
            else:
                at_change_vals.append(False)

            if before_at is None:
                before_costs.append(0.0)
            else:
                before_costs.append(dr.get_leg_costs(orgn, dstn, depdt, before_at))

            if after_at is None:
                after_costs.append(0.0)
            else:
                after_costs.append(dr.get_leg_costs(orgn, dstn, depdt, after_at))

        inv_df["A/C before"] = before_at_vals
        inv_df["A/C after"] = after_at_vals
        inv_df["A/C change"] = at_change_vals
        inv_df["Costs before"] = before_costs
        inv_df["Costs after"] = after_costs
        inv_df["Pax before"] = before_paxes_vals
        inv_df["Pax after"] = after_paxes_vals
        inv_df["Revenue before"] = before_rev_vals
        inv_df["Revenue after"] = after_rev_vals
        inv_df = inv_df.drop("AIRCRAFT_TYPE", axis=1)

        with pd.ExcelWriter(self.fname, mode="a", if_sheet_exists="replace") as writer:
            inv_df.to_excel(writer, index=False, sheet_name="inv_df")

    def write_costs_df(self, costs_df):
        with pd.ExcelWriter(self.fname, mode="a", if_sheet_exists="replace") as writer:
            costs_df.to_excel(writer, index=False, sheet_name="costs_df")

    def write_leg_distance_df(self, leg_distance_df):
        with pd.ExcelWriter(self.fname, mode="a", if_sheet_exists="replace") as writer:
            leg_distance_df.to_excel(writer, index=False, sheet_name="leg_distance_df")

    def write_subfleet_range_df(self, subfleet_range_df):
        with pd.ExcelWriter(self.fname, mode="a", if_sheet_exists="replace") as writer:
            subfleet_range_df.to_excel(writer, index=False, sheet_name="subfleet_range_df")

    def write_cabin_df(self, cabin_df):
        with pd.ExcelWriter(self.fname, mode="a", if_sheet_exists="replace") as writer:
            cabin_df.to_excel(writer, index=False, sheet_name="cabin_df")

    def write_leg_df(self, leg_df):
        with pd.ExcelWriter(self.fname, mode="a", if_sheet_exists="replace") as writer:
            leg_df.to_excel(writer, index=False, sheet_name="leg_df")

    def write_standalone_df(self, standalone_df):
        with pd.ExcelWriter(self.fname, mode="a", if_sheet_exists="replace") as writer:
            standalone_df.to_excel(writer, index=False, sheet_name="standalone_df")

    def write_duties_df(self, duty_2legs_df, duty_3legs_df, duty_4legs_df):
        with pd.ExcelWriter(self.fname, mode="a", if_sheet_exists="replace") as writer:
            duty_2legs_df.to_excel(writer, index=False, sheet_name="duty_2legs_df")
            duty_3legs_df.to_excel(writer, index=False, sheet_name="duty_3legs_df")
            duty_4legs_df.to_excel(writer, index=False, sheet_name="duty_4legs_df")

    def write_fixed_y_var_df(self, fixed_y_var):
        # Create data frame.
        data = {
            "d": [],
            "k": [],
            "val": [],
            "reason": []
        }
        for d, k in fixed_y_var.keys():
            val, reason = fixed_y_var[(d, k)]
            data["d"].append(d)
            data["k"].append(k)
            data["val"].append(val)
            data["reason"].append(reason)
        df = pd.DataFrame(data)
        with pd.ExcelWriter(self.fname, mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, index=False, sheet_name="fixed_y_var")

    def write_pairings_df(self, dr, pairings_df, sol_y, fleet_types):
        sol_df = pd.DataFrame(columns=["duty_id", "New A/C"])
        for duty_id in sol_y.keys():
            row = {
                "duty_id": duty_id,
                "New A/C": fleet_types[sol_y[duty_id]],
                "Costs": dr.get_duty_costs(duty_id, dr.fleet_types.index(dr.duty2at[duty_id])),
                "New costs": dr.get_duty_costs(duty_id, sol_y[duty_id])
            }
            sol_df = sol_df._append(row, ignore_index=True)
        pairings_df = pd.merge(pairings_df, sol_df, on="duty_id", how="left")
        pairings_df["Swapped"] = (
            (pairings_df["A/C"] != pairings_df["New A/C"]) &
            (~pairings_df["Skipped"])
        )
        with pd.ExcelWriter(self.fname, mode="a", if_sheet_exists="replace") as writer:
            pairings_df.to_excel(writer, index=False, sheet_name="pairings_df")

    def write_skipped_legs_df(self, skipped_legs_df):
        with pd.ExcelWriter(self.fname, mode="a", if_sheet_exists="replace") as writer:
            skipped_legs_df.to_excel(writer, index=False, sheet_name="skipped_legs_df")

    def write_skipped_pairings_df(self, skipped_pairings_df):
        with pd.ExcelWriter(self.fname, mode="a", if_sheet_exists="replace") as writer:
            skipped_pairings_df.to_excel(writer, index=False, sheet_name="skipped_pairings_df")

    def write_maint_df(self, maint_df):
        with pd.ExcelWriter(self.fname, mode="a", if_sheet_exists="replace") as writer:
            maint_df.to_excel(writer, index=False, sheet_name="maint_df")
