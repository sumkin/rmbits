#include "smplx.h"

//#define DEBUG

bool smplx_solve(SmplxTbl* p_st) {
    SmplxBasisElement be;
    uint num = 0;
    while (true) {
        uint newidx = smplxtbl_find_enter_var(p_st);
        if (newidx == INT_MAX) {
            printf("Number of iterations = %d\n", num);
            return true;
        }
        bool res = smplxtbl_find_leave_var(p_st, newidx, &be);
        if (!res) break;
        smplxtbl_pivot(p_st, newidx, &be);
        num++;
    }
}



