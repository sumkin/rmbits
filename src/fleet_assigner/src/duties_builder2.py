import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from defs import *

class DutiesBuilder2:

    def __init__(self,
                 dr,
                 pairings_file,
                 depdates,
                 next_depdate,
                 legs,
                 fleet_types,
                 output_writer):
        self.dr = dr
        self.pairings_file = pairings_file
        self.depdates = depdates
        self.next_depdate = next_depdate
        self.legs = legs
        self.fleet_types = fleet_types
        self.output_writer = output_writer

        self.sequences = []
        self.wetlease_sequences = []
        self.duties = []
        self.leg2duty = {}
        self.duty2startend = []
        self.duty2at = {}

    def read_parent_child_pairs(self):
        df = pd.read_excel(self.pairings_file, sheet_name="OTP_Fedor")
        for i, r in df.iterrows():
            if r["A/C"] == "73Z" or r["A/C"] == "32V":
                # This is wetlease. Should be ignored.
                continue

            if r["OnwdEventService"].strip() == "Z":
                # This is maintenance. Ignore such entries for duty builder.
                continue

            flids = r["FlId"].strip().split()
            flids = [e for e in flids if e != ""]
            assert len(flids) == 2, "flids = {}".format(flids)

            orgn = r["Orig"].strip()
            dstn = r["Dest"].strip()
            cc, fltnum = flids[0], flids[1]
            depdate_utc = datetime.strftime(r["Date"], "%Y%m%d")
            svc = r["Svc"].strip()

            next_orgn = dstn
            next_dstn = r["OnwdEventDest"].strip()
            next_fltnum = int(r["OnwdEventFlNo"].strip())
            next_depdate_utc = datetime.strftime(r["OnwdEventDate"], "%Y%m%d")
            next_svc = r["OnwdEventService"].strip()
            ac = r["A/C"].strip()

            # Check that next leg is in file.
            sub_df = df[
                (df["Orig"] == next_orgn) &
                (df["Dest"] == next_dstn) &
                (
                    (df["FlId"].str.strip() == cc + " " + str(next_fltnum).zfill(3)) |
                    (df["FlId"].str.strip() == cc + "  " + str(next_fltnum).zfill(3))
                ) &
                (df["Date"] == next_depdate_utc)
            ]
            if sub_df.shape[0] == 0:
                continue

            leg_id1 = self.dr.get_leg_id(orgn, dstn, fltnum, depdate_utc)
            leg_id2 = self.dr.get_leg_id(next_orgn, next_dstn, next_fltnum, next_depdate_utc)
            if cc == "AY":
                # Check this for AY flights only.
                if leg_id1 is None or leg_id2 is None:
                    continue

            leg1 = cc + orgn + dstn + str(fltnum).zfill(4) + depdate_utc + ac + svc
            leg2 = cc + next_orgn + next_dstn + str(next_fltnum).zfill(4) + next_depdate_utc + ac + next_svc

            self.sequences.append([leg1, leg2])

    def merge(self):
        while True:
            merged = False
            n = len(self.sequences)
            print("n = {}".format(n))
            for i in range(n):
                e1 = self.sequences[i]
                for j in range(i + 1, n):
                    e2 = self.sequences[j]
                    if e1[len(e1) - 1] == e2[0]:
                        self.sequences[i] = e1[:-1] + e2
                        del self.sequences[j]
                        merged = True
                        break
                    elif e1[0] == e2[len(e2) - 1]:
                        self.sequences[i] = e2[:-1] + e1
                        del self.sequences[j]
                        merged = True
                        break
                if merged:
                    break
            if not merged:
                break

    def clean(self):
        # Remove wrong ending legs.
        for sequence in self.sequences:
            last_leg = sequence[-1]
            cc, orgn, dstn = last_leg[:2], last_leg[2:5], last_leg[5:8]
            if cc == "AY" and dstn != "HEL":
                del sequence[-1]

        # Remove wrong starting legs.
        for sequence in self.sequences:
            first_leg = sequence[0]
            cc, orgn, dstn = first_leg[:2], first_leg[2:5], first_leg[5:8]
            if cc == "AY" and orgn != "HEL":
                del sequence[0]

    def create_duties(self):
        self.duties = []
        self.duties_svc = []
        self.duties2startend = []
        self.leg2duty = {}
        self.duty2at = {}
        self.fixed_duties = {}
        self.num_wetlease_sequences = 0

        for sequence in self.sequences:
            cc = sequence[0][:2]
            if cc != "AY":
                self.num_wetlease_sequences += 1
                self.wetlease_sequences.append(sequence)
                continue

            cur_duty = []
            cur_duty_svc = []
            n = len(sequence)
            for i in range(n):
                l = sequence[i]
                prev_l = None
                if i > 0:
                    prev_l = sequence[i - 1]

                cc, orgn, dstn, fltnum, depdate, ac, svc = l[:2], l[2:5], l[5:8], l[8:12], l[12:20], l[20:-1], l[-1]
                leg_id = self.dr.get_leg_id(orgn, dstn, int(fltnum.lstrip("0")), depdate)
                leg = self.legs[leg_id]

                if prev_l is not None:
                    prev_cc, prev_orgn, prev_dstn, prev_fltnum, prev_depdate, prev_ac, prev_svc =\
                        prev_l[:2], prev_l[2:5], prev_l[5:8], prev_l[8:12], prev_l[12:20], prev_l[20:-1], prev_l[-1]
                    prev_leg_id = self.dr.get_leg_id(prev_orgn, prev_dstn, int(prev_fltnum.lstrip("0")), prev_depdate)
                    prev_leg = self.legs[prev_leg_id]
                    assert prev_dstn == orgn
                    if prev_dstn == "HEL" and orgn == "HEL":
                        actual_turnaround_time = leg[5] - prev_leg[6]
                        required_turnaround_time = self.dr.turnaround_times_df[
                            self.dr.turnaround_times_df["Subfleet"] == ac
                        ]["Turnaround"].iloc[0]
                        if actual_turnaround_time >= required_turnaround_time:
                            cur_duty.append(prev_leg_id)
                            cur_duty_svc.append(prev_svc)
                            duty_id = len(self.duties)
                            assert len(cur_duty) % 2 == 0, "len(cur_duty) = {}".format(len(cur_duty))
                            self.duties.append(cur_duty)
                            self.duties_svc.append(cur_duty_svc)
                            if "C" in cur_duty_svc or "P" in cur_duty_svc or "K" in cur_duty_svc:
                                self.fixed_duties[duty_id] = ac
                            duty_start = np.inf
                            duty_end = -np.inf
                            for l_id in cur_duty:
                                duty_start = min(duty_start, self.legs[l_id][5])
                                duty_end = max(duty_end, self.legs[l_id][6])
                                self.leg2duty[l_id] = duty_id
                            self.duties2startend.append([duty_start, duty_end])
                            self.duty2at[duty_id] = ac
                            cur_duty = []
                            cur_duty_svc = []
                            continue
                        else:
                            duty_id = len(self.duties)
                            if duty_id in self.fixed_duties:
                                assert ac == self.fixed_duties[duty_id]
                            self.fixed_duties[duty_id] = ac
                    cur_duty.append(prev_leg_id)
                    cur_duty_svc.append(prev_svc)

                if i == n - 1:
                    cur_duty.append(leg_id)
                    cur_duty_svc.append(svc)
                    duty_id = len(self.duties)
                    assert len(cur_duty) % 2 == 0, "len(cur_duty) = {}".format(len(cur_duty))
                    self.duties.append(cur_duty)
                    self.duties_svc.append(cur_duty_svc)
                    if "C" in cur_duty_svc or "P" in cur_duty_svc or "K" in cur_duty_svc:
                        self.fixed_duties[duty_id] = ac
                    duty_start = np.inf
                    duty_end = -np.inf
                    for l_id in cur_duty:
                        duty_start = min(duty_start, self.legs[l_id][5])
                        duty_end = max(duty_end, self.legs[l_id][6])
                        self.leg2duty[l_id] = duty_id
                    self.duties2startend.append([duty_start, duty_end])
                    self.duty2at[duty_id] = ac

    def build(self):
        self.read_parent_child_pairs()
        self.merge()
        self.clean()
        self.create_duties()
        return self.duties,\
               self.duties_svc,\
               self.duties2startend,\
               [],\
               self.leg2duty,\
               self.duty2at,\
               self.fixed_duties,\
               self.wetlease_sequences
