#from pyairport.airport import Airport

#ap = Airport()

"""
def au_influences(row, d):
    #
    # Jurgis influences for closing AU offices.
    #
    eps = 0.0000001
    alpha = 0.50
    if row['POS'] == 'AU' or row['POS'] == 'AVS':
        if row['GEO_ORGN'] == 'MEL':
            return alpha * d
        elif row['GEO_ORGN'] == 'SYD':
            return alpha * d
        elif row['GEO_ORGN'] == 'BNE':
            return alpha * d
        elif row['GEO_ORGN'] == 'PER':
            return alpha * d
        elif row['GEO_ORGN'] == 'CBR':
            return alpha * d
        elif row['GEO_ORGN'] == 'ADL':
            return alpha * d
        elif row['GEO_DSTN'] == 'MEL':
            return alpha * d
        elif row['GEO_DSTN'] == 'SYD':
            return alpha * d
        elif row['GEO_DSTN'] == 'BNE':
            return alpha * d
        elif row['GEO_DSTN'] == 'PER':
            return alpha * d
        elif row['GEO_DSTN'] == 'CBR':
            return alpha * d
        elif row['GEO_DSTN'] == 'ADL':
            return alpha * d 
    return d
"""

"""
def brexit_influences(row, d):
    #
    # Brexit.
    #
    eps = 0.0000001
    # 5th freedom.
    if str(row['BASE_OD_DEPT_DATE']) >= '20190329':
        if row['BASE_OD_ORGN_COUNTRY'] == 'GB' and row['BASE_OD_DSTN_COUNTRY'] == 'FI':
            geo_orgn = row['GEO_ORGN']
            if ap.get_cr(geo_orgn)[0] == 'US':
                print(row['BASE_OD_ORGN_COUNTRY'], row['BASE_OD_DSTN_COUNTRY'], 'erased')
                d = eps
        if row['BASE_OD_DSTN_COUNTRY'] == 'GB' and row['BASE_OD_ORGN_COUNTRY'] == 'FI':
            geo_dstn = row['GEO_DSTN']
            if ap.get_cr(geo_dstn)[0] == 'US':
                print(row['BASE_OD_ORGN_COUNTRY'], row['BASE_OD_DSTN_COUNTRY'], 'erased')
                d = eps

    # 6th freedom.
    if str(row['BASE_OD_DEPT_DATE']) >= '20190329':
        if row['BASE_OD_ORGN_COUNTRY'] == 'GB' and row['BASE_OD_DSTN_COUNTRY'] != 'FI':
            d = eps
        if row['BASE_OD_ORGN_COUNTRY'] != 'FI' and row['BASE_OD_DSTN_COUNTRY'] == 'GB':
            d = eps
        if row['BASE_OD_ORGN_COUNTRY'] == 'GB' and row['GEO_ORGN'] != 'LHR' and row['GEO_ORGN'] != 'MAN':
            d = eps
        if row['BASE_OD_DSTN_COUNTRY'] == 'GB' and row['GEO_DSTN'] != 'LHR' and row['GEO_DSTN'] != 'MAN':
            d = eps

    '''
    # Kalle's influences.
    try:
        infl = self.bdf[(self.bdf['ORGN'] == row['BASE_OD_ORGN']) &\
                        (self.bdf['DSTN'] == row['BASE_OD_DSTN'])]['INFL'].iloc[0]
        infl = float(infl)
        d = infl * d
    except Exception as e:
        pass
    '''

    # Antii's influences.
    pos = row['POS']
    rgn = ap.get_ayr(pos)

    depm = str(row['BASE_OD_DEPT_DATE'])[:6]            

    if depm == '201904':
        if pos == 'GB':
            d = (1 - 0.13) * d
        elif rgn == 'EUROPE':
            d = (1 - 0.09) * d
    elif depm == '201905':
        if pos == 'GB':
            d = (1 - 0.14) * d
        elif rgn == 'EUROPE':
            d = (1 - 0.09) * d
    elif depm == '201906':
        if pos == 'GB':
            d = (1 - 0.08) * d
        elif rgn == 'EUROPE':
            d = (1 - 0.07) * d
    elif depm == '201907':
        if pos == 'GB':
            d = (1 - 0.12) * d
        elif rgn == 'EUROPE':
            d = (1 - 0.08) * d
    elif depm == '201908':
        if pos == 'GB':
            d = (1 - 0.11) * d
        elif rgn == 'EUROPE':
            d = (1 - 0.08) * d
    elif depm == '201909':
        if pos == 'GB':
            d = (1 - 0.08) * d
        elif rgn == 'EUROPE':
            d = (1 - 0.07) * d
    elif depm == '201910':
        if pos == 'GB':
            d = (1 - 0.08) * d
        elif rgn == 'EUROPE':
            d = (1 - 0.07) * d
    elif depm == '201911':
        if pos == 'GB':
            d = (1 - 0.09) * d
        elif rgn == 'EUROPE':
            d = (1 - 0.07) * d
    elif depm == '201912':
        if pos == 'GB':
            d = (1 - 0.08) * d
        elif rgn == 'EUROPE':
            d = (1 - 0.07) * d
    elif depm == '202001':
        if pos == 'GB':
            d = (1 - 0.08) * d
        elif rgn == 'EUROPE':
            d = (1 - 0.07) * d
    elif depm == '202002':
        if pos == 'GB':
            d = (1 - 0.07) * d
        elif rgn == 'EUROPE':
            d = (1 - 0.06) * d
    elif depm == '202003':
        if pos == 'GB':
            d = (1 - 0.04) * d
        elif rgn == 'EUROPE':
            d = (1 - 0.05) * d
    elif depm == '202004':
        if pos == 'GB':
            d = (1 - 0.03) * d
        elif pos == 'EUROPE':
            d = (1 - 0.05) * d
    elif depm == '202005':
        if pos == 'GB':
            d = (1 - 0.02) * d
        elif pos == 'EUROPE':
            d = (1 - 0.04) * d
    return d
"""

