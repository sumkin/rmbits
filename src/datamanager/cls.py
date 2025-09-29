import os
import sys
#import ConfigParser

'''
config = ConfigParser.RawConfigParser()
path_to_config = os.path.realpath(__file__).replace(os.path.basename(__file__),'../../../rw.cfg')
path_to_config = os.path.normpath(path_to_config)
config.read(path_to_config)

sys.path.append(config.get('PATHS','datamanager'))
'''

#from db_connector import dbConnector

classes = ['J','C','D','I','F','U',\
           'Y','B','H','K','M','P',\
           'T','L','V','S','N','G',\
           'A','Q','O','Z','R','W',\
           'X','E']

classes_wosc = ['J','C','D','I',\
                'Y','B','H','M','P',\
                'T','L','V','S','N',\
                'Q','O','Z','R','W']              

classes_j = ['J','C','D','I','F','U']
classes_j_wosc = ['J','C','D','I']

classes_y = ['Y','B','H','K','M','P',\
             'T','L','V','S','N','G',\
             'A','Q','O','Z','R','W',\
             'X','E']
classes_y_wosc = ['Y','B','H','K','M','P',\
                  'T','L','V','S','N','Q',\
                  'O','Z','R','W']


def is_special_cls(cls):
    if cls == 'F' or cls == 'U' or\
       cls == 'X' or cls == 'E' or\
       cls == 'G' or cls == 'A':
        return True
    return False


def get_bus_clss():
    return ['J','C','D','I','F','U']


def get_econ_clss():
    return ['Y','B','H','K','M','P',\
            'T','L','V','S','N','G',\
            'A','Q','O','Z','R','W',\
            'X','E']


def get_products():
    '''
    Returns dictionary where
    key is the name of product and
    value is the list of classes.
    '''
    res = {}

    # Business compartment
    res['BUS'] = ['J','C','D']
    res['BSAVER'] = ['I']
    res['BNREV'] = ['F','U']
  
    # Economy compartment
    res['PRO'] = ['Y','B','H']
    res['VALUE'] = ['K','M','P','T']
    res['BASIC'] = ['L','V','S','N','Q','O','Z','R']
    res['GROUPS'] = ['G','A']
    res['CAMP'] = ['W']
    res['ENREV'] = ['X','E']

    return res


def get_clss_():
    return classes


def get_cls_ind(cls):
    try:
        ind = classes.index(cls)
    except:
        ind = -1
    return ind


def get_cls_ind_j(cls):
    try:
        ind = classes_j.index(cls)
    except:
        ind = -1
    return ind


def get_cls_ind_y(cls):
    try:
        ind = classes_y.index(cls)
    except:
        ind = -1
    return ind


def get_cls_ind_j_wosc(cls):
    try:
        ind = classes_j_wosc.index(cls)
    except:
        ind = -1
    return ind


def get_cls_ind_y_wosc(cls):
    try:
        ind = classes_y_wosc.index(cls)
    except:
        ind = -1
    return ind


def get_upper_cls(cls):
    ind = get_cls_ind(cls)
    ind -= 1
    if ind < 0:
        return None
    try:
        return classes[ind]
    except:
        return None


def get_lower_cls(cls):
    ind = get_cls_ind(cls)
    ind += 1
    if ind >= len(classes):
        return None
    try:
        return classes[ind]
    except:
        return None


def cls_dist(cls1,cls2):
    ind1 = get_cls_ind(cls1)
    ind2 = get_cls_ind(cls2)
    return abs(ind1-ind2)
   

def get_closest(cls,clss):
    min_dist = 1000 # some big number
    ret_cls = None
    for c in clss:
        if get_cmpt(c) != get_cmpt(cls):
            continue
        if cls_dist(cls,c) < min_dist:
            min_dist = cls_dist(cls,c)
            ret_cls = c
    return [ret_cls,min_dist]


def get_cmpt(cls):
    if cls == 'J' or cls == 'C' or cls == 'D' or\
       cls == 'I' or cls == 'F' or cls == 'U':
        return 'J'

    if cls == 'Y' or cls == 'B' or cls == 'H' or\
       cls == 'K' or cls == 'M' or cls == 'P' or\
       cls == 'T' or cls == 'L' or cls == 'V' or\
       cls == 'S' or cls == 'N' or cls == 'G' or\
       cls == 'A' or cls == 'Q' or cls == 'O' or\
       cls == 'Z' or cls == 'R' or cls == 'W' or\
       cls == 'X' or cls == 'E':
        return 'Y' 


def get_clss():
    ret = []
    ret = ret + get_cmpt_clss('J')
    ret = ret + get_cmpt_clss('Y')
    return ret


def get_cls_color(cls):
    if cls == 'C':
        return 'CD5C5C'
    if cls == 'D':
        return '22AD12'
    if cls == 'F':
        return 'BB75A3'
    if cls == 'I':
        return 'FF0000'
    if cls == 'J':
        return '708090'
    if cls == 'U': 
        return 'DEB887'
    if cls == 'A': 
        return 'FF4500'
    if cls == 'B': 
        return '800080'
    if cls == 'E': 
        return '7CFC00'
    if cls == 'G': 
        return 'BDB76B'
    if cls == 'H': 
        return '008000'
    if cls == 'K':
        return '696969'
    if cls == 'L':
        return 'FFC0CB'
    if cls == 'M': 
        return '4682B4'
    if cls == 'N': 
        return '808000'
    if cls == 'O':
        return '2F4F4F'
    if cls == 'P': 
        return 'C00000'
    if cls == 'Q': 
        return '00BFFF'
    if cls == 'R':
        return '9370BB'
    if cls == 'S':
        return '00FFFF'
    if cls == 'T':
        return '2E8B57'
    if cls == 'V':
        return 'FFD700'
    if cls == 'W':
        return 'DC143C'
    if cls == 'X':
        return '008080'
    if cls == 'Y':
        return 'FF69B4'
    if cls == 'Z':
        return 'FFA387' 




