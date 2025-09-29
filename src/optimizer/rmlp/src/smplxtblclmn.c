#include "smplxtblclmn.h"

SmplxTblClmn* smplxtblclmn_init() {
    SmplxTblClmn* p_res = malloc(sizeof(SmplxTblClmn));
    p_res->num = 0;
    return p_res;
}

//#define DEBUG_CLMN_SET

void smplxtblclmn_set(SmplxTblClmn* p_col, uint pos, double v) {
    if (p_col->num == 0) {
        p_col->p_posval = malloc(sizeof(PosVal));
        p_col->p_posval->pos = pos;
        p_col->p_posval->val = v;
        p_col->p_posval->p_next = NULL;
        p_col->num++;
    }
    else {
        PosVal* prev_p_posval = p_col->p_posval;
        PosVal* p_posval = prev_p_posval->p_next;
        while (p_posval != NULL) {
            //assert(prev_p_posval->pos < p_posval->pos);
            if (pos < prev_p_posval->pos) {
                assert(prev_p_posval != NULL);
                PosVal* p_new_posval = malloc(sizeof(PosVal));
                p_new_posval->pos = pos;
                p_new_posval->val = v;
                p_new_posval->p_next = prev_p_posval;
                p_col->p_posval = p_new_posval;
                p_col->num++;
                return;
            }
            if (prev_p_posval->pos == pos) {
                prev_p_posval->val = v;
                return;
            }
            if (prev_p_posval->pos < pos && pos < p_posval->pos) {
                PosVal* p_new_posval = malloc(sizeof(PosVal));
                p_new_posval->pos = pos;
                p_new_posval->val = v;
                p_new_posval->p_next = p_posval;
                prev_p_posval->p_next = p_new_posval;
                p_col->num++;
                return;
            }
            if (p_posval->pos == pos) {
                p_posval->val = v;
                return;
            }
            prev_p_posval = p_posval;
            p_posval = prev_p_posval->p_next;
        }
        //assert(prev_p_posval != NULL);
        if (pos < prev_p_posval->pos) {
            PosVal* p_new_posval = malloc(sizeof(PosVal));
            p_new_posval->pos = pos;
            p_new_posval->val = v;
            p_new_posval->p_next = prev_p_posval;
            p_col->num++;
            p_col->p_posval = p_new_posval;
            return;
        }
        if (pos == prev_p_posval->pos) {
            prev_p_posval->val = v;
            return;
        }
        if (pos > prev_p_posval->pos) {
            PosVal* p_new_posval = malloc(sizeof(PosVal));
            p_new_posval->pos = pos;
            p_new_posval->val = v;
            p_new_posval->p_next = NULL;
            prev_p_posval->p_next = p_new_posval;
            p_col->num++;
            return;
        }
    }
}

double smplxtblclmn_set_zero(SmplxTblClmn* p_col, uint pos) {
    if (p_col->num == 0) {
        return 0;
    }
    else {
        PosVal* prev_p_posval = p_col->p_posval;
        PosVal* p_posval = prev_p_posval->p_next;
        while (p_posval != NULL) {
            if (pos < prev_p_posval->pos) {
                return 0;
            }
            if (prev_p_posval->pos == pos) {
                double v = prev_p_posval->val;
                prev_p_posval->val = 0;
                return v;
            }
            if (prev_p_posval->pos < pos && pos < p_posval->pos) {
                return 0;
            }
            if (p_posval->pos == pos) {
                double v = p_posval->val;
                p_posval->val = 0;
                return v;
            }
            prev_p_posval = p_posval;
            p_posval = prev_p_posval->p_next;
        }
        if (pos < prev_p_posval->pos) {
            return 0;
        }
        if (pos == prev_p_posval->pos) {
            double v = prev_p_posval->val;
            prev_p_posval->val = 0;
            return v;
        }
        if (pos > prev_p_posval->pos) {
            return 0;
        }
    }
}

void smplxtblclmn_divide(SmplxTblClmn* p_col, uint pos, double v) {
    if (p_col->num == 0) {
        return;
    }
    else {
        PosVal* prev_p_posval = p_col->p_posval;
        PosVal* p_posval = prev_p_posval->p_next;
        while (p_posval != NULL) {
            if (pos < prev_p_posval->pos) {
                return;
            }
            if (prev_p_posval->pos == pos) {
                prev_p_posval->val /= v;
                return;
            }
            if (prev_p_posval->pos < pos && pos < p_posval->pos) {
                return;
            }
            if (p_posval->pos == pos) {
                p_posval->val /= v;
                return;
            }
            prev_p_posval = p_posval;
            p_posval = prev_p_posval->p_next;
        }
        if (pos < prev_p_posval->pos) {
            return;
        }
        if (pos == prev_p_posval->pos) {
            prev_p_posval->val /= v;
            return;
        }
        if (pos > prev_p_posval->pos) {
            return;
        }
    }
}

