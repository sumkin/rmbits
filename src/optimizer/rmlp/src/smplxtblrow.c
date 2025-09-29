#include "smplxtblrow.h"


SmplxTblRow* smplxtblrow_init() {
    SmplxTblRow* p_res = malloc(sizeof(SmplxTblRow));
    p_res->p_posval = NULL;
    p_res->num = 0;
    return p_res;
}

//#define DEBUG_ROW_SET

void smplxtblrow_set(SmplxTblRow* p_row, uint pos, double v) {
    if (p_row->num == 0) {
        p_row->p_posval = malloc(sizeof(PosVal));
        p_row->p_posval->pos = pos;
        p_row->p_posval->val = v;
        p_row->p_posval->p_next = NULL;
        p_row->num++;
    }
    else {
        PosVal* prev_p_posval = p_row->p_posval;
        PosVal* p_posval = prev_p_posval->p_next;
        while (p_posval != NULL) {
            if (pos < prev_p_posval->pos) {
                PosVal* p_new_posval = malloc(sizeof(PosVal));
                p_new_posval->pos = pos;
                p_new_posval->val = v;
                p_new_posval->p_next = prev_p_posval;
                p_row->p_posval = p_new_posval;
                p_row->num++;
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
                p_row->num++;
                return;
            }
            if (p_posval->pos == pos) {
                p_posval->val = v;
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
            p_row->num++;
            p_row->p_posval = p_new_posval;
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
            p_row->num++;
            return;
        }
    }
}

double smplxtblrow_set_zero(SmplxTblRow* p_row, uint pos) {
    if (p_row->num == 0) {
        return 0;
    }
    else {
        PosVal* prev_p_posval = p_row->p_posval;
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


void smplxtblrow_divide(SmplxTblRow* p_row, uint pos, double v) {
    if (p_row->num == 0) {
        return;
    }
    else {
        PosVal* prev_p_posval = p_row->p_posval;
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



void smplxtblrow_add(SmplxTblRow* p_row, uint pos, double v) {
    if (p_row->num == 0) {
        p_row->p_posval = malloc(sizeof(PosVal));
        p_row->p_posval->pos = pos;
        p_row->p_posval->val = v;
        p_row->p_posval->p_next = NULL;
        p_row->num++;
    }
    else {
        PosVal* prev_p_posval = p_row->p_posval;
        PosVal* p_posval = prev_p_posval->p_next;
        while (p_posval != NULL) {
            if (pos < prev_p_posval->pos) {
                PosVal* p_new_posval = malloc(sizeof(PosVal));
                p_new_posval->pos = pos;
                p_new_posval->val = v;
                p_new_posval->p_next = prev_p_posval;
                p_row->p_posval = p_new_posval;
                p_row->num++;
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
                p_row->num++;
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
            p_row->num++;
            p_row->p_posval = p_new_posval;
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
            p_row->num++;
            return;
        }
    }
}



double smplxtblrow_at(const SmplxTblRow* p_row, uint pos) {
    PosVal* p_posval = p_row->p_posval;
    for (uint i = 0; i < p_row->num; i++) {
        if (p_posval->pos == pos)  return p_posval->val;
        p_posval = p_posval->p_next;
    }    
    return 0;
}


PosVal* smplxtblrow_nullify(SmplxTblRow* p_row, uint pos) {
    PosVal* prev_p_posval = NULL;
    PosVal* p_posval = p_row->p_posval;
    while (p_posval != NULL) {
        if (p_posval->pos == pos) {
            PosVal* res = p_posval->p_next;
            if (prev_p_posval != NULL) {
                prev_p_posval->p_next = p_posval->p_next;
                p_row->num--;
                free(p_posval);
            }
            else {
                p_row->p_posval = p_posval->p_next;
                p_row->num--;
                free(p_posval);
            }
            return res;
        }
        prev_p_posval = p_posval; 
        p_posval = p_posval->p_next;
    }
    assert(false);
}


void smplxtblrow_find_and_nullify(SmplxTblRow* p_row) {
    PosVal* p_posval = p_row->p_posval;
    while (p_posval != NULL) {
        if (fabs(p_posval->val) <= EPS) {
            p_posval = smplxtblrow_nullify(p_row, p_posval->pos);
        }
        else {
            p_posval = p_posval->p_next;
        }
    }
}


uint smplxtblrow_nzero_num(SmplxTblRow* p_row) {
    return p_row->num;
}


void smplxtblrow_free(SmplxTblRow* p_row) {
    uint i;
    PosVal* p_res = p_row->p_posval;
    for (i = 0; i < p_row->num; i++) {
        PosVal* p_tofree = p_res;
        p_res = p_res->p_next;
        free(p_tofree);
    }
    free(p_row);
}




