from datetime import datetime, timedelta
import pandas as pd

from ssim_reader import SSIMReader

class MaintenanceReader(SSIMReader):

    def __init__(self, s3fname, start_date, turnaround_times_df):
        super().__init__(s3fname)
        self.start_date = start_date
        self.turnaround_times_df = turnaround_times_df

    def load(self):
        data = {}
        data["carrier"] = []
        data["orgn"] = []
        data["dstn"] = []
        data["fltnum"] = []
        data["from"] = []
        data["to"] = []
        data["from_mins"] = []
        data["to_mins"] = []
        data["actype"] = []

        def time2mins(dt):
            return int((dt - datetime.strptime(self.start_date, "%Y%m%d")).total_seconds() / 60.0)

        for line in self.get_line():
            carrier, orgn, dstn, fltnum, date_s, date_e, time_s, time_e, dows, actype = line
            if carrier != "AY" and carrier != "N7":
                continue
            if orgn != "HEL" or dstn != "HEL":
                continue
            date = date_s
            while date <= date_e:
                dow = date.weekday() + 1
                if dow not in dows:
                    date += timedelta(days=1)
                    continue
                dt_s = date
                dt_s = dt_s.replace(hour=int(time_s[:2]), minute=int(time_s[2:]))
                if time_e > time_s:
                    dt_e = date
                else:
                    dt_e = date + timedelta(days=1)
                if time_e == "2400":
                    time_e = "2359"
                dt_e = dt_e.replace(hour=int(time_e[:2]), minute=int(time_e[2:]))
                mins_s = time2mins(dt_s)
                mins_e = time2mins(dt_e)

                data["carrier"].append(carrier)
                data["orgn"].append(orgn)
                data["dstn"].append(dstn)
                data["fltnum"].append(fltnum)
                data["from"].append(dt_s)
                data["to"].append(dt_e)
                data["from_mins"].append(mins_s)
                data["to_mins"].append(mins_e)
                data["actype"].append(actype)

                date += timedelta(days=1)
        df = pd.DataFrame(data=data).drop_duplicates()
        df = df[["carrier", "orgn", "dstn", "fltnum", "from_mins", "to_mins", "actype"]]
        df = pd.merge(df, self.turnaround_times_df, how="left", left_on="actype", right_on="Subfleet")
        df["to_mins"] = df["to_mins"] - df["Turnaround"]

        return df

if __name__ == "__main__":
    s3fname = "s3://ay-emr-job/fleet_assigner/december2023/W23_dec_190923.ssim"
    start_date = "20231230"
    mr = MaintenanceReader(s3fname, start_date)
    df = mr.load()
    print(df.tail(5))
