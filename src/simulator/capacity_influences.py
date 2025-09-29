def cap_35A_to_35B(r, cap):
    if r['CABIN'] == 'J':
        if r['CAPS'] == 46:
            print(r['CC'],r['FLTNUM'],r['DEPDT'],r['ORGN'],r['DSTN'],r['CABIN'],r['CAPS'],' capacity changed 32')
            return 32    
    elif r['CABIN'] == 'Y':
        if r['CAPS'] == 251:
            print(r['CC'],r['FLTNUM'],r['DEPDT'],r['ORGN'],r['DSTN'],r['CABIN'],r['CAPS'],' capacity changed to 304')
            return 304
    return cap

def xiy_ckg_cap(r, cap):
    if r['ORGN'] == 'XIY' or r['ORGN'] == 'CKG' or\
       r['DSTN'] == 'XIY' or r['DSTN'] == 'CKG':
        if r['CABIN'] == 'J':
            return 20
        elif r['CABIN'] == 'Y':
            return 360
        else:
            assert False
    return cap

def partnership_base_cap(r, cap):
    return cap

def partnership_sce1_cap(r, cap):
    return cap

def partnership_sce2_cap(r, cap):
    return cap
