#ifndef SMPLXTBL_H
#define SMPLXTBL_H

#include <float.h>
#include <limits.h>
#include <string.h>
#include <stdio.h>

#include "defs.h"
#include "smplxtblrow.h"
#include "smplxtblclmn.h"


typedef struct SmplxBasisElement {
    uint varidx;
    uint rowidx;
} SmplxBasisElement;

typedef struct SmplxTbl {
    uint                nrows;    // number of rows in simplex tableu (m + n).
    uint                ncols;    // number of columns in simplex tableu (n + m + n).
    double*             p_rhs;    // right-hand side of simplex tableu (m + n).
    double*             p_lr;     // last row of simplex tableu (n + m + n).
    double              v;        // value of objective. Element in right-bottom angle.
    SmplxBasisElement*  p_basis;  // basis
    uint*               p_nbvars; // indices of non-basis variables.
    SmplxTblRow*        p_rows;   // rows of tableu.
    SmplxTblClmn*       p_cols;   // columns of tableu.
} SmplxTbl;


// Initialize simplex tableu.
SmplxTbl* smplxtbl_init(uint m, uint n);

// Get the value of right-hand side.
double smplxtbl_get_rhs(const SmplxTbl* p_st, uint i);

// Set the value of right-hand side.
void smplxtbl_set_rhs(SmplxTbl* p_st, uint i, double v);

// Get the value of matrix element.
double smplxtbl_get_m(const SmplxTbl* p_st, uint i, uint j);

// Set the value of matrix element.
void smplxtbl_set_m(SmplxTbl* p_st, uint i, uint j, double v);

// Set the value of matrix element to zero.
double smplxtbl_set_m_zero(SmplxTbl* p_st, uint i, uint j);

// Add the value to matrix element.
void smplxtbl_add_m(SmplxTbl* p_st, uint i, uint j, double v);

// Divide the value of matrix element.
void smplxtbl_divide_m(SmplxTbl* p_st, uint i, uint j, double v);

// Nullify element.
void smplxtbl_nullify(SmplxTbl* p_st, uint i, uint j);

// Find and nullify elements.
void smplxtbl_find_and_nullify(SmplxTbl* p_st);

// Get last row coefficient.
double smplxtbl_get_lr(const SmplxTbl* p_st, uint i);

// Set last row coefficient.
void smplxtbl_set_lr(SmplxTbl* p_st, uint i, double v);

// Initialize slack basis.
bool smplxtbl_init_slack_basis(SmplxTbl* p_st);

// Find variable to enter basis.
uint smplxtbl_find_enter_var(SmplxTbl* p_st);

// Find variable to leave basis.
bool smplxtbl_find_leave_var(const SmplxTbl* p_st, uint j, SmplxBasisElement* p_be);

// Pivot to new basis.
void smplxtbl_pivot(SmplxTbl* p_st, uint newvaridx, SmplxBasisElement* p_be); 

// Check whether variable is basis.
bool smplxtbl_is_basis(SmplxTbl* p_st, uint j);

// Replace variable in basis.
void smplxtbl_replace_var_in_basis(SmplxTbl* p_st, uint newvaridx, uint newrowidx, uint oldvaridx);

// Get value of objective.
double smplxtbl_get_value(const SmplxTbl* p_st);

// Get solution.
double smplxtbl_get_sol(const SmplxTbl* p_st, uint i);

// Print simplex tableu.
void smplxtbl_print(const SmplxTbl* p_st);

// Print basis.
void smplxtbl_print_basis(const SmplxTbl* p_st);

// Check validity of basis.
bool smplxtbl_check_basis(const SmplxTbl* p_st);

// Check feasibility of basis.
bool smplxtbl_basis_feasible(const SmplxTbl* p_st);

#endif // SMPLXTBL_H