void smplxtblclmn_add(SmplxTblClmn* p_col, uint pos, double v) {
    if (p_col->num == 0) {
        p_col->p_posval = malloc(sizeof(PosVal));
        p_col->p_posval->pos = pos;
        p_col->p_posval->val = v;
        p_col->p_posval->p_next = NULL;
        p_col->num++;
    }
    else {
        PosVal* prev_p_posval = p_col->p_posval;
        PosVal* p_posval = prev_p_posval->p_next;
        while (p_posval != NULL) {
            if (pos < prev_p_posval->pos) {
                PosVal* p_new_posval = malloc(sizeof(PosVal));
                p_new_posval->pos = pos;
                p_new_posval->val = v;
                p_new_posval->p_next = prev_p_posval;
                p_col->p_posval = p_new_posval;
                p_col->num++;
                return;
            }
            if (prev_p_posval->pos == pos) {
                prev_p_posval->val += v;
                return;
            }
            if (prev_p_posval->pos < pos && pos < p_posval->pos) {
                PosVal* p_new_posval = malloc(sizeof(PosVal));
                p_new_posval->pos = pos;
                p_new_posval->val = v;
                p_new_posval->p_next = p_posval;
                prev_p_posval->p_next = p_new_posval;
                p_col->num++;
                return;
            }
            if (p_posval->pos == pos) {
                p_posval->val += v;
                return;
            }
            prev_p_posval = p_posval;
            p_posval = prev_p_posval->p_next;
        }
        if (pos < prev_p_posval->pos) {
            PosVal* p_new_posval = malloc(sizeof(PosVal));
            p_new_posval->pos = pos;
            p_new_posval->val = v;
            p_new_posval->p_next = prev_p_posval;
            p_col->num++;
            p_col->p_posval = p_new_posval;
            return;
        }
        if (pos == prev_p_posval->pos) {
            prev_p_posval->val += v;
            return;
        }
        if (pos > prev_p_posval->pos) {
            PosVal* p_new_posval = malloc(sizeof(PosVal));
            p_new_posval->pos = pos;
            p_new_posval->val = v;
            p_new_posval->p_next = NULL;
            prev_p_posval->p_next = p_new_posval;
            p_col->num++;
            return;
        }
    }
}



double smplxtblclmn_at(const SmplxTblClmn* p_col, uint pos) {
    PosVal* p_posval = p_col->p_posval;
    for (uint i = 0; i < p_col->num; i++) {
        if (p_posval->pos == pos) return p_posval->val;
        p_posval = p_posval->p_next;
    }
    return 0;
}


PosVal* smplxtblclmn_nullify(SmplxTblClmn* p_col, uint pos) {
    PosVal* prev_p_posval = NULL;
    PosVal* p_posval = p_col->p_posval;
    while (p_posval != NULL) {
        if (p_posval->pos == pos) {
            PosVal* res = p_posval->p_next;
            if (prev_p_posval != NULL) {
                prev_p_posval->p_next = p_posval->p_next;
                p_col->num--;
                free(p_posval);
            }
            else {
                p_col->p_posval = p_posval->p_next;
                p_col->num--;
                free(p_posval);
            }
            return res;
        }
        prev_p_posval = p_posval;
        p_posval = p_posval->p_next;
    }
    assert(false);
}


void smplxtblclmn_find_and_nullify(SmplxTblClmn* p_col) {
    PosVal* p_posval = p_col->p_posval;
    while (p_posval != NULL) {
        if (fabs(p_posval->val) <= EPS) {
            p_posval = smplxtblclmn_nullify(p_col, p_posval->pos);
        }
        else {
            p_posval = p_posval->p_next;
        }
    }
}


uint smplxtblclmn_nzero_num(SmplxTblClmn* p_col) {
    return p_col->num;
}


void smplxtblclmn_free(SmplxTblClmn* p_col) {
    uint i;
    PosVal* p_res = p_col->p_posval; 
    for (i = 0; i < p_col->num; i++) {
        PosVal* p_tofree = p_res;
        p_res = p_res->p_next;
        free(p_tofree);
    }
    free(p_col);    
}


