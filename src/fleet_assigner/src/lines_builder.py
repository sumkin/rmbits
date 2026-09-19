import csv
import copy
from datetime import datetime, timedelta

from aircraft_router import AircraftRouter

class LinesBuilder:

    def __init__(self,
                 depdates,
                 legs,
                 duties,
                 sol_y,
                 sol_w,
                 fleet_types,
                 fleet_type2fleet_ids,
                 leg2duty,
                 dr,
                 output_writer):
        """
        @arg legs                 --- the list of legs.
        @arg sol                  --- solution, i.e. mapping leg index to fleet type index.
        @arg fleet_types          --- list of fleet types.
        @arg fleet_type2fleet_ids --- mapping from fleet type to list of fleet ids.
        """
        self.depdates = depdates
        self.legs = legs
        self.duties = copy.deepcopy(duties)
        self.num_regular_duties = len(self.duties)  # Non-regular duties are maintenance duties.
        self.sol_y = sol_y
        self.sol_w = sol_w
        self.fleet_types = fleet_types
        self.fleet_type2fleet_ids = fleet_type2fleet_ids
        self.leg2duty = leg2duty
        self.dr = dr
        self.output_writer = output_writer

    def get_subnetwork(self, ac_type):
        """
        Gets subnetwork for the aircraft type.
        """
        subnetwork = []

        # Add regular duties.
        k = self.fleet_types.index(ac_type)
        for d in self.sol_y.keys():
            if self.sol_y[d] == k:
                subnetwork.append(d)

        # Add maintenance duties.
        df = self.dr.maint_df[self.dr.maint_df['from_mins'] > 0]
        for _, r in df.iterrows():
            leg = ["HEL", "HEL", r["fltnum"],
                   datetime.strftime(datetime.strptime(self.depdates[0], "%Y%m%d") + timedelta(minutes=r["from_mins"]), "%Y%m%d"),
                   datetime.strftime(datetime.strptime(self.depdates[0], "%Y%m%d") + timedelta(minutes=r["to_mins"]), "%Y%m%d"),
                   r["from_mins_original"],
                   r["to_mins_original"],
                   r["actype"],
                   "AY"]
            if ac_type == r["actype"]:
                self.legs.append(leg)
                leg_id = len(self.legs) - 1
                #self.leg_id2from_to_mins_original[leg_id] = [r["from_mins_original"], r["to_mins_original"]]
                self.duties.append([leg_id])
                duty_id = len(self.duties) - 1
                self.leg2duty[leg_id] = duty_id
                self.sol_y[duty_id] = k
                subnetwork.append(duty_id)

        return subnetwork

    def build(self):
        """
        Builds the lines.
        """
        # Build subnetwork for each aircraft type.
        self.lines = {}
        for k in range(len(self.fleet_types)):
            ac_type = self.fleet_types[k]
            subnetwork = self.get_subnetwork(ac_type)
            if len(subnetwork) == 0:
                continue 
            print("")
            print("fleet_type = {} ({})".format(self.fleet_types[k], len(self.fleet_type2fleet_ids[self.fleet_types[k]])))
            ar = AircraftRouter(self.legs, self.duties, subnetwork, ac_type, self.fleet_type2fleet_ids[ac_type], self.dr)
            self.lines[k] = ar.solve()

    def write_csv(self, fname):
        """
        Write results to CSV file.
        """
        with open(fname, "w") as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(["ORGN", "DSTN", "FLTNUM", "DEPDT", "ARRDT", "DEPTM",
                                 "ARRTM", "AC_TYPE", "AIRCRAFT_ID", "LINE", "COSTS", "J_CAP", "W_CAP", "Y_CAP",
                                 "GROUND_TIME", "DUTY_ID", "CC"])
            ac_type2num = {}
            for k in range(len(self.fleet_types)):
                ac_type = self.fleet_types[k]
                for q in range(self.dr.get_num_configurations(k)):
                    # Get compartment capacities.
                    capacities = {}
                    for l, cmpt in enumerate(self.dr.compartments):
                        capacities[(q, cmpt)] = self.dr.get_capacity(k, l, q)

                subnetwork = self.get_subnetwork(ac_type)
                if len(subnetwork) == 0:
                    continue
                lines = self.lines[k]
                line_num = 1
                for line in lines:
                    ac_type2num[ac_type] = line_num
                    prev_leg_arr_mins = None
                    for leg_id in line:
                        duty_id = self.leg2duty[leg_id]
                        assert self.sol_y[duty_id] == k

                        # Determine optimal config.
                        try:
                            q_opt = None
                            for q in range(self.dr.get_num_configurations(k)):
                                if self.sol_w[(leg_id, k, q)] == 1:
                                    q_opt = q
                            assert q_opt is not None, "leg_id = {}, k = {}, q = {}".format(leg_id, k, q)
                        except:
                            print("WARNING")
                            q_opt = 0

                        num_legs = len(self.duties[duty_id])
                        row = copy.deepcopy(self.legs[leg_id])
                        leg_dep_mins, leg_arr_mins = row[5], row[6]
                        row[3] = (datetime.strptime(self.depdates[0], "%Y%m%d") + timedelta(minutes=leg_dep_mins)).strftime("%Y%m%d")
                        row[4] = (datetime.strptime(self.depdates[0], "%Y%m%d") + timedelta(minutes=leg_arr_mins)).strftime("%Y%m%d")
                        row[5] = (datetime.strptime(self.depdates[0], "%Y%m%d") + timedelta(minutes=leg_dep_mins)).strftime("%H:%M")
                        row[6] = (datetime.strptime(self.depdates[0], "%Y%m%d") + timedelta(minutes=leg_arr_mins)).strftime("%H:%M")
                        if duty_id < self.num_regular_duties:
                            costs = self.dr.get_duty_costs(duty_id, k)
                        else:
                            costs = 0
                        if prev_leg_arr_mins is None:
                            ground_time = None
                        else:
                            ground_time = leg_dep_mins - prev_leg_arr_mins

                        cap_j = 0
                        if (q_opt, "J") in capacities.keys():
                            cap_j = capacities[(q_opt, "J")]

                        cap_w = 0
                        if (q_opt, "W") in capacities.keys():
                            cap_w = capacities[(q_opt, "W")]

                        cap_y = 0
                        if (q_opt, "Y") in capacities.keys():
                            cap_y = capacities[(q_opt, "Y")] 

                        cc = row[8]
                        row = row[:7] + [ac_type, line_num, ac_type + "/" + str(line_num), costs / num_legs]
                        row += [cap_j, cap_w, cap_y, ground_time, duty_id, cc]
                        csv_writer.writerow(row)

                        prev_leg_arr_mins = leg_arr_mins
                    line_num += 1

            # Add wetlease flights.
            for _, r in self.dr.wetlease_df.iterrows():
                depdt = datetime.strptime(self.depdates[0], "%Y%m%d") + timedelta(minutes=r["from_mins"])
                arrdt = datetime.strptime(self.depdates[0], "%Y%m%d") + timedelta(minutes=r["to_mins"])
                if r["actype"] not in ac_type2num.keys():
                    ac_type2num[r["actype"]] = 0
                row = [
                    r["orgn"],                                              # ORGN
                    r["dstn"],                                              # DSTN
                    r["fltnum"],                                            # FLTNUM
                    depdt.strftime("%Y%m%d"),                               # DEPDT
                    arrdt.strftime("%Y%m%d"),                               # ARRDT
                    depdt.strftime("%H:%M"),                                # DEPTM
                    arrdt.strftime("%H:%M"),                                # ARRTM
                    r["actype"],                                            # AC_TYPE
                    ac_type2num[r["actype"]] + 1,                           # AIRCRAFT NUM
                    r["actype"] + "/" + str(ac_type2num[r["actype"]] + 1),  # LINE
                    "",                                                     # COSTS
                    "",                                                     # J_CAP
                    "",                                                     # W_CAP
                    "",                                                     # Y_CAP
                    "",                                                     # GROUND_TIME
                    0,                                                      # DUTY_ID,
                    r["cc"]                                                 # CC
                ]
                csv_writer.writerow(row)

