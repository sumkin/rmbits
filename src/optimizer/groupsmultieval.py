import json
import time
from datetime import datetime
import networkx as nx
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from currency_converter import CurrencyConverter
import multiprocessing
from joblib import Parallel, delayed
import yaml
import boto3
from decimal import Decimal


from lpmodelloader import LPModelLoader
from glpsolver import GLPSolver
from funcutils import *
from s3utils import *


class GroupsMultiEvaluator:


    def __init__(self, fcstdate, g, component_id, component, mode = 'remaining'):
        self.fcstdate, self.fcstyear, self.fcstmonth = fcstdate, fcstdate[:4], fcstdate[4:6]
        self.g = g
        self.component_id = component_id
        self.component = component

        depdates = set()
        for i in component:
            for depdate in g.nodes[i]["depdates"]:
                depdates.add(depdate)

        self.depdates = list(depdates)
        self.depdates.sort()

        self.invdf = pd.read_csv("s3://ay-rmp-home/nrm/bif/{}/{}/INV_{}.csv.gz".format(self.fcstyear, self.fcstmonth, self.fcstdate))
        self.invdf = self.invdf.loc[(self.invdf['ORGN'] == 'HEL') | (self.invdf['DSTN'] == 'HEL')]
        self.invdf = self.invdf.loc[(self.invdf['CABIN'] == 'J') | (self.invdf['CABIN'] == 'Y')]
        self.invdf = self.invdf.loc[self.invdf['CAPO'] < 900]

        with open("/home/ay49514/rmbits/config.yaml") as f:
            d = yaml.load(f, Loader = yaml.FullLoader)
            self.dynamodb = boto3.resource("dynamodb",
            aws_access_key_id = d['DYNAMODB_DATABASE']['ACCESS_KEY_ID'],
            aws_secret_access_key = d['DYNAMODB_DATABASE']['SECRET_ACCESS_KEY'],
            region_name = d['DYNAMODB_DATABASE']['REGION_NAME']
        )
        print("GroupsMultiEvaluator for component_id {} created.".format(self.component_id))


    def evaluate(self):
        """
        Evaluates requests in component.
        """
        print("GroupsMultiEval.evaluate() for component_id {} called.".format(self.component_id))
        self.model = self._create_model()
        print("Model for component_id {} created.".format(self.component_id))
        adjusted, missing_flights = self._adjust_model()
        print("Model adjusted for component_id {}.".format(self.component_id))
        if adjusted:
            self.glpsolver = GLPSolver(self.model["Ai"],
                                       self.model["Aj"],
                                       self.model["Adata"],
                                       self.model["cap"],
                                       self.model["d"],
                                       self.model["f"],
                                       self.model["b"],
                                       self.model["y"],
                                       self.model["prdt_names"],
                                       self.model["rsrc_names"],
                                       semiints = self.model["semiints"],
                                       semiint_lbs = self.model["semiint_lbs"]
            )
            print("GLPSolver for component_id {} created.".format(self.component_id))
            self.glpsolver.solve("")
            print("Solved for component_id {}".format(self.component_id))
            for i in self.component:
                idx = self.g.nodes[i]["idx"]
                pax = self.g.nodes[i]["pax"]
                var_name = "group_" + str(idx)
                index = self.model["prdt_names"].index(var_name)
                sol = self.glpsolver.sol[index]
                yield [self.component_id, idx, pax, sol, '']
        else:
            for k in missing_flights.keys():
                idx = self.g.nodes[k]["idx"]
                pax = self.g.nodes[k]["pax"]
                error = "missing flights " + ' '.join(missing_flights[k])
                error = error.strip()
                yield [self.component_id, idx, pax, None, error]


    def _create_model(self):
        """
        Creates model.
        """
        # TODO: make loading async.
        models = []
        num = 1
        for depdate in self.depdates:
            model = LPModelLoader(self.fcstdate, depdate).get()
            models.append(model)
            num += 1
        
        # Combined models.
        return self._combine_models(models)


    def _combine_models(self, models):
        """
        Combines the list of models to one model.
        """
        res_nrows = 0
        res_ncols = 0

        res_Ai, res_Aj, res_Adata = [], [], []
        res_cap = []
        res_d = []
        res_f = []
        res_b = []
        res_y = []
        res_prdt_names = []
        res_rsrc_names = []
        res_initrow = []
        res_fcap = []
        res_v_flowsh2idx = {}
        res_v_idx2flowsh = []
        res_rownumd = {}

        for model in models:
            Ai, Aj, Adata = model['Ai'], model['Aj'], model['Adata'] # matrix of constraints
            cap = model['cap']                                       # vector of capacities
            d = model['d']                                           # vector of demand
            f = model['f']                                           # vector of fares
            b = model['b']                                           # vector of bookings
            y = model['y']                                           # vector of yields
            prdt_names = model['prdt_names']                         # name of products
            rsrc_names = model['rsrc_names']                         # name of resources
            initrow = model['initrow']                               # product used to write results to csv
            fcap = model['fcap']                                     # full capacity
            v_flowsh2idx = model['v_flowsh2idx']                     # geo flow to index of variable
            v_idx2flowsh = model['v_idx2flowsh']                     # index of variable to geo flow
            rownumd = model['rownumd']                               # resource (flight) to row number
            assert len(d) == len(f) == len(b) == len(y) == len(prdt_names) == len(initrow)
            assert len(cap) == len(fcap) == len(rsrc_names)

            nrows = len(cap)
            ncols = len(d)

            # Ai is the list containing row indices of non-zero elements.
            # Aj is the list containing column indices of non-zero elements.
            # Adata is the list of non-zero elements.
            assert len(Ai) == len(Aj) == len(Adata)
            res_Ai += [e + res_nrows for e in Ai]
            res_Aj += [e + res_ncols for e in Aj]
            res_Adata += Adata

            res_cap = np.concatenate((res_cap,cap))
            res_d = np.concatenate((res_d,d))
            res_f = np.concatenate((res_f,f))
            res_b = np.concatenate((res_b,b)) 
            res_y = np.concatenate((res_y,y))
            res_prdt_names += prdt_names 
            res_rsrc_names += rsrc_names
            res_initrow += initrow
            res_fcap = np.concatenate((res_fcap,fcap)) 

            for k in v_flowsh2idx.keys():
                res_v_flowsh2idx[k] = v_flowsh2idx[k] + res_ncols

            res_v_idx2flowsh += v_idx2flowsh

            for k in rownumd.keys():
                res_rownumd[k] = rownumd[k] + res_nrows

            res_nrows = len(res_cap)
            res_ncols = len(res_d)
        
        res = {}
        res['Ai'] = res_Ai 
        res['Aj'] = res_Aj
        res['Adata'] = res_Adata 
        res['cap'] = res_cap 
        res['d'] = res_d 
        res['f'] = res_f 
        res['b'] = res_b 
        res['y'] = res_y 
        res['prdt_names'] = res_prdt_names 
        res['rsrc_names'] = res_rsrc_names 
        res['initrow'] = res_initrow 
        res['fcap'] = res_fcap 
        res['v_flowsh2idx'] = res_v_flowsh2idx 
        res['v_idx2flowsh'] = res_v_idx2flowsh 
        res['rownumd'] = res_rownumd

        return res 


    def _adjust_model(self):
        """
        Adjusts model with demand according to component.
        """
        return_false = False
        missing_flights = {}

        self.model["semiints"] = []
        self.model["semiint_lbs"] = []
        for node_id in self.component:
            idx = self.g.nodes[node_id]["idx"]
            pax = self.g.nodes[node_id]["pax"]
            fare = self.g.nodes[node_id]["fare"]
            legs = self.g.nodes[node_id]["legs"]
            rownums = []
            missing_flights[node_id] = []
            for leg in legs:
                depdate = leg[6:14]
                fltnum = leg[16:20]
                rsrc_name = fltnum.lstrip("0") + "Y" + depdate
                rownum = self.model["rownumd"].get(rsrc_name, None)
                if rownum is None:
                    missing_flights[node_id].append(rsrc_name)
                rownums.append(rownum)

            if None in rownums:
                return_false = True
                continue

            # Ai, Aj, Adata, cap, d, f, b, y, prdt_names, rsrc_names.
            ncols = len(self.model["f"])

            # Add new variable.
            for rownum in rownums:
                self.model["Ai"].append(int(rownum))
                self.model["Aj"].append(int(ncols))
                self.model["Adata"].append(1)
            self.model["d"] = np.append(self.model["d"], pax)
            self.model["f"] = np.append(self.model["f"], fare)
            self.model["b"] = np.append(self.model["b"], 0)
            self.model["y"] = np.append(self.model["y"], 0)
            self.model["prdt_names"].append("group_" + str(idx))
            self.model["semiints"].append(len(self.model["d"]) - 1)
            self.model["semiint_lbs"].append(10)
        
        if return_false:
            return False, missing_flights 
        else:
            return True, missing_flights


    @staticmethod 
    def components(requests):
        # Currency converter.
        c = CurrencyConverter()

        # Create the graph.
        print("Creating graph...")
        g = nx.Graph()

        # Add nodes.
        for i in range(len(requests)):
            idx = requests[i]["idx"]
            pax = requests[i]['Pax']
            fare, currency = requests[i]['Net Fare Request'], requests[i]['Currency']
            fare = c.convert(float(fare), currency, 'EUR')
            legs = [e for e in requests[i]["legs"].split("-") if e != ""]
            depdts = [e[6:14] for e in legs]
            d = set()
            for depdt in depdts:
                d.add(depdt)
            g.add_node(i, idx = idx, pax = pax, fare = fare, depdates = d, legs = legs)
        print("Nodes added.")

        # Add edges.
        depdts = set()
        for i in range(len(requests)):
            legs1 = [e for e in requests[i]['legs'].split("-") if e != '']
            legs1 = set(legs1)
            for j in range(i + 1, len(requests)):
                legs2 = [e for e in requests[j]['legs'].split("-") if e != '']
                legs2 = set(legs2)
                if len(legs1.intersection(legs2)) != 0:
                    g.add_edge(i, j)
        print("Edges added.")

        # Components.
        num_components = 0 
        for component in nx.connected_components(g):
            print("Component number {} yielded.".format(num_components))
            yield g, component
            num_components += 1


    @staticmethod 
    def update_status(optimization_id, requests, status):
        dynamodb = None
        with open("/home/ay49514/rmbits/config.yaml") as f:
            d = yaml.load(f, Loader = yaml.FullLoader)
            dynamodb = boto3.resource("dynamodb",
                aws_access_key_id = d['DYNAMODB_DATABASE']['ACCESS_KEY_ID'],
                aws_secret_access_key = d['DYNAMODB_DATABASE']['SECRET_ACCESS_KEY'],
                region_name = d['DYNAMODB_DATABASE']['REGION_NAME']
            )
        assert dynamodb is not None

        table = dynamodb.Table("GROUP_OPTS")
        cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        idxes = [r["idx"] for r in requests]
        if status == "STARTED":
            response = table.update_item(
                Key = {'OPT_ID': str(optimization_id)},
                UpdateExpression = "set #sta=:r, #time=:t, #ser=:s, #sercnt=:c",
                ExpressionAttributeValues = {
                    ":r": status,
                    ":t": cur_time,
                    ":s": idxes,
                    ":c": len(requests) 
                },
                ExpressionAttributeNames = {
                    "#sta": "STATUS",
                    "#time": "TIME_STARTED",
                    "#ser": "SERIES",
                    "#sercnt": "SERIES_COUNT"
                }
            )
        elif status == "FINISHED":
            response = table.update_item(
                Key = {'OPT_ID': str(optimization_id)},
                UpdateExpression = "set #sta=:r, #time=:t",
                ExpressionAttributeValues = {
                    ":r": status,
                    ":t": cur_time
                },
                ExpressionAttributeNames = {
                    "#sta": "STATUS",
                    "#time": "TIME_FINISHED"
                }
            )
 

    @staticmethod 
    def process(optimization_id, requests):
        fcstdate = (datetime.now() - timedelta(days = 2)).strftime("%Y%m%d")

        # Update status of optimization.
        GroupsMultiEvaluator.update_status(optimization_id, requests, "STARTED")

        def f(fcstdate, g, num, component):
            gme = GroupsMultiEvaluator(fcstdate, g, num, component)
            table = gme.dynamodb.Table("GROUP_OPT_SERIES_RESULTS")
            for res in gme.evaluate():
                series_id = res[1]
                taken = res[3]
                msg = res[4]
                print("optimization_id, series_id, taken, msg = {}, {}, {}, {}".format(optimization_id, series_id, taken, msg))
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    table.put_item(
                        Item = {
                            "OPT_ID": str(optimization_id),
                            "SERIES_ID": str(series_id),
                            "taken": str(taken),
                            "msg": msg,
                            "timestamp": timestamp,
                        }
                    )
                except Exception as e:
                    print("e = {}".format(e))
                    print("WARNING: writing to dynamodb failed.")
                    
        parallel = True 
        if parallel:
            components = [(g, c) for g, c in GroupsMultiEvaluator.components(requests)]
            args = []
            n = 0
            for g,c in components:
                args.append([n,g,c])
                n += 1
            args = [(fcstdate, g, num, c) for num, g, c in args]
            
            num_cores = 8 #multiprocessing.cpu_count()
            Parallel(n_jobs = int(num_cores))(delayed(f)(fcst,g,n,c) for fcst,g,n,c in args) 
        else:
            num = 0
            for g, component in GroupsMultiEvaluator.components(requests):
                f(fcstdate, g, num, component)
                num += 1

        # Update status of optimization.
        GroupsMultiEvaluator.update_status(optimization_id, requests, "FINISHED")


if __name__ == "__main__":
    with open("/home/ay49514/rmbits/data/groupseval/data4.json") as f:
        requests = json.load(f)
        GroupsMultiEvaluator.process(888, requests)
