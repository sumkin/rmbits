import os
import pandas as pd
from datetime import datetime
from scipy.sparse import csc_matrix

pd.set_option('display.max_columns', None)

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
            df.to_excel(writer, header=False, index=False, sheet_name="Summary")

    def write_summary(self, sol_y_fixed, sol):
        total_pax_before = float(sol_y_fixed["pax"]) + float(sol_y_fixed["booked_pax"])
        total_pax_after = float(sol["pax"]) + float(sol["booked_pax"])
        total_pax_diff = total_pax_after - total_pax_before

        total_revenue_before = float(sol_y_fixed["rev"]) + float(sol_y_fixed["booked_rev"])
        total_revenue_after = float(sol["rev"]) + float(sol["booked_rev"])
        total_revenue_diff = total_revenue_after - total_revenue_before

        costs_before = float(sol_y_fixed["costs"])
        costs_after = float(sol["costs"])
        costs_diff = costs_after - costs_before

        profit_before = total_revenue_before - costs_before
        profit_after = total_revenue_after - costs_after
        profit_diff = profit_after - profit_before

        duties_changed_before = ""
        duties_changed_after = sol["duties_changed_ac"]
        duties_changed_diff = ""

        total_pax_before = format(int(total_pax_before), ',d').replace(',', ' ')
        total_pax_after = format(int(total_pax_after), ',d').replace(',', ' ')
        total_pax_diff = format(int(total_pax_diff), ',d').replace(',', ' ')

        total_revenue_before = format(int(total_revenue_before), ',d').replace(',', ' ')
        total_revenue_after = format(int(total_revenue_after), ',d').replace(',', ' ')
        total_revenue_diff = format(int(total_revenue_diff), ',d').replace(',', ' ')

        costs_before = format(int(costs_before), ',d').replace(',', ' ')
        costs_after = format(int(costs_after), ',d').replace(',', ' ')
        costs_diff = format(int(costs_diff), ',d').replace(',', ' ')

        profit_before = format(int(profit_before), ',d').replace(',', ' ')
        profit_after = format(int(profit_after), ',d').replace(',', ' ')
        profit_diff = format(int(profit_diff), ',d').replace(',', ' ')

        data = [
            ["Created", self.created_dt, "", ""],
            ["", "", "", ""],
            ["", "Before optimization", "After optimization", "Difference"],
            ["Total pax", total_pax_before, total_pax_after, total_pax_diff],
            ["Total revenue", total_revenue_before, total_revenue_after, total_revenue_diff],
            ["Costs", costs_before, costs_after, costs_diff],
            ["Profit", profit_before, profit_after, profit_diff],
            ["Duties changed aircraft", duties_changed_before, duties_changed_after, duties_changed_diff]
        ]
        df = pd.DataFrame(data)
        with pd.ExcelWriter(self.fname, mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, header=False, index=False, sheet_name="Summary")

    def write_info_per_leg_df(self, inv_df, sol_y_fixed, sol, y, dr):
        leg_id_vals = []
        deptm_vals = []
        arrtm_vals = []
        duty_id_vals = []
        before_paxes_vals = []
        after_paxes_vals = []
        booked_paxes_vals = []
        before_rev_vals = []
        after_rev_vals = []
        booked_rev_vals = []
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
        b_paxes = A.dot(sol["b"])

        rev_fixed = A_fixed.dot(sol_y_fixed["f"] * sol_y_fixed["z"])
        rev = A.dot(sol["f"] * sol["z"])
        b_rev = A.dot(sol["f"] * sol["b"])

        for k, r in inv_df.iterrows():
            cc = r["CC"]
            orgn = r["ORGN"]
            dstn = r["DSTN"]
            fltnum = r["FLTNUM"]
            depdt_utc = r["DEPDT_UTC"]

            before_at = None
            after_at = None

            leg_id = dr.get_leg_id(orgn, dstn, fltnum, depdt_utc)
            duty_id = dr.get_duty_id_by_leg_id(leg_id)
            if duty_id is None:
                duty_id_vals.append("")
            else:
                duty_id_vals.append(str(duty_id))

            if leg_id is None:
                leg_id_vals.append("")
                deptm_vals.append("")
                arrtm_vals.append("")

                before_paxes_vals.append(0.0)
                after_paxes_vals.append(0.0)
                booked_paxes_vals.append(0.0)

                before_rev_vals.append(0.0)
                after_rev_vals.append(0.0)
                booked_rev_vals.append(0.0)
            else:
                if (cc, int(fltnum), depdt_utc) in dr.leg2deparrtm.keys():
                    deparrtm = dr.leg2deparrtm[(cc, int(fltnum), depdt_utc)]
                    deptm_vals.append(deparrtm[0])
                    arrtm_vals.append(deparrtm[1])
                else:
                    deptm_vals.append("")
                    arrtm_vals.append("")


                rsrc_name_idxs = dr.get_rsrc_name_indices_by_leg(orgn, dstn, fltnum, depdt_utc)

                before_paxes = round(sum([paxes_fixed[i] for i in rsrc_name_idxs if i < len(paxes_fixed)]))
                after_paxes = round(sum([paxes[i] for i in rsrc_name_idxs if i < len(paxes)]))
                booked_paxes = round(sum([b_paxes[i] for i in rsrc_name_idxs if i < len(b_paxes)]))

                before_rev = sum([rev_fixed[i] for i in rsrc_name_idxs if i < len(rev_fixed)])
                after_rev = sum([rev[i] for i in rsrc_name_idxs if i < len(rev)])
                booked_rev = sum([b_rev[i] for i in rsrc_name_idxs if i < len(b_rev)])

                leg_id_vals.append(str(leg_id))

                before_paxes_vals.append(before_paxes)
                after_paxes_vals.append(after_paxes)
                booked_paxes_vals.append(booked_paxes)

                before_rev_vals.append(before_rev)
                after_rev_vals.append(after_rev)
                booked_rev_vals.append(booked_rev)

            if duty_id is not None:
                before_at = dr.duty2at.get(duty_id)
                for kk in range(len(dr.fleet_types)):
                    if sol["y"][(duty_id, kk)] == 1:
                        assert kk == y[duty_id], "kk = {}, y[{}] = {}".format(kk, duty_id, y[duty_id])
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
                before_costs.append(dr.get_leg_costs(orgn, dstn, depdt_utc, before_at))

            if after_at is None:
                after_costs.append(0.0)
            else:
                after_costs.append(dr.get_leg_costs(orgn, dstn, depdt_utc, after_at))

        n = len(inv_df)
        assert n == len(leg_id_vals)
        assert n == len(deptm_vals)
        assert n == len(arrtm_vals)
        assert n == len(duty_id_vals)
        assert n == len(before_paxes_vals)
        assert n == len(after_paxes_vals)
        assert n == len(booked_paxes_vals)
        assert n == len(before_rev_vals)
        assert n == len(after_rev_vals)
        assert n == len(booked_rev_vals)
        assert n == len(before_at_vals)
        assert n == len(after_at_vals)
        assert n == len(at_change_vals)
        assert n == len(before_costs)
        assert n == len(after_costs)

        inv_df["LEG_ID"] = leg_id_vals
        inv_df["DUTY_ID"] = duty_id_vals
        inv_df["A/C before"] = before_at_vals
        inv_df["A/C after"] = after_at_vals
        inv_df["A/C change"] = at_change_vals
        inv_df["Costs before"] = before_costs
        inv_df["Costs after"] = after_costs
        inv_df["Booked pax"] = booked_paxes_vals
        inv_df["Pax before"] = before_paxes_vals
        inv_df["Pax after"] = after_paxes_vals
        inv_df["Booked revenue"] = booked_rev_vals
        inv_df["Revenue before"] = before_rev_vals
        inv_df["Revenue after"] = after_rev_vals
        inv_df["Booked profit before"] = [a - b for a, b in zip(booked_rev_vals, before_costs)]
        inv_df["Booked profit after"] = [a - b for a, b in zip(booked_rev_vals, after_costs)]
        inv_df["Profit before"] = [a - b for a, b in zip(before_rev_vals, before_costs)]
        inv_df["Profit after"] = [a - b for a, b in zip(after_rev_vals, after_costs)]
        inv_df["Total pax before"] = [a + b for a, b in zip(booked_paxes_vals, before_paxes_vals)]
        inv_df["Total pax after"] = [a + b for a, b in zip(booked_paxes_vals, after_paxes_vals)]
        inv_df["Total revenue before"] = [a + b for a, b in zip(booked_rev_vals, before_rev_vals)]
        inv_df["Total revenue after"] = [a + b for a, b in zip(booked_rev_vals, after_rev_vals)]
        inv_df["Total profit before"] = [a + b - c for a, b, c in zip(booked_rev_vals, before_rev_vals, before_costs)]
        inv_df["Total profit after"] = [a + b - c for a, b, c in zip(booked_rev_vals, after_rev_vals, after_costs)]

        inv_df["DEPTM"] = deptm_vals
        inv_df["ARRTM"] = arrtm_vals

        inv_df = inv_df[
            (inv_df["LEG_ID"].astype(str).str.strip() != "") &
            (inv_df["DUTY_ID"].astype(str).str.strip() != "")
        ]
        inv_df = inv_df.drop("AIRCRAFT_TYPE", axis=1)
        """
        inv_df = inv_df[["CC", "FLTNUM", "ORGN", "DSTN", "DEPDT", "DEPTM", "ARRTM", "LEG_ID", "DUTY_ID",
            "A/C before", "A/C after", "A/C change", "Costs before", "Costs after",
            "Booked pax", "Pax before", "Pax after",
            "Booked revenue", "Revenue before", "Revenue after",
            "Booked profit before", "Booked profit after", "Profit before", "Profit after",
            "Total pax before", "Total pax after", "Total revenue before", "Total revenue after",
            "Total profit before", "Total profit after"]]
        """
        inv_df["Forecast difference"] = inv_df["Total pax after"] - inv_df["Total pax before"]
        inv_df["Costs difference"] = inv_df["Costs after"] - inv_df["Costs before"]
        inv_df["Profit difference"] = inv_df["Profit after"] - inv_df["Profit before"]

        inv_df = inv_df[["CC","FLTNUM","ORGN","DSTN","DEPDT","DEPTM","ARRTM",
                         "A/C change", "A/C before", "A/C after",
                         "Booked pax", "Total pax before", "Total pax after", "Forecast difference",
                         "Total revenue before", "Total revenue after",
                         "Costs before", "Costs after", "Costs difference",
                         "Total profit before", "Total profit after", "Profit difference"
                         ]]
        inv_df["DEPDT"] = pd.to_datetime(inv_df["DEPDT"], format="%Y%m%d")
        inv_df["DEPDT"] = inv_df["DEPDT"].dt.strftime("%Y-%m-%d")

        #inv_df["DEPTM"] = inv_df["DEPTM"].astype(str).str.zfill(4)
        #inv_df["DEPTM"] = inv_df["DEPTM"].str[:2] + ":" + inv_df["DEPTM"].str[2:4]

        #inv_df["ARRTM"] = inv_df["ARRTM"].astype(str).str.zfill(4)
        #inv_df["ARRTM"] = inv_df["ARRTM"].str[:2] + ":" + inv_df["ARRTM"].str[2:4]

        cols_to_format = [
            "Booked pax",
            "Total pax before", "Total pax after", "Forecast difference",
            "Total revenue before", "Total revenue after",
            "Costs before", "Costs after", "Costs difference",
            "Total profit before", "Total profit after", "Profit difference"
        ]
        for col in cols_to_format:
            inv_df[col] = inv_df[col].fillna(0).astype(int)
            inv_df[col] = inv_df[col].apply(lambda x: f"{x:,}".replace(",", " "))

        inv_df = inv_df.drop_duplicates()

        with pd.ExcelWriter(self.fname, mode="a", if_sheet_exists="replace") as writer:
            inv_df.to_excel(writer, index=False, sheet_name="Info per leg")

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
