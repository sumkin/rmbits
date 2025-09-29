import numpy as np


def feasible_ex1(x1,x2):
    return (x1 <= 200) and (x1 + x2 <= 500)


def feasible_ex2(x1,x2,x3):
    return (x1 + x2 <= 200) and (x1 + x3 <= 500)


def min_ex1():
    sol = []
    for x1 in range(0,301):
        for x2 in range(0,401):
            if feasible_ex1(x1,x2):
                if not feasible_ex1(x1+1,x2) and not feasible_ex1(x1,x2+1):
                    sol.append([x1,x2,2*x1+x2])
    minv = np.inf
    for s in sol:
        if s[2] < minv:
            minv = s[2]
    return minv    


def min_ex2():
    sol = []
    for x1 in range(0,301):
        for x2 in range(0,201):
            for x3 in range(0,501):
                if feasible_ex2(x1,x2,x3):
                    if not feasible_ex2(x1+1,x2,x3) and not feasible_ex2(x1,x2+1,x3) and not feasible_ex2(x1,x2,x3+1):
                        sol.append([x1,x2,x3,3*x1+2*x2+2*x3])
    minv = np.inf
    for s in sol:
        if s[2] < minv:
            minv = s[3]
    return minv


def max_ex1():
    pass


def max_ex2():
    pass


if __name__ == "__main__":
    print min_ex1()
    print min_ex2()



