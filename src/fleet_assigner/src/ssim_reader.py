import subprocess
from datetime import datetime, timedelta
import pandas as pd

from s3utils import s3copy

class SSIMReader:

    def __init__(self, s3fname):
        self.s3fname = s3fname

    def get_line(self):
        local_fname = "/home/ay49514/tmp/main.ssim"
        s3copy(self.s3fname, local_fname)
        with (open(local_fname, "r") as fin):
            num = 0
            lines = fin.readlines()
            for line in lines:
                line = line.strip()
                if line[0] != "3":
                    continue
                assert len(line) == 200
                code = line[0]
                carrier = line[2:4]
                fltnum = line[5:8]
                _ = line[9:13]
                dates = line[14:28]
                dow = line[28:36]
                start = line[36:52]
                end = line[54:70]
                actype = line[72:75]

                num += 1
                from_date = dates[:7]
                to_date = dates[7:]
                from_date = datetime.strptime(from_date, "%d%b%y")
                to_date = datetime.strptime(to_date, "%d%b%y")
                dows = [int(e) for e in dow if e.strip() != ""]
                orgn = start[:3].strip()
                dstn = end[:3].strip()
                orgn_time_s = start[3:]
                dstn_time_s = end[3:]
                orgn_time = orgn_time_s[:4]
                dstn_time = dstn_time_s[:4]
                assert orgn_time == orgn_time_s[4:8] and dstn_time == dstn_time_s[4:8]
                yield [carrier, orgn, dstn, fltnum, from_date, to_date, orgn_time, dstn_time, dows, actype]
            subprocess.run(["rm", local_fname])


