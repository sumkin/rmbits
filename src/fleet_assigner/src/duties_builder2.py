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
        df = pd.read_excel(self.pairings_file, sheet_name="Data")
        for i, r in df.iterrows():
            if r["A/C"] == "32V":
                # This is wetlease. Should be ignored.
                continue

            if pd.isna(r["OnwdEventService"]):
                continue

            if r["OnwdEventService"].strip() == "Z" and r["OnwdEventDest"] != "TLL":
                # This is maintenance. Ignore such entries for duty builder.
                continue

            flids = r["FlId"].strip().split()
            flids = [e for e in flids if e != ""]
            assert len(flids) == 2, "flids = {}".format(flids)

            orgn = r["Orig"].strip()
            dstn = r["Dest"].strip()
            cc, fltnum = flids[0].strip(), flids[1].strip()
            depdate_utc = datetime.strftime(r["Date"], "%Y%m%d")
            deptm_utc = r["STD"]
            arrtm_utc = r["STA"]
            svc = r["Svc"].strip()

            next_orgn = dstn
            next_dstn = r["OnwdEventDest"].strip()
            next_fltnum = r["OnwdEventFlNo"].strip()
            next_depdate_utc = datetime.strftime(r["OnwdEventDate"], "%Y%m%d")
            next_svc = r["OnwdEventService"].strip()
            ac = r["A/C"].strip()

            # Check that next leg is in file.
            if str(next_fltnum).strip().isdigit():
                next_fltnum = str(next_fltnum).zfill(3)
            else:
                next_fltnum = next_fltnum.strip()
            next_fltnum1 = cc + " " + next_fltnum
            next_fltnum2 = cc + "  " + next_fltnum
            sub_df = df[
                (df["Orig"] == next_orgn) &
                (df["Dest"] == next_dstn) &
                (
                    (df["FlId"].str.strip() == next_fltnum1) |
                    (df["FlId"].str.strip() == next_fltnum2)
                ) &
                (df["Date"] == next_depdate_utc)
            ]
            if sub_df.shape[0] == 0:
                if orgn == "TLL" or dstn == "TLL":
                    print("skipped 1")
                    print(orgn, dstn, fltnum, depdate_utc)
                    print(next_orgn, next_dstn, next_fltnum, next_depdate_utc)
                    print("")
                continue

            leg_id1 = self.dr.get_leg_id(orgn, dstn, fltnum, depdate_utc)
            leg_id2 = self.dr.get_leg_id(next_orgn, next_dstn, next_fltnum, next_depdate_utc)
            if cc == "AY":
                # Check this for AY flights only.
                if leg_id1 is None or leg_id2 is None:
                    if orgn == "TLL" or dstn == "TLL":
                        print("skipped 2")
                        print("leg_id1 = {}".format(leg_id1))
                        print("leg_id2 = {}".format(leg_id2))
                        print(orgn, dstn, fltnum, depdate_utc)
                        print(next_orgn, next_dstn, next_fltnum, next_depdate_utc)
                        print("")
                    continue

            leg1 = cc + orgn + dstn + str(fltnum).zfill(4) + depdate_utc + ac + svc
            leg2 = cc + next_orgn + next_dstn + str(next_fltnum).zfill(4) + next_depdate_utc + ac + next_svc

            self.sequences.append([leg1, leg2])

    def merge(self):
        head_map = {}  # first element → seq index
        tail_map = {}  # last element  → seq index
        for i, seq in enumerate(self.sequences):
            if seq:
                head_map.setdefault(seq[0], i)
                tail_map.setdefault(seq[-1], i)

        used = [False] * len(self.sequences)
        result = []

        for i, seq in enumerate(self.sequences):
            if used[i] or not seq:
                continue
            # skip sequences that have a predecessor — they'll be absorbed
            pred_idx = tail_map.get(seq[0])
            if pred_idx is not None and pred_idx != i:
                continue

            # walk the chain forward
            chain = list(seq)
            used[i] = True
            while True:
                next_idx = head_map.get(chain[-1])
                if next_idx is None or used[next_idx]:
                    break
                used[next_idx] = True
                chain = chain[:-1] + self.sequences[next_idx]

            result.append(chain)

        # keep any sequences not reached (isolated or in cycles)
        for i, seq in enumerate(self.sequences):
            if not used[i] and seq:
                result.append(list(seq))

        self.sequences = result

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
            if len(sequence) == 0:
                continue
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
                if isinstance(fltnum, int):
                    pass
                elif fltnum.isdigit():
                    fltnum = int(fltnum.lstrip("0"))
                else:
                    #print("fltnum = {}".format(fltnum))
                    #print("type(fltnum) = {}".format(type(fltnum)))
                    fltnum = fltnum.lstrip("0").strip()
                leg_id = self.dr.get_leg_id(orgn, dstn, fltnum, depdate)
                assert leg_id is not None, f"Leg ID not found for {orgn}-{dstn}-{fltnum}-{depdate}"
                leg = self.legs[leg_id]

                if prev_l is not None:
                    prev_cc, prev_orgn, prev_dstn, prev_fltnum, prev_depdate, prev_ac, prev_svc =\
                        prev_l[:2], prev_l[2:5], prev_l[5:8], prev_l[8:12], prev_l[12:20], prev_l[20:-1], prev_l[-1]
                    prev_fltnum = prev_fltnum.lstrip("0")
                    if prev_fltnum.isdigit():
                        prev_fltnum = int(prev_fltnum)
                    else:
                        prev_fltnum = prev_fltnum.strip()
                    prev_leg_id = self.dr.get_leg_id(prev_orgn, prev_dstn, prev_fltnum, prev_depdate)
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

        """
        for duty_id in self.duties:
            for leg_id in duty_id:
                leg = self.legs[leg_id]
                fltnum = leg[2]
                is_debug = False
                if int(fltnum) == 8921:
                    is_debug = True
                if is_debug:
                    print(leg)
            print("")
        assert False
        """

        return self.duties,\
               self.duties_svc,\
               self.duties2startend,\
               [],\
               self.leg2duty,\
               self.duty2at,\
               self.fixed_duties,\
               self.wetlease_sequences
