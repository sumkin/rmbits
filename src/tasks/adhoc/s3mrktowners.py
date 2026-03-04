import csv
import math
import pandas as pd
import numpy as np


df_raw = pd.read_csv('s3://ay-rmp-home/static/market_owners_raw.csv', skiprows=1, sep=';')
df_owners = df_raw[['Initials',\
                    'Origin Continent',\
                    'Origin Country',\
                    'Origin Subcountry Region',\
                    'Origin Country Excluded ',\
                    'Destination Continent',\
                    'Destination Country',\
                    'Destination Subcountry Region',\
                    ' Destination Country Excluded ',\
                    'POS Included',\
                    ' POS Excluded ']]
df_owners.columns = ['OWNER',\
                     'ORGN_CONTINENT',\
                     'ORGN_COUNTRY',\
                     'ORGN_SUBCOUNTRY',\
                     'ORGN_COUNTRY_EXCL',\
                     'DSTN_CONTINENT',\
                     'DSTN_COUNTRY',\
                     'DSTN_SUBCOUNTRY',\
                     'DSTN_COUNTRY_EXCL',\
                     'POSI',\
                     'POSE']

df_pos = pd.read_csv('s3://ay-rmp-home/static/POS.csv')
df_ap = pd.read_csv('s3://ay-rmp-home/static/ff_airports.csv', sep=';')

def cntnt_map(cntnt):
    '''
    Maps continent from Excel to corresponding
    continents from ff_airports.csv.
    '''
    if cntnt == 'Europe':
        return ['EUROP','EEURO','EURAS']
    elif cntnt == 'North America':
        return ['NAMER','ATLAN']
    elif cntnt == 'Asia':
        return ['ASIA','MEAST','SEASI','PACIF']
    elif cntnt == 'Oceania':
        return ['IOCEA','AUSTL']
    elif cntnt == 'South and Central America':
        return ['SAMER','CAMER','CARIB']
    else:
        assert False

def get_cntrs_for_cntnts(cntnts):
    '''
    Get all countries for list of continents.
    '''
    global df_ap

    res = []
    for cntnt in cntnts:
        df = df_ap.loc[df_ap['REGION_CODE'] == cntnt]
        for k,r in df.iterrows():
            res.append(r['COUNTRY_CODE'])    
    res = list(set(res))
    return res


def get_owner_poss_c2c(owner, orgn, dstn, posis, poses):
    '''
    Get owner pos for orgn and dstn country.
    FIXME: add country excluded.
    '''
    global df_pos

    res = []
    for kp,rp in df_pos.iterrows():
        pos = rp['POS']
            
        # Check that pos is excluded.
        nextpos = False
        for pose in poses:
            if pose == pos:
                nextpos = True
                break
            elif pose == 'Off':
                if pos == dstn:
                    nextpos = True
                    break
            elif pose == 'On':
                if pos == orgn:
                    nextpos = True
                    break
            elif pose == 'Others':
                if pos != orgn and pos != dstn:
                    nextpos = True
                    break
            else:
                assert False
        if nextpos:
            continue

        # Check that pos is included.
        for posi in posis:
            if posi == 'On':
                if pos == orgn:
                    res.append(pos)
            elif posi == 'Off':
                if pos == dstn:
                    res.append(pos)
            elif posi == 'Others':
                if pos != dstn or pos == 'ROW' or pos == 'AVS':
                    res.append(pos)
            elif posi == pos:
                res.append(pos)
            else:
                assert False
    res = list(set(res))
    return res


