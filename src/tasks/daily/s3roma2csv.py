import csv 
import multiprocessing 
from datetime import datetime, timedelta 


from s3utils import * 
from rom_analyzer import ROMAnalyzer 


if __name__ == "__main__":
    dt = datetime.now()
    for i in range(1,1500):
        dtstr = datetime.strftime(dt - timedelta(days = i), "%Y%m%d")
        dty = dtstr[:4]
        dtm = dtstr[4:6]
        dtd = dtstr[6:8]

        csv_tmtf = "ay-rmp-home/nrm/roma/{}/{}/roma_tmtf_{}.csv.gz".format(dty, dtm, dtstr)
        csv_tnf = "ay-rmp-home/nrm/roma/{}/{}/roma_tnf_{}.csv.gz".format(dty, dtm, dtstr)
        csv_tlto = "ay-rmp-home/nrm/roma/{}/{}/roma_tlto_{}.csv.gz".format(dty, dtm, dtstr)
        csv_tmto = "ay-rmp-home/nrm/roma/{}/{}/roma_tmto_{}.csv.gz".format(dty, dtm, dtstr)
        
        tmtf_out = "/home/ay49514/tmp/roma_tmtf_{}.csv".format(dtstr)
        tnf_out = "/home/ay49514/tmp/roma_tnf_{}.csv".format(dtstr)
        tlto_out = "/home/ay49514/tmp/roma_tlto_{}.csv".format(dtstr)
        tmto_out = "/home/ay49514/tmp/roma_tmto_{}.csv".format(dtstr)

        if not s3fileexists(csv_tmtf) or\
           not s3fileexists(csv_tnf) or\
           not s3fileexists(csv_tlto) or\
           not s3fileexists(csv_tmto):
            try:
                ra = ROMAnalyzer(dtstr)
                ra.analyze()
            except Exception as e:
                print("e = ", e)
                continue 

            # Taken more than forecasted.
            with open(tmtf_out, "w") as fout:
                tmtf_df = ra.get_tmtf_df()
                tmtf_df.to_csv(fout, index = False)

            subprocess.check_output(['gzip', tmtf_out])
            subprocess.check_output(['aws', 's3', 'cp', tmtf_out + '.gz', 's3://' + csv_tmtf])
            subprocess.check_output(['rm', tmtf_out + '.gz'])

            # Taken non-forecasted.
            with open(tnf_out, "w") as fout:
                tnf_df = ra.get_tnf_df()
                tnf_df.to_csv(fout, index = False)

            subprocess.check_output(['gzip', tnf_out])
            subprocess.check_output(['aws', 's3', 'cp', tnf_out + '.gz', 's3://' + csv_tnf])
            subprocess.check_output(['rm', tnf_out + '.gz'])

            # Taken less than optimal.
            with open(tlto_out, "w") as fout:
                tlto_df = ra.get_tlto_df()
                tlto_df.to_csv(fout, index = False)

            subprocess.check_output(['gzip', tlto_out])
            subprocess.check_output(['aws', 's3', 'cp', tlto_out + '.gz', 's3://' + csv_tlto])
            subprocess.check_output(['rm', tlto_out + '.gz'])

            # Taken more than optimal.
            with open(tmto_out, "w") as fout:
                tmto_df = ra.get_tmto_df()
                tmto_df.to_csv(fout, index = False)

            subprocess.check_output(['gzip', tmto_out])
            subprocess.check_output(['aws', 's3', 'cp', tmto_out + '.gz', 's3://' + csv_tmto])
            subprocess.check_output(['rm', tmto_out + '.gz'])

            