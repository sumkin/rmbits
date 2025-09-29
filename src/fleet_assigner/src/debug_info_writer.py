import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

from s3utils import s3copy

class DebugInfoWriter:

    def __init__(self, output_folder):
        self.output_folder = output_folder

    def write_fa_diagram(self, month, dr, y, m):
        with_extra = (len(m) != 0)

        D = dr.get_num_duties()
        K = dr.get_num_fleet_types()
        T = dr.get_num_time_indices()

        # Create dataframe.
        if with_extra:
            data = {
                "time": [],
                "ac_type": [],
                "num": [],
                "extra": [],
                "used": []
            }
        else:
            data = {
                "time": [],
                "ac_type": [],
                "num": [],
                "used": []
            }

        for k in range(K):
            for t in range(1, T):
                num = dr.get_num_aircrafts(k, t)
                for tau in range(dr.ts[t-1], dr.ts[t]):
                    used = 0
                    for d in range(D):
                        alpha = dr.get_alpha(d, t, k)
                        used += alpha * y[(d, k)]
                    dt = datetime.strptime(dr.depdates[0], "%Y%m%d") + timedelta(minutes=tau)
                    data["time"].append(dt)
                    data["ac_type"].append(dr.fleet_types[k])
                    data["num"].append(num)
                    if with_extra:
                        data["extra"].append(m[(k, t)])
                    data["used"].append(used)
        df = pd.DataFrame(data)
        df.to_csv(self.output_folder + "fleet_availability.csv")

        ac_types = df["ac_type"].unique()
        for ac_type in ac_types:
            subdf = df[df["ac_type"] == ac_type]

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=subdf["time"], y=subdf["num"], name="available"))
            if with_extra:
                fig.add_trace(go.Scatter(x=subdf["time"], y=subdf["num"] + subdf["extra"], name="required"))
            fig.add_trace(go.Scatter(x=subdf["time"], y=subdf["used"], name="used"))
            fig.write_html("{}{}_fa.html".format(self.output_folder, ac_type))
            fig.update_layout(title=ac_type)
            s3copy(
                "{}{}_fa.html".format(self.output_folder, ac_type),
                "s3://ay-emr-job/fleet_assigner/{}/output/{}_fa.html".format(month, ac_type)
            )

if __name__ == "__main__":
    diw = DebugInfoWriter("../output/")