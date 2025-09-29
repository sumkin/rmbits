#include "smplxtbl.h"

//#define DEBUG

SmplxTbl* smplxtbl_init(uint nrows, uint ncols) {

#ifdef DEBUG
    printf("smplxtbl_init() called.\n");
#endif

    SmplxTbl* p_st = malloc(sizeof(SmplxTbl));
    assert(p_st != NULL);

    p_st->nrows = nrows;
    p_st->ncols = ncols;

    p_st->p_rhs = malloc(nrows * sizeof(double));
    memset(p_st->p_rhs, 0, nrows * sizeof(double));

    p_st->p_lr = malloc(ncols * sizeof(double));
    memset(p_st->p_lr, 0, ncols * sizeof(double)); 

    p_st->v = 0;
    p_st->p_basis  = malloc(nrows * sizeof(SmplxBasisElement));
    p_st->p_nbvars = malloc((ncols - nrows) * sizeof(uint));

    p_st->p_cols = malloc(ncols * sizeof(SmplxTblClmn));
    memset(p_st->p_cols, 0, ncols * sizeof(SmplxTblClmn));
 
    p_st->p_rows = malloc(nrows * sizeof(SmplxTblRow));
    memset(p_st->p_rows, 0, nrows * sizeof(SmplxTblRow));

#ifdef DEBUG
    printf("smplxtbl_init() finished.\n");
#endif
    return p_st;
}


double smplxtbl_get_rhs(const SmplxTbl* p_st, uint i) {
    return p_st->p_rhs[i];
}


void smplxtbl_set_rhs(SmplxTbl* p_st, uint i, double v) {
    p_st->p_rhs[i] = v;
}


double smplxtbl_get_m(const SmplxTbl* p_st, uint i, uint j) {
    return smplxtblclmn_at(&p_st->p_cols[j], i);
    //return smplxtblrow_at(&p_st->p_rows[i], j);
}


void smplxtbl_set_m(SmplxTbl* p_st, uint i, uint j, double v) {
    smplxtblrow_set(&p_st->p_rows[i], j, v);
    smplxtblclmn_set(&p_st->p_cols[j], i, v); 
}

double smplxtbl_set_m_zero(SmplxTbl* p_st, uint i, uint j) {
    smplxtblrow_set_zero(&p_st->p_rows[i], j);
    return smplxtblclmn_set_zero(&p_st->p_cols[j], i);
}

void smplxtbl_add_m(SmplxTbl* p_st, uint i, uint j, double v) {
    smplxtblrow_add(&p_st->p_rows[i], j, v);
    smplxtblclmn_add(&p_st->p_cols[j], i, v);
}

void smplxtbl_divide_m(SmplxTbl* p_st, uint i, uint j, double v) {
    smplxtblrow_divide(&p_st->p_rows[i], j, v);
    smplxtblclmn_divide(&p_st->p_cols[j], i, v);
}


void smplxtbl_nullify(SmplxTbl* p_st, uint i, uint j) {
    smplxtblrow_nullify(&p_st->p_rows[i], j);
    smplxtblclmn_nullify(&p_st->p_cols[j], i);
}


void smplxtbl_find_and_nullify(SmplxTbl* p_st) {
    for (uint i = 0; i < p_st->nrows; i++) {
        smplxtblrow_find_and_nullify(&p_st->p_rows[i]);
    }
    for (uint j = 0; j < p_st->ncols; j++) {
        smplxtblclmn_find_and_nullify(&p_st->p_cols[j]);
    }
}


double smplxtbl_get_lr(const SmplxTbl* p_st, uint i) {
    return p_st->p_lr[i];
}


void smplxtbl_set_lr(SmplxTbl* p_st, uint i, double v) {
    p_st->p_lr[i] = v;
}


bool smplxtbl_init_slack_basis(SmplxTbl* p_st) {
#ifdef DEBUG
    printf("smplxtbl_init_slack_basis() called.\n");
#endif

    // For each row find the column with one non-zero eleemnt.
    for (uint i = 0; i < p_st->nrows; i++) {
        bool found = false;
        for (uint j = 0; j < p_st->ncols; j++) {
            SmplxTblClmn* p_col = &p_st->p_cols[j];
            if (p_col->num == 1) {
                if (p_col->p_posval->pos == i) {
                    assert(fabs(p_col->p_posval->val - 1) <= EPS);
                    p_st->p_basis[i].varidx = j;
                    p_st->p_basis[i].rowidx = i;
                    found = true;
                    break;
                }
            }
        }
        if (!found) {
            return false;
        }
    }

    // Fill non-basis variables. 
    uint num = 0;
    for (uint i = 0; i < p_st->ncols; i++) {
        if (!smplxtbl_is_basis(p_st, i)) {
            p_st->p_nbvars[num] = i;
            num++;    
        }
    }
    assert(num == (p_st->ncols - p_st->nrows));
#ifdef DEBUG
    printf("smplxtbl_init_slack_basis() finished.\n"); 
    smplxtbl_print_basis(p_st);
#endif
    return true;
}


