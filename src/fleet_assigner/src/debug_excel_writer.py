import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

MAX_EXCEL_ROWS = 1048575  # Excel limit minus header row.
MAX_SHEET_NAME_LEN = 31   # Excel limit.

class DebugExcelWriter:
    """
    Writes debugging information into a separate Excel file.

    Sheets are collected in memory and the whole file is rewritten on flush(),
    which is much faster than reopening the workbook for every sheet. The file
    is created right away so that it exists even if the run fails early.
    """

    def __init__(self, fname, info=None):
        self.fname = fname
        self.created_dt = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.info = [["Created", self.created_dt]]
        if info is not None:
            for key, val in info.items():
                self.info.append([key, val])
        self.sheets = {}
        self.flush()

    def __getstate__(self):
        # Do not drag collected dataframes into dill caches.
        state = self.__dict__.copy()
        state["sheets"] = {}
        return state

    def add_info(self, key, val):
        self.info.append([key, val])

    def write_df(self, sheet_name, df):
        assert len(sheet_name) <= MAX_SHEET_NAME_LEN, "Sheet name '{}' is too long.".format(sheet_name)
        if df.shape[0] > MAX_EXCEL_ROWS:
            logger.warning("Debug sheet '{}' has {} rows, truncated to {}.".format(sheet_name, df.shape[0], MAX_EXCEL_ROWS))
            df = df.head(MAX_EXCEL_ROWS)
        self.sheets[sheet_name] = df

    def flush(self):
        with pd.ExcelWriter(self.fname, mode="w") as writer:
            pd.DataFrame(self.info).to_excel(writer, header=False, index=False, sheet_name="Info")
            for sheet_name, df in self.sheets.items():
                df.to_excel(writer, index=False, sheet_name=sheet_name)

    def _mins2dt(self, dr, mins):
        return datetime.strptime(dr.depdates[0], "%Y%m%d") + timedelta(minutes=int(mins))

    def _leg2str(self, leg):
        orgn, dstn, fltnum, depdt, _, _, _, _, cc = leg
        return "{}{} {}-{} {}".format(cc, fltnum, orgn, dstn, depdt)

    def write_data_reader(self, dr):
        """
        Writes inputs and derived structures of the DataReader.
        """
        self.write_df("Fleet", dr.fr.fleet_df)
        self.write_df("Fleet types", pd.DataFrame({
            "k": range(len(dr.fleet_types)),
            "Fleet type": dr.fleet_types,
            "Num aircrafts": [len(dr.fleet_type2fleet_ids[at]) for at in dr.fleet_types],
            "Turnaround": [dr.get_turnaround_time(k) for k in range(len(dr.fleet_types))],
            "Num configurations": [dr.get_num_configurations(k) for k in range(len(dr.fleet_types))],
        }))
        self.write_df("Subfleet configurations", dr.subfleet_configurations_df)
        self.write_df("Subfleet ranges", dr.subfleet_range_df)
        self.write_df("Cabins", dr.cabin_df)
        self.write_df("Turnaround times", dr.turnaround_times_df)
        self.write_df("Restrictions", dr.restrictions_df)
        self.write_df("Airport allowance", dr.airport_allowance_df)
        self.write_df("Maintenance", dr.maint_df)
        self.write_df("Wetlease", dr.wetlease_df)

        # Legs.
        missing = {tuple(leg) for leg in dr.missing_fcst_legs}
        rows = []
        for i, leg in enumerate(dr.legs):
            orgn, dstn, fltnum, depdt, arrdt, dep_mins, arr_mins, at, cc = leg
            d = dr.get_duty_id_by_leg_id(i)
            rows.append({
                "LEG_ID": i,
                "CC": cc,
                "FLTNUM": fltnum,
                "ORGN": orgn,
                "DSTN": dstn,
                "DEPDT": depdt,
                "ARRDT": arrdt,
                "DEP (UTC)": self._mins2dt(dr, dep_mins),
                "ARR (UTC)": self._mins2dt(dr, arr_mins),
                "A/C": at,
                "DISTANCE": dr.get_leg_distance(orgn, dstn),
                "DUTY_ID": d,
                "IN_DUTY": d is not None,
                "MISSING_FORECAST": tuple(leg) in missing,
            })
        self.write_df("Legs", pd.DataFrame(rows))

        # Duties.
        rows = []
        for d, duty in enumerate(dr.duties):
            start_mins, end_mins = dr.duties2startend[d]
            rows.append({
                "DUTY_ID": d,
                "A/C": dr.duty2at[d],
                "NUM_LEGS": len(duty),
                "START (UTC)": self._mins2dt(dr, start_mins),
                "END (UTC)": self._mins2dt(dr, end_mins),
                "FIXED_A/C": dr.fixed_duties.get(d, ""),
                "SVC": ",".join(dr.duties_svc[d]),
                "LEG_IDS": ",".join(str(i) for i in duty),
                "LEGS": " | ".join(self._leg2str(dr.legs[i]) for i in duty),
            })
        self.write_df("Duties", pd.DataFrame(rows))

        # Wetlease sequences.
        self.write_df("Wetlease sequences", pd.DataFrame({
            "SEQUENCE_ID": range(len(dr.wetlease_sequences)),
            "A/C": [seq[0][20:-1] for seq in dr.wetlease_sequences],
            "LEGS": [" | ".join(seq) for seq in dr.wetlease_sequences],
        }))

        # Time indices.
        self.write_df("Time indices", pd.DataFrame({
            "t": range(len(dr.ts)),
            "MINS": dr.ts,
            "TIME (UTC)": [self._mins2dt(dr, ts) for ts in dr.ts],
        }))

    def write_aircraft_availability(self, dr, num_aircrafts):
        """
        Writes number of available aircrafts per fleet type and time interval.
        @arg num_aircrafts --- mapping fleet type index to array indexed by t.
        """
        T = dr.get_num_time_indices()
        data = {
            "t": range(1, T),
            "FROM (UTC)": [self._mins2dt(dr, dr.ts[t - 1]) for t in range(1, T)],
            "TO (UTC)": [self._mins2dt(dr, dr.ts[t]) for t in range(1, T)],
        }
        for k in sorted(num_aircrafts.keys()):
            data[dr.fleet_types[k]] = num_aircrafts[k][1:]
        self.write_df("Aircraft availability", pd.DataFrame(data))

    def write_fixed_y_vars(self, sheet_name, dr, fixed_y_vars):
        rows = []
        for (d, k), (val, reason) in sorted(fixed_y_vars.items()):
            rows.append({
                "DUTY_ID": d,
                "k": k,
                "Fleet type": dr.fleet_types[k],
                "Current A/C": dr.duty2at[d],
                "Value": val,
                "Reason": reason,
            })
        self.write_df(sheet_name, pd.DataFrame(rows, columns=["DUTY_ID", "k", "Fleet type", "Current A/C", "Value", "Reason"]))

    def write_model_stats(self, sheet_name, model):
        data = [
            ["Num vars", model.NumVars],
            ["Num binary vars", model.NumBinVars],
            ["Num int vars", model.NumIntVars],
            ["Num constraints", model.NumConstrs],
            ["Num non-zeros", model.NumNZs],
        ]
        if model.SolCount > 0:
            data += [
                ["Status", model.Status],
                ["Objective", model.ObjVal],
                ["Objective bound", model.ObjBound],
                ["MIP gap", model.MIPGap],
                ["Runtime (s)", model.Runtime],
            ]
        elif model.Status != 1:  # 1 is GRB.LOADED, i.e. not solved yet.
            data += [["Status", model.Status]]
        self.write_df(sheet_name, pd.DataFrame(data, columns=["Key", "Value"]))

    def write_duty_assignment(self, sheet_name, dr, sol_y):
        rows = []
        for d in range(dr.get_num_duties()):
            before_at = dr.duty2at[d]
            after_at = dr.fleet_types[sol_y[d]] if d in sol_y else None
            before_k = dr.fleet_types.index(before_at)
            rows.append({
                "DUTY_ID": d,
                "A/C before": before_at,
                "A/C after": after_at,
                "Changed": before_at != after_at,
                "Costs before": dr.get_duty_costs(d, before_k),
                "Costs after": dr.get_duty_costs(d, sol_y[d]) if d in sol_y else None,
                "LEGS": " | ".join(self._leg2str(dr.legs[i]) for i in dr.duties[d]),
            })
        self.write_df(sheet_name, pd.DataFrame(rows))
