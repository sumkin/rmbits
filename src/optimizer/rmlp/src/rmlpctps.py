from ctypes import *


class c_PosVal(Structure):
    pass


c_PosVal._fields_ = [('pos', c_uint),
                     ('val', c_double),
                     ('p_next', POINTER(c_PosVal))]


class c_SmplxTblRow(Structure):
    _fields_ = [('p_posval', POINTER(c_PosVal)),
                ('num', c_uint)]


class c_SmplxTblClmn(Structure):
    _fields_ = [('p_posval', POINTER(c_PosVal)),
                ('num', c_uint)]


class c_SmplxTbl(Structure):
    _fields_ = [('nrows', c_uint),
                ('ncols', c_uint),
                ('p_rhs', POINTER(c_double)),
                ('p_lr', POINTER(c_double)),
                ('v', c_double),
                ('p_bvars', POINTER(c_uint)),
                ('p_nbvars', POINTER(c_uint)),
                ('p_rows', POINTER(c_SmplxTblRow)),
                ('p_cols', POINTER(c_SmplxTblClmn))]





