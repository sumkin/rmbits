import pandas as pd
from datetime import datetime, timedelta
import networkx as nx 


from emailutils import *
from lpmodelloader import *
from glpsolver import *
from s3utils import *


class GroupsEvaluator:


    def __init__(self, fcstdate, depdate, mode = 'remaining'):
        print('GroupsEvaluator fcstdate, depdate = ', fcstdate, depdate)
        self.fcstdate, self.depdate = fcstdate, depdate
        self.fcstyear = self.fcstdate[:4]
        self.fcstmonth = self.fcstdate[4:6]
        self.next_depdate = datetime.strftime(datetime.strptime(self.depdate, '%Y%m%d') + timedelta(days = 1), '%Y%m%d')

        print('Model reading...')
        self.model = LPModelLoader(self.fcstdate, self.depdate).get()

        print('Reading inventory...')
        self.invdf = pd.read_csv('s3://ay-rmp-home/nrm/bif/' + self.fcstyear + '/' +\
                                                              self.fcstmonth + '/' +\
                                                        'INV_' + self.fcstdate + '.csv.gz')
        self.invdf = self.invdf.loc[(self.invdf['DEPDT'] == int(self.depdate)) |
                                    (self.invdf['DEPDT'] == int(self.next_depdate))]
        self.invdf = self.invdf.loc[(self.invdf['ORGN'] == 'HEL') |\
                                    (self.invdf['DSTN'] == 'HEL')]
        self.invdf = self.invdf.loc[(self.invdf['CABIN'] == 'J') |
                                    (self.invdf['CABIN'] == 'Y')]
        self.invdf = self.invdf.loc[(self.invdf['CAPO'] < 900)]
        self.invdf = optimize_bif(self.invdf)


    def get_arrdt(self, cc, orgn, dstn, fltnum, depdt):
        return self.invdf[(self.invdf['CC'] == cc) &\
                          (self.invdf['ORGN'] == orgn) &\
                          (self.invdf['DSTN'] == dstn) &\
                          (self.invdf['FLTNUM'] == fltnum) &\
                          (self.invdf['DEPDT'] == int(depdt))]['ARRDT'].iloc[0] 


    def adjust_demand(self, flowsh, f, d, cabins):
        print('self.model.keys() = ', self.model.keys())
        try:
            idx = self.model['v_flowsh2idx'][flowsh]
            self.f[idx] = f
            self.d[idx] = max(self.d[idx], d)
        except Exception as e:
            print('Flow ', flowsh, ' not found')
            print('Adding flow...')
            idx = len(self.model['v_idx2flowsh'])
            self.v_idx2flowsh.append(flowsh)
            self.model['v_flowsh2idx'][flowsh] = idx

            nrows,ncols = self.A.shape
            col = np.zeros((nrows,1))
            self.A = np.append(self.A, col, axis = 1)
            self.f = np.append(self.f, f)
            self.d = np.append(self.d, d)

            for c in cabins:
                if c in self.rownumd.keys():
                    self.A[self.rownumd[c],idx] = 1
                else:
                    print(c, ' is not found')
                    assert False
            print('Flow is added')

 
    def get_idx(self, flowsh):
        return self.v_flowsh2idx[flowsh]


    def evaluate(self, flow):
        assert len(flow) == 10 or len(flow) == 16

        flowsh = ''
        if len(flow) == 10:
            pos = str(flow[6])
            bc = str(flow[7])
        elif len(flow) == 16:
            pos = str(flow[12])
            bc = str(flow[13])

        cabins = []
        if flow[0] is not None:
            fltnum = flow[5]
            cc = fltnum[:2]
            fltnum = int(fltnum[2:])
            try:
                arrdt = self.get_arrdt(cc,flow[0],flow[1],fltnum,flow[4])
            except Exception as e:
                print('flow = ', flow)
                print('1. e = ', e)
                return 0,0,0,0,0,0,''
            flowsh += str(flow[0])+str(flow[1])+str(flow[4])+str(arrdt)+str(flow[5])
            if bc == 'G':
                cabins.append(str(int(fltnum)) + 'Y' + str(int(flow[4])))
            else:
                assert False

        if len(flow) == 16:
            if flow[6] is not None:
                fltnum = flow[11]
                cc = fltnum[:2]
                fltnum = int(fltnum[2:])
                try:
                    arrdt = self.get_arrdt(cc,flow[6],flow[7],fltnum,flow[10])
                except Exception as e:
                    print('flow = ', flow)
                    print('2. e = ', e)
                    return 0,0,0,0,0,0,''
                flowsh += str(flow[6])+str(flow[7])+str(flow[10])+str(arrdt)+str(flow[11])
                if bc == 'G':
                    cabins.append(str(int(fltnum)) + 'Y' + str(int(flow[10])))
                else:
                    assert False

        flowsh += '-' + pos + '--' + bc + '-L'

        # Zero demand.
        self.adjust_demand(flowsh, 0.0, 0.000001, cabins)
        idx = self.get_idx(flowsh)

        # Given demand.
        if len(flow) == 10:
            d = flow[8]
        elif len(flow) == 16:
            d = flow[14]
        else:
            assert False

        print('model.keys() = ', self.model.keys())
        A = self.model['A']
        cap = self.model['cap']
        d = self.model['d']
        f = self.model['f']
        prdt_names = self.model['prdt_names']
        rsrc_names = self.model['rsrc_names']
        initrow = self.model['initrow']

        self.lps = GLPSolver(A, cap, ds, f, prdt_names, rsrc_names)
        val_zero, sol_zero = self.lps.solve('ge_zero')
        msplg_zero = self.lps.get_min_rsrc_slack(idx)
        msplgs_zero = self.lps.get_rsrc_slacks(idx)

        ds[idx] = max(ds[idx],d) 

        self.lps = GLPSolver(A, cap, ds, f, prdt_names, rsrc_names, [idx])
        val, sol = self.lps.solve('ge')

        return flowsh, sol[idx], 0, (val_zero - val) / d, msplg_zero, msplgs_zero, ''


    @staticmethod 
    def requests_components(requests):

        # Collect flights.
        flights = set()
        for request in requests:
            for flight in request.split("-"):
                flights.add(flight)

        # Create graph.
        g = nx.Graph()

        # Add nodes.
        for flight in flights:
            g.add_node(flight)

        # Add edges.
        for request in requests:
            flights = request.split("-")
            for i in range(len(flights)):
                for j in range(i + 1, len(flights)):
                    g.add_edge(flights[i], flights[j])

        # Components.
        num_components = 0
        for component in nx.connected_components(g):
            num_components += 1

        return g


if __name__ == "__main__":
    """
    ge = GroupsEvaluator('20200210','20200609')
    flow = ['OSL','HEL','20200210','20200210','20200609','AY0914','HEL','NRT','20200210','20200210','20200609','AY0073','DK','G',26,0]
    d,s,f,pf,a,b,c = ge.evaluate(flow)
    print('d,s,f,pf = ',d,s,f,pf)
    """
    requests = [
        "NRTHEL202101011-HELLHR202101014",
        "KIXHEL202101013-HELLHR202101012"
    ]

    GroupsEvaluator.requests_components(requests)




