#ifndef SMPLXTBLCLMN_H
#define SMPLXTBLCLMN_H

#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <math.h>

#include "posval.h"

typedef struct SmplxTblClmn {
    PosVal* p_posval;
    uint num;
} SmplxTblClmn;

// Initialize structure.
SmplxTblClmn* smplxtblclmn_init();

// Set element at position.
void smplxtblclmn_set(SmplxTblClmn* p_col, uint pos, double v);

// Set element at position to zero.
double smplxtblclmn_set_zero(SmplxTblClmn* p_col, uint pos);

// Divide element at position.
void smplxtblclmn_divide(SmplxTblClmn* p_col, uint pos, double v);

// Add value to element.
void smplxtblclmn_add(SmplxTblClmn* p_col, uint pos, double v);

// Get element at position.
double smplxtblclmn_at(const SmplxTblClmn* p_col, uint pos);

// Remove element at position.
PosVal* smplxtblclmn_nullify(SmplxTblClmn* p_col, uint pos);

// Find and nullify elements.
void smplxtblclmn_find_and_nullify(SmplxTblClmn* p_col);

// Get number of nonzero elements.
uint smplxtblclmn_nzero_num(SmplxTblClmn* p_col);

// Free structure.
void smplxtblclmn_free(SmplxTblClmn* p_col);

#endif // SMPLXTBLCLMN_H


