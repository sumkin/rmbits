from datetime import datetime, timedelta

cur_date = datetime.now()

def dmd_factor(dep_date, dtd_to, dtd_from, source_date):
    DELTA = (dep_date - cur_date).days

    if dtd_to <= DELTA and DELTA <= dtd_from:
        delta = (dep_date - source_date).days
        mdtd1 = -dtd_to + 1
        if dtd_to <= delta and delta <= dtd_from:
            #res = (DELTA - f1(dtd_to) + 1) / (delta - dtd_to + 1)
            res = (DELTA + 0.5 if dtd_to == 0 else mdtd1) / (delta + mdtd1)
        else:
            #res = (DELTA - f1(dtd_to) + 1) / (dtd_from - dtd_to + 1)
            res = (DELTA + 0.5 if dtd_to == 0 else mdtd1) / (dtd_from + mdtd1)
    elif DELTA > dtd_from:
        res = 1.0
    elif DELTA < dtd_to:
        res = 0.0
    else:
        res = 0.0
    return res

def gc_dmd_factor(dep_date, dtd_to, dtd_from, source_date):
    cur_date = datetime.now()
    DELTA = (dep_date - cur_date).days
         
    if dtd_to <= DELTA and DELTA <= dtd_from:
        return (DELTA - f1(dtd_to) + 1) / (dtd_from - f2(dtd_to) + 1)
    elif DELTA > dtd_from:
        return 1.0
    elif DELTA < dtd_to:
        return 0.0
    else:
        return 0.0

def get_decomposition_dt(orgn, dstn, depdt, deptm, arrdt, arrtm):
    if orgn == "HEL":
        if int(deptm) < 300:
            return datetime.strftime(depdt - timedelta(days=1), "%Y%m%d")
        else:
            return datetime.strftime(depdt, "%Y%m%d")
    elif dstn == "HEL":
        if int(arrtm) < 300:
            return datetime.strftime(arrdt - timedelta(days=1), "%Y%m%d")
        else:
            return datetime.strftime(arrdt, "%Y%m%d")
    else:
        if int(deptm) < 300:
            return datetime.strftime(depdt - timedelta(days=1), "%Y%m%d")
        else:
            return datetime.strftime(depdt, "%Y%m%d")


     
    