def xiy_ckg_dmd(row, d):
    # row - row corresponding to forecasted flows.
    # d - original demand of the flow.
    if row['BASE_OD_ORGN'] == 'XIY' or row['BASE_OD_ORGN'] == 'CKG' or\
       row['BASE_OD_DSTN'] == 'XIY' or row['BASE_OD_DSTN'] == 'CKG':
        if row['POS'] == 'CN' and row['BC'] == 'G':
            return 1000
    return d   

def partnership_base_dmd(row, d):
    return d

def partnership_sce1_dmd(row, d):
    geo_orgn = row["GEO_ORGN"]
    geo_dstn = row["GEO_DSTN"]
    base_od_orgn = row["BASE_OD_ORGN"]
    base_od_dstn = row["BASE_OD_DSTN"]
    pos = row["POS"]

    is_offline = False
    if geo_orgn != base_od_orgn:
        is_offline = True
    if geo_dstn != base_od_dstn:
        is_offline = True

    is_pos_avs = False
    if pos == "AVS":
        is_pos_avs = True

    if is_offline or is_pos_avs:
        return 0
    else:
        return d

def partnership_sce2_dmd(row, d):
    geo_orgn = row["GEO_ORGN"]
    geo_dstn = row["GEO_DSTN"]
    base_od_orgn = row["BASE_OD_ORGN"]
    base_od_dstn = row["BASE_OD_DSTN"]
    pos = row["POS"]

    is_offline = False
    if geo_orgn != base_od_orgn:
        is_offline = True
    if geo_dstn != base_od_dstn:
        is_offline = True

    is_pos_avs = False
    if pos == "AVS":
        is_pos_avs = True

    is_pos_row = False
    if pos == "ROW":
        is_pos_row = True

    if is_offline or is_pos_avs or is_pos_row:
        return 0
    else:
        return d
