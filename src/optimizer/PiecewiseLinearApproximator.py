import numpy as np


class PiecewiseLinearApproximator:


    def __init__(self, f, a, b, eps):
        self.f = f
        self.a = a
        self.b = b 
        self.eps = eps


    def getLinearCoeffs(self, xs, vs):
        A = (vs[1] - vs[0])/(xs[1] - xs[0])
        B = vs[0] - A * xs[0] 
        return [A, B]


    def getLinearCoeffsForBreak(self, i):
        return self.coeffs[i]


    def getPLinearFunc(self):
        assert len(self.breaks) > 0


    def resFunc(self):
        def f(xs):
            res = []
            for x in xs:
                for i in range(len(self.breaks)):
                    a = self.breaks[i][0]
                    b = self.breaks[i][1]
                    if x >= a and x <= b:
                        res.append(self.coeffs[i][0] * x + self.coeffs[i][1])
                        break
            return res
        return f


    def getNumBreaks(self):
        return len(self.breaks)


    def getBreakPoints(self):
        res = []
        for i in range(len(self.breaks)):
            res.append(self.breaks[i][0])
        res.append(self.breaks[len(self.breaks)-1][1])
        return res


    def getBreakValues(self):
        res = []
        for i in range(len(self.vals)):
            res.append(self.vals[i][0])
        res.append(self.vals[len(self.vals)-1][1])
        return res


    def getMinMax(self):
        minRes = np.inf
        maxRes = -np.inf
        for i in range(len(self.breaks)):
            x = self.breaks[i][0]
            v = self.coeffs[i][0] * x + self.coeffs[i][1]
            minRes = min(minRes, v)
            maxRes = max(maxRes, v)
        x = self.breaks[len(self.breaks)-1][1]
        coeffs = self.coeffs[len(self.coeffs)-1]   
        v = coeffs[0] * x + coeffs[1]
        minRes = min(minRes, v)
        maxRes = max(maxRes, v)
        return minRes, maxRes
   

    def approximate(self):
        self.breaks = [[self.a, self.b]]
        self.vals = [[self.f(self.a), self.f(self.b)]]
        self.coeffs = [self.getLinearCoeffs(self.breaks[0], self.vals[0])]
        ssStep = 0.5

        maxApproxX = self.breaks[0][0]

        while True:
            if len(self.breaks) > 1000:
                assert False
                return
            assert len(self.breaks) == len(self.coeffs)

            for i in range(len(self.breaks)):
                brk   = self.breaks[i]
                coeff = self.coeffs[i]
                val   = self.vals[i]
                assert brk[0] < brk[1]
                if maxApproxX >= brk[1]:
                    continue
    
                # Find x, where difference is at maximum. 
                x = brk[0]
                maxx = x
                maxv = val[0]
                maxdiffv = abs(maxv - coeff[0] * x - coeff[1])
                x += ssStep

                while x <= brk[1]:
                    v = self.f(x)
                    diffv = abs(v - coeff[0] * x - coeff[1])
                    if maxdiffv + self.eps < diffv:
                        maxx = x
                        maxv = v
                        maxdiffv = diffv
                    x += ssStep

                assert maxdiffv >= 0.0
                if maxdiffv > self.eps:
                    if i == 0:
                        self.breaks.insert(0, [brk[0], maxx])
                        self.vals.insert(0, [val[0], maxv])
                        self.breaks[1][0] = maxx
                        self.vals[1][0] = maxv
            
                        xs = self.breaks[0]
                        vs = self.vals[0]
                        self.coeffs.insert(0, self.getLinearCoeffs(xs, vs))

                        xs = self.breaks[1]
                        vs = self.vals[1]
                        self.coeffs[1] = self.getLinearCoeffs(xs, vs)
                    elif i == len(self.breaks) - 1:
                        self.breaks.append([maxx, brk[1]])
                        self.vals.append([maxv, val[1]])
                        self.breaks[len(self.breaks) - 2][1] = maxx
                        self.vals[len(self.vals) - 2][1] = maxv

                        xs = self.breaks[len(self.breaks)-1]
                        vs = self.vals[len(self.vals)-1]
                        self.coeffs.append(self.getLinearCoeffs(xs, vs))

                        xs = self.breaks[len(self.breaks)-2]
                        vs = self.vals[len(self.vals)-2]
                        self.coeffs[len(self.breaks) - 2] = self.getLinearCoeffs(xs, vs)
                    else: 
                        self.breaks.insert(i, [brk[0], maxx])
                        self.vals.insert(i, [val[0], maxv])
                        self.breaks[i+1][0] = maxx
                        self.vals[i+1][0] = maxv

                        xs = self.breaks[i]
                        vs = self.vals[i]
                        self.coeffs.insert(i, self.getLinearCoeffs(xs, vs))

                        xs = self.breaks[i+1]
                        vs = self.vals[i+1]
                        self.coeffs[i+1] = self.getLinearCoeffs(xs, vs)
                        break
                else:
                    maxApproxX = brk[1]
                    if i == len(self.breaks) - 1:
                        return  


    def validate(self):
        approxFunc = self.getPLinearFunc()

        x = self.a
        while x <= self.b:
            y1 = self.f(x)
            y2 = approxFunc(x)
            diff = abs(y1 - y2)
            assert diff <= self.eps 
            x += 1.0


if __name__ == "__main__":

    def f(x):
        return np.exp(x)

    pwla = PiecewiseLinearApproximator(f, 0, 5, 1)
    pwla.approximate()
    breakPoints = pwla.getBreakPoints()
    breakValues = pwla.getBreakValues()
    print('breakPoints = ', breakPoints)
    print('breakValues = ', breakValues)
    f = pwla.resFunc()
    print('f(2.5) = ', f([2.5]))