result = []
for ko,ro in df_owners.iterrows():
    owner = ro['OWNER'].strip()
    posis = [e.strip() for e in ro['POSI'].strip().split(',')]
    poses = [e.strip() for e in ro['POSE'].strip().split(',')]

    print 'owner,posis,poses = ', owner, posis, poses

    if not isinstance(ro['ORGN_COUNTRY'], float) and not isinstance(ro['DSTN_COUNTRY'], float):
        # Country to country case.
        assert isinstance(ro['ORGN_CONTINENT'], float)
        assert isinstance(ro['DSTN_CONTINENT'], float)
        assert isinstance(ro['ORGN_SUBCOUNTRY'], float)
        assert isinstance(ro['DSTN_SUBCOUNTRY'], float)

        orgn = ro['ORGN_COUNTRY'].strip()
        dstn = ro['DSTN_COUNTRY'].strip()
        print "Country to country", orgn, dstn

        owner_poss = get_owner_poss_c2c(owner, orgn, dstn, posis, poses) 
        for owner_pos in owner_poss:
            k = orgn+dstn+owner_pos
            result.append([owner, orgn, dstn, owner_pos, k])

        owner_poss = get_owner_poss_c2c(owner, dstn, orgn, poses, posis)
        for owner_pos in owner_poss:
            k = dstn+orgn+owner_pos
            result.append([owner, dstn, orgn, owner_pos, k])


    elif not isinstance(ro['ORGN_CONTINENT'], float) and not isinstance(ro['DSTN_CONTINENT'], float):   
        # Continent to continent case.
        assert isinstance(ro['ORGN_COUNTRY'], float)
        assert isinstance(ro['DSTN_COUNTRY'], float)
        assert isinstance(ro['ORGN_SUBCOUNTRY'], float)
        assert isinstance(ro['DSTN_SUBCOUNTRY'], float)

        orgn_cntnts = cntnt_map(ro['ORGN_CONTINENT'])
        dstn_cntnts = cntnt_map(ro['DSTN_CONTINENT'])
        orgn_cntrs = get_cntrs_for_cntnts(orgn_cntnts)
        dstn_cntrs = get_cntrs_for_cntnts(dstn_cntnts)
        print "Continent to continent", orgn_cntnts, dstn_cntnts
           
        owner_poss = []
        for orgn in orgn_cntrs:
            if orgn == ro['ORGN_COUNTRY_EXCL']:
                continue
            for dstn in dstn_cntrs:
                if dstn == ro['DSTN_COUNTRY_EXCL']:
                    continue
                print '\t',owner,orgn,dstn
                owner_poss = get_owner_poss_c2c(owner, orgn, dstn, posis, poses)
                for owner_pos in owner_poss:
                    k = orgn+dstn+owner_pos
                    result.append([owner, orgn, dstn, owner_pos, k])
                owner_poss = get_owner_poss_c2c(owner, dstn, orgn, poses, posis)
                for owner_pos in owner_poss:
                    k = dstn+orgn+owner_pos
                    result.append([owner, dstn, orgn, owner_pos, k])

    elif not isinstance(ro['ORGN_CONTINENT'], float) and not isinstance(ro['DSTN_COUNTRY'], float):
        # Continent to country case.
        assert isinstance(ro['ORGN_COUNTRY'], float)
        assert isinstance(ro['ORGN_SUBCOUNTRY'], float)
        assert isinstance(ro['DSTN_CONTINENT'], float)
        assert isinstance(ro['DSTN_SUBCOUNTRY'], float)

        orgn_cntnts = cntnt_map(ro['ORGN_CONTINENT'])
        orgn_cntrs = get_cntrs_for_cntnts(orgn_cntnts)
        dstn = ro['DSTN_COUNTRY']
        print "Continent to country", orgn_cntnts, dstn

        owner_poss = []
        for orgn in orgn_cntrs:
            if orgn == ro['ORGN_COUNTRY_EXCL']:
                continue
            print '\t',owner,orgn,dstn
            owner_poss = get_owner_poss_c2c(owner, orgn, dstn, posis, poses)
            for owner_pos in owner_poss:
                k = orgn+dstn+owner_pos
                result.append([owner, orgn, dstn, owner_pos, k])

            owner_poss = get_owner_poss_c2c(owner, dstn, orgn, poses, posis)
            for owner_pos in owner_poss:
                k = dstn+orgn+owner_pos
                result.append([owner, dstn, orgn, owner_pos, k])

    elif not isinstance(ro['ORGN_COUNTRY'], float) and not isinstance(ro['DSTN_CONTINENT'], float):
        # Country to continent case.
        assert isinstance(ro['ORGN_CONTINENT'], float)
        assert isinstance(ro['ORGN_SUBCOUNTRY'], float)
        assert isinstance(ro['DSTN_COUNTRY'], float)
        assert isinstance(ro['DSTN_SUBCOUNTRY'], float)

        dstn_cntnts = cntnt_map(ro['DSTN_CONTINENT'])
        dstn_cntrs = get_cntrs_for_cntnts(dstn_cntnts)
        orgn = ro['ORGN_COUNTRY']
        print "Country to continent", orgn, dstn_cntnts

        owner_poss = []
        for dstn in dstn_cntrs:
            if dstn == ro['DSTN_COUNTRY_EXCL']:
                continue
            # Fix for entry Europe excluding LAP (Lapland).
            if dstn == 'FI' and ro['DSTN_COUNTRY_EXCL'] == 'LAP':
                dstn = 'NLP'
            print '\t',owner,orgn,dstn
            owner_poss = get_owner_poss_c2c(owner, orgn, dstn, posis, poses)
            for owner_pos in owner_poss:
                k = orgn+dstn+owner_pos
                result.append([owner, orgn, dstn, owner_pos, k])

            owner_poss = get_owner_poss_c2c(owner, dstn, orgn, poses, posis)
            for owner_pos in owner_poss:
                k = dstn+orgn+owner_pos
                result.append([owner, dstn, orgn, owner_pos, k])
    else:
        print ro     

print 'Writing CSV file...' 
with open('market_owners.csv', 'w') as fout:
    cw = csv.writer(fout)
    cw.writerow(['OWNER','ORGN','DSTN','POS','KEY'])
    for r in result:
        cw.writerow(r)





 
          
