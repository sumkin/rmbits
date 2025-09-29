#ifndef POSVAL_H
#define POSVAL_H

#include "defs.h"

typedef struct PosVal {
    uint  pos;
    double  val;
    struct PosVal* p_next;
} PosVal;

#endif // POSVAL_H
