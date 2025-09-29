#ifndef SMPLXTBLROW_H
#define SMPLXTBLROW_H

#include <stdlib.h>
#include <limits.h>
#include <stdio.h>
#include <math.h>

#include "posval.h"

typedef struct SmplxTblRow {
    PosVal* p_posval;
    uint num;
} SmplxTblRow;

// Initialize structure.
SmplxTblRow* smplxtblrow_init();

// Set element at position.
void smplxtblrow_set(SmplxTblRow* p_row, uint pos, double v);

// Set element at position to zero.
double smplxtblrow_set_zero(SmplxTblRow* p_row, uint pos);

// Divide element at position.
void smplxtblrow_divide(SmplxTblRow* p_row, uint pos, double v);

// Add value to element at position.
void smplxtblrow_add(SmplxTblRow* p_row, uint pos, double v);

// Get element at position.
double smplxtblrow_at(const SmplxTblRow* p_row, uint pos); 

// Nullify element at position.
PosVal* smplxtblrow_nullify(SmplxTblRow* p_row, uint pos);

// Find and nullify all elements.
void smplxtblrow_find_and_nullify(SmplxTblRow* p_row);

// Get number of nonzero elements.
uint smplxtblrow_nzero_num(SmplxTblRow* p_row);

// Free structure.
void smplxtblrow_free(SmplxTblRow* p_row);

#endif // SMPLXTBLROW_H


