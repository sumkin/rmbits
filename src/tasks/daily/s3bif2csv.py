import os
import sys
import csv
import re
import subprocess
from datetime import datetime, timedelta
import traceback
from timezonefinder import TimezoneFinder
from pytz import timezone

from bifreader import *
from s3utils import *
#from emailutils import *
from airport import Airport


def process(fname):
    dt_s = datetime.now()

    print("Processing ", fname)

    print("Copying to local file...")
    fnames = fname.split('/')
    lfname = "/mnt/data/tmp/{}".format(fnames[5])
    subprocess.check_output(["aws", "s3", "cp", "s3://ay-dp-prod-data-inbound-nrm/{}".format(fname), lfname])

    src_dt = datetime.strptime(fnames[5].split(".")[4][1:], "%y%m%d")

    print("Unzipping...")
    try:
        subprocess.check_output(["gunzip", lfname])
    except Exception as e:
        print(e)
        subprocess.check_output(["rm", lfname])
        return

    tzf = TimezoneFinder()

    print("Generating csv...")
    lfnamewogz = lfname.rsplit(".", 1)[0]
    csv_fname = "INV_" + str(src_dt.year) + str(src_dt.month).zfill(2) + str(src_dt.day).zfill(2) + ".csv"
    csv_fname_fp = "/mnt/data/tmp/{}".format(csv_fname)
    bifReader = BIFReader(lfnamewogz)
    with open(csv_fname_fp, "w") as fout:
        csvwriter = csv.writer(fout)
        csvwriter.writerow(["CC", "FLTNUM", "DECOMPOSITION_DT", "DEPDT", "DEPTM", "DEPDT_UTC",
                            "DEPTM_UTC", "ARRDT", "ARRTM", "ARRDT_UTC", "ARRTM_UTC",
                            "ORGN", "DSTN", "DAYSPRIOR", "AIRCRAFT_TYPE", "CABIN",
                            "CAPS", "CAPA", "CAPO", "CAPE", "BKC", "ETB", "RC", "EGS",
                            "AMR", "RCR", "ESB", "SRC_DATE"])
        for l in bifReader.legs():
            depdt, deptm = l[3], l[4]
            dep_year, dep_month, dep_day = int(depdt[:4]), int(depdt[4:6]), int(depdt[6:8])
            dep_hour, dep_min = int(deptm[:2]), int(deptm[2:4])
            if dep_hour == 24:
                dep_hour = 0
            depdt = datetime(dep_year, dep_month, dep_day, dep_hour, dep_min)

            arrdt, arrtm = l[5], l[6]
            arr_year, arr_month, arr_day = int(arrdt[:4]), int(arrdt[4:6]), int(arrdt[6:8])
            arr_hour, arr_min = int(arrtm[:2]), int(arrtm[2:4])
            if arr_hour == 24:
                arr_hour = 0
            arrdt = datetime(arr_year, arr_month, arr_day, arr_hour, arr_min)

            orgn, dstn = l[7], l[8]
            """
            orgn_ap = Airport(orgn)
            dstn_ap = Airport(dstn)
            try:
                orgn_offset = orgn_ap.get_gmt_offset()
            except:
                print("orgn = {}".format(orgn))
                assert False
            try:
                dstn_offset = dstn_ap.get_gmt_offset()
            except:
                print("dstn = {}".format(dstn))
                assert False

            if orgn_offset.strip() != "":
                orgn_offset = float(orgn_offset)
                if orgn_offset > 0.0:
                    depdt_utc = depdt - timedelta(minutes=int(60 * orgn_offset))
                else:
                    depdt_utc = depdt + timedelta(minutes=int(60 * abs(orgn_offset)))

            if dstn_offset.strip() != "":
                dstn_offset = float(dstn_offset)
                if dstn_offset > 0.0:
                    arrdt_utc = arrdt - timedelta(minutes=int(60 * dstn_offset))
                else:
                    arrdt_utc = arrdt + timedelta(minutes=int(60 * abs(dstn_offset)))
            """

            def get_utc(dt, airport):
                ap = Airport(airport)
                lat = ap.get_latitude()
                lon = ap.get_longitude()
                tz = timezone(tzf.timezone_at(lng=lon, lat=lat))
                dt = tz.localize(dt)
                dt_utc = dt.astimezone(timezone("UTC"))
                return dt_utc

            depdt_utc = get_utc(depdt, orgn)
            arrdt_utc = get_utc(arrdt, dstn)

            depdt_utc_s = str(depdt_utc.year) + str(depdt_utc.month).zfill(2) + str(depdt_utc.day).zfill(2)
            deptm_utc_s = str(depdt_utc.hour) + str(depdt_utc.minute).zfill(2)
            arrdt_utc_s = str(arrdt_utc.year) + str(arrdt_utc.month).zfill(2) + str(arrdt_utc.day).zfill(2)
            arrtm_utc_s = str(arrdt_utc.hour) + str(arrdt_utc.minute).zfill(2)

            csvwriter.writerow([l[0], l[1], l[2], l[3], l[4], depdt_utc_s, deptm_utc_s,
                                l[5], l[6], arrdt_utc_s, arrtm_utc_s,
                                l[7], l[8], l[9], l[10], l[11], l[12], l[13],
                                l[14], l[15], l[16], l[17], l[18], l[19], l[20], l[21], l[22], l[23]])
    
    print("Zipping file...")
    try:
        subprocess.check_output(['gzip', csv_fname_fp]) 
    except Exception as e:
        print(e)
        subprocess.check_output(['rm', csv_fname_fp])
        return

    print("Copying file to s3...")
    subfolder = str(src_dt.year) + '/' + str(src_dt.month).zfill(2)
    s3fname = "s3://ay-rmp-home/nrm/bif/{}/{}.gz".format(subfolder, csv_fname)
    subprocess.check_output(["aws", "s3", "cp", csv_fname_fp+".gz", s3fname])

    print("Cleaning-up...")
    print(csv_fname + ".gz", lfname)
    subprocess.check_output(["rm", csv_fname_fp+".gz"])
    subprocess.check_output(["rm", lfnamewogz])


if __name__ == "__main__":
    # Get files in folder.
    fnames = gets3files("ay-dp-prod-data-inbound-nrm/boomi/bif/")

    # Filter out not BIF files.
    fnames = filter(lambda s: "PRD.NGI.BIF5.INV." in s, fnames)
    fnames = sorted(fnames, reverse=True)

    # Go over files and process them.
    for fname in fnames[:400]:
        # Check that file is already processed.
        dt = datetime.strptime(fname.rsplit('/',1)[1].split('.')[4][1:], "%y%m%d")
        csv2check = "ay-rmp-home/nrm/bif/" + str(dt.year) +\
                    "/" + str(dt.month).zfill(2) + "/INV_"+dt.strftime("%Y%m%d")+".csv.gz"
        if s3fileexists(csv2check):
            print(csv2check, "exists")
            continue
        process(fname)

    print("Done.")