uint smplxtbl_find_enter_var(SmplxTbl* p_st) {
    // Go over non basic variables and find maximum.
    uint j;
    uint maxj;
    double maxv = 0;
    for (j = 0; j < p_st->ncols - p_st->nrows; j++) {
        uint idx = p_st->p_nbvars[j];
        if (p_st->p_lr[idx] > maxv) {
            maxj = idx;
            maxv = p_st->p_lr[idx];   
        }
    }
    if (maxv == 0) return INT_MAX;
    return maxj;
}


bool smplxtbl_find_leave_var(const SmplxTbl* p_st, uint j, SmplxBasisElement* p_be) {
    // Go over column and find minimum ratio of rhs to 
    // to element conditional on positiviness.
    SmplxTblClmn* p_col = &p_st->p_cols[j];

    uint ridx = INT_MAX;
    double minr = DBL_MAX;

    uint i;
    PosVal* p_posval = p_col->p_posval;
    for (i = 0; i < p_col->num; i++) {
        if (fabs(p_posval->val - 1) < EPS) {
            double rhs = p_st->p_rhs[p_posval->pos];
            if (rhs < minr) {
                minr = rhs;
                ridx = p_posval->pos;
            }
        }
        else if (p_posval->val > 0) {
            double rhs = p_st->p_rhs[p_posval->pos];
            if (rhs / p_posval->val < minr) {
                minr = rhs / p_posval->val;
                ridx = p_posval->pos;
            } 
        }
        if (i != p_col->num - 1) {
            p_posval = p_posval->p_next;
        }
    }   
    uint varidx = INT_MAX;
    for (uint i = 0; i < p_st->nrows; i++) {
        if (p_st->p_basis[i].rowidx == ridx) {
            varidx = p_st->p_basis[i].varidx;
        }
    }
    if (varidx == INT_MAX) return false;
    assert(varidx < INT_MAX);
    p_be->varidx = varidx;
    p_be->rowidx = ridx; 
    return true;
}

//#define DEBUG_PIVOT

void smplxtbl_pivot(SmplxTbl* p_st, uint newvaridx, SmplxBasisElement* p_be) {
    uint ipvt = p_be->rowidx;
    uint jpvt = newvaridx;

    double pv = smplxtbl_get_m(p_st, ipvt, jpvt);

    // Update pivot rows and right-hand side.
    double rhsvpvt = smplxtbl_get_rhs(p_st, ipvt);
    if (fabs(pv - 1) > EPS) {
        PosVal* p_posval = p_st->p_rows[ipvt].p_posval;
        while (p_posval != NULL) {
            smplxtbl_divide_m(p_st, ipvt, p_posval->pos, pv);
            p_posval = p_posval->p_next;
        }
        rhsvpvt = rhsvpvt / pv;
        smplxtbl_set_rhs(p_st, ipvt, rhsvpvt);
    }

    // Nullify pivot column.
    PosVal* p_cposval = p_st->p_cols[jpvt].p_posval;
    while (p_cposval != NULL) {
        if (p_cposval->pos != ipvt) {
            double cv = smplxtbl_set_m_zero(p_st, p_cposval->pos, jpvt);            

            PosVal* p_rposval = p_st->p_rows[ipvt].p_posval;
            while (p_rposval != NULL) {
                if (p_rposval->pos != jpvt) {
                    double rv = smplxtbl_get_m(p_st, ipvt, p_rposval->pos);
                    smplxtbl_add_m(p_st, p_cposval->pos, p_rposval->pos, -rv * cv);
                }
                p_rposval = p_rposval->p_next;
            }
            double rhsv = smplxtbl_get_rhs(p_st, p_cposval->pos);
            smplxtbl_set_rhs(p_st, p_cposval->pos, rhsv - cv * rhsvpvt);
        }
        p_cposval = p_cposval->p_next;
    }

    // Update last row.
    double cv = smplxtbl_get_lr(p_st, jpvt);
    PosVal* p_rposval = p_st->p_rows[ipvt].p_posval;
    while (p_rposval != NULL) {
        double rv = smplxtbl_get_m(p_st, ipvt, p_rposval->pos);
        if (p_rposval->pos != jpvt) {
            double v = smplxtbl_get_lr(p_st, p_rposval->pos);
            smplxtbl_set_lr(p_st, p_rposval->pos, v - rv * cv);
        }
        else {
            smplxtbl_set_lr(p_st, p_rposval->pos, 0);
        }
        p_rposval = p_rposval->p_next;
    }

    // Update value.
    p_st->v = p_st->v - rhsvpvt * cv;

    // Nullify zero elements.
    smplxtbl_find_and_nullify(p_st);

    // Update basis.
    smplxtbl_replace_var_in_basis(p_st, newvaridx, p_be->rowidx, p_be->varidx);
}


