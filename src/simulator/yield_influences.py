def xiy_ckg_yld(row, yld):
    if row['BASE_OD_ORGN'] == 'XIY' or row['BASE_OD_ORGN'] == 'CKG' or\
       row['BASE_OD_DSTN'] == 'XIY' or row['BASE_OD_DSTN'] == 'CKG':
        if row['POS'] == 'CN' and row['BC'] == 'G':   
            return 0.5 * yld
    return yld

def partnership_base_yld(row, yld):
    return yld

def partnership_sce1_yld(row, yld):
    return yld

def partnership_sce2_yld(row, yld):
    return yld








































