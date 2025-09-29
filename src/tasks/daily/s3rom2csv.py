import csv
import multiprocessing
from datetime import datetime, timedelta

from s3utils import *
from romcalculator import *

if __name__ == "__main__":
    dt = datetime.now()
    #dt = datetime(2020,2,1)
    for i in range(1,1500):
        dtstr = datetime.strftime(dt - timedelta(days = i), "%Y%m%d")
        dty = dtstr[:4]
        dtm = dtstr[4:6]
        dtd = dtstr[6:8]

        csv_load = "ay-emr-job/nrm/rom/" + dty + "/" + dtm + "/rom_load_" + dtstr + ".csv.gz"
        csv_max = "ay-emr-job/nrm/rom/" + dty + "/" + dtm + "/rom_max_" + dtstr + ".csv.gz"
        csv_min = "ay-emr-job/nrm/rom/" + dty + "/" + dtm + "/rom_min_" + dtstr + ".csv.gz"
        csv_act = "ay-emr-job/nrm/rom/" + dty + "/" + dtm + "/rom_act_" + dtstr + ".csv.gz"
        
        load_out = "/home/ay49514/tmp/rom_load_" + dtstr + ".csv"
        max_out = "/home/ay49514/tmp/rom_max_" + dtstr + ".csv"
        min_out = "/home/ay49514/tmp/rom_min_" + dtstr + ".csv"
        act_out = "/home/ay49514/tmp/rom_act_" + dtstr + ".csv"

        if not s3fileexists(csv_load) or\
           not s3fileexists(csv_max) or\
           not s3fileexists(csv_min) or\
           not s3fileexists(csv_act):

            try:
                romcalc = ROMCalculator(dtstr, dtstr)
            except Exception as e:
                print("e = ", e)
                continue

            # ROM load file.
            load_val, load_names, load_ds, load_sols = romcalc.solve_load()
            if load_val == 0.0:
                continue
            assert len(load_names) == len(load_sols)
            with open(load_out, "w") as fout:
                csvwriter = csv.writer(fout)
                csvwriter.writerow(['GEO_OD_TS_KEY','POS','FF','TP','D','SOL'])
                for i in range(len(load_names)):
                    r = [load_names[i][0],load_names[i][1],load_names[i][2],load_names[i][3],load_ds[i],load_sols[i]]
                    csvwriter.writerow(r)

            # ROM max file.
            max_names, max_ds, max_sols, max_revs = romcalc.solve_max(load_val)
            assert len(max_names) == len(max_sols)
            with open(max_out, "w") as fout:
                csvwriter = csv.writer(fout)
                csvwriter.writerow(['GEO_OD_TS_KEY','POS','FF','TP','D','SOL','REV'])
                for i in range(len(max_names)):
                    r = [max_names[i][0],max_names[i][1],max_names[i][2],max_names[i][3],max_ds[i],max_sols[i],max_revs[i]]
                    csvwriter.writerow(r)

            # ROM min file.
            min_names, min_ds, min_sols, min_revs = romcalc.solve_min(load_val)
            assert len(min_names) == len(min_sols)
            with open(min_out, "w") as fout:
                csvwriter = csv.writer(fout)
                csvwriter.writerow(['GEO_OD_TS_KEY','POS','FF','TP','D','SOL','REV'])
                for i in range(len(min_names)):
                    r = [min_names[i][0],min_names[i][1],min_names[i][2],min_names[i][3],min_ds[i],min_sols[i],min_revs[i]]
                    csvwriter.writerow(r)

            # ROM act file.
            act_names, act_bkgs, act_revs = romcalc.get_actual()
            assert len(act_names) == len(act_bkgs)
            assert len(act_bkgs) == len(act_revs)
            with open(act_out, "w") as fout:
                csvwriter = csv.writer(fout)
                csvwriter.writerow(['GEO_OD_TS_KEY','POS','FF','BKG','REV'])
                for i in range(len(act_names)):
                    r = [act_names[i][0],act_names[i][1],act_names[i][2],act_bkgs[i],act_revs[i]]
                    csvwriter.writerow(r) 

            subprocess.check_output(['gzip',load_out])
            subprocess.check_output(['aws','s3','cp',load_out+'.gz','s3://'+csv_load]) 
            subprocess.check_output(['rm',load_out+'.gz']) 

            subprocess.check_output(['gzip',max_out])
            subprocess.check_output(['aws','s3','cp',max_out+'.gz','s3://'+csv_max]) 
            subprocess.check_output(['rm',max_out+'.gz']) 

            subprocess.check_output(['gzip',min_out])
            subprocess.check_output(['aws','s3','cp',min_out+'.gz','s3://'+csv_min]) 
            subprocess.check_output(['rm',min_out+'.gz']) 

            subprocess.check_output(['gzip',act_out])
            subprocess.check_output(['aws','s3','cp',act_out+'.gz','s3://'+csv_act])
            subprocess.check_output(['rm',act_out+'.gz'])