bool smplxtbl_is_basis(SmplxTbl* p_st, uint j) {
    uint i;
    for (i = 0; i < p_st->nrows; i++) {
        if (p_st->p_basis[i].varidx == j) return true;
    }
    return false;
}


void smplxtbl_replace_var_in_basis(SmplxTbl* p_st, uint newvaridx, uint newrowidx, uint oldvaridx) {
    uint foundIdx = INT_MAX;
    for (uint k = 0; k < p_st->nrows; k++) {
        if (p_st->p_basis[k].varidx == oldvaridx) {
            foundIdx = k;
            p_st->p_basis[foundIdx].varidx = newvaridx;
            p_st->p_basis[foundIdx].rowidx = newrowidx;
            break;
        }
    }
    //assert(foundIdx < INT_MAX);

    foundIdx = INT_MAX;
    for (uint k = 0; k < p_st->ncols - p_st->nrows; k++) {
        if (p_st->p_nbvars[k] == newvaridx) {
            foundIdx = k;
            p_st->p_nbvars[foundIdx] = oldvaridx;
            break;
        }
    }
    //assert(foundIdx < INT_MAX); 
}


void smplxtbl_print(const SmplxTbl* p_st) {
    for (uint i = 0; i < p_st->nrows; i++) {
        for (uint j = 0; j < p_st->ncols; j++) {
            double v = smplxtbl_get_m(p_st, i, j);
            printf("%f ", v);
        }
        printf("| %f", smplxtbl_get_rhs(p_st, i)); 
        printf("\n");
    }
    printf("==============================\n");
    for (uint j = 0; j < p_st->ncols; j++) {
        double v = smplxtbl_get_lr(p_st, j);
        printf("%f ", v);
    }
    printf("| %f\n", p_st->v); 
    smplxtbl_print_basis(p_st);
    printf("\n\n");
}


void smplxtbl_print_basis(const SmplxTbl* p_st) {
    printf("Basis: ");
    for (uint i = 0; i < p_st->nrows; i++) {
        printf("%d ", p_st->p_basis[i].varidx);
    }    
    printf("\n");
}


double smplxtbl_get_value(const SmplxTbl* p_st) {
    return -p_st->v;
}


double smplxtbl_get_sol(const SmplxTbl* p_st, uint ci) {
    for (uint i = 0; i < p_st->nrows; i++) {
        if (ci == p_st->p_basis[i].varidx) {
            return smplxtbl_get_rhs(p_st, p_st->p_basis[i].rowidx);
        }
    }
    return 0.0;
}


bool smplxtbl_check_basis(const SmplxTbl* p_st) {
    for (uint i = 0; i < p_st->nrows; i++) {
        const SmplxBasisElement* p_be = &p_st->p_basis[i];

        SmplxTblClmn* p_clmn = &p_st->p_cols[p_be->varidx];
        // Check that only one element is in basis column.
        if (p_clmn->num != 1) {
            printf("varidx = %d, p_clmn->num = %d\n", p_be->varidx, p_clmn->num);
            return false;
        }
        // Check that element is equal 1.
        if (fabs(p_clmn->p_posval->val - 1) > EPS) {
            printf("p_clmn->p_posval->val = %f\n", p_clmn->p_posval->val);
            return false;
        }
    }
    return true;
}


bool smplxtbl_basis_feasible(const SmplxTbl* p_st) {
    // Check that right-hand side corresponding to basis is non-negative.
    for (uint i = 0; i < p_st->nrows; i++) {
        const SmplxBasisElement* p_be = &p_st->p_basis[i];
        uint ridx = p_be->rowidx;
        double rhsv = smplxtbl_get_rhs(p_st, ridx);
        if (rhsv < 0) return false;
    }
    return true;
}


