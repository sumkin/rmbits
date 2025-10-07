import pickle
import networkx as nx
import numpy as np


from distinct_paths_iterator import DistinctPathsIterator


class AircraftRouter:

    def __init__(self, legs, duties, subnetwork, ac_type, aircraft_ids, dr):
        self.legs = legs
        self.duties = duties 
        self.subnetwork = subnetwork
        self.ac_type = ac_type
        self.aircraft_ids = aircraft_ids
        self.dr = dr
        tat_df = self.dr.turnaround_times_df
        assert ac_type in tat_df["Subfleet"].to_list(), "ac_type = {}".format(ac_type)
        self.turnaround_time = int(tat_df[tat_df["Subfleet"] == ac_type]["Turnaround"].iloc[0])

    def build_duties_graph(self):
        """
        Builds duty-graph for routing.
        duty1 -> duty2 if duty2 can be flown after duty1.
        """
        self.duties_graph = nx.DiGraph()

        def get_duty_deptime_arrtime(d):
            duty_deptime = np.inf 
            duty_arrtime = -np.inf 
            for i in self.duties[d]:
                leg = self.legs[i]
                _, _, _, _, _, deptime, arrtime, _ = leg 
                duty_deptime = min(duty_deptime, deptime)
                duty_arrtime = max(duty_arrtime, arrtime)
            return duty_deptime, duty_arrtime
            
        # Add nodes.
        for d in self.subnetwork:
            duty_deptime, duty_arrtime = get_duty_deptime_arrtime(d)
            self.duties_graph.add_node(d, duty_deptime=duty_deptime, duty_arrtime=duty_arrtime)

        # Add edges.
        for i in range(len(self.subnetwork)):
            d = self.subnetwork[i]
            duty_deptime1, duty_arrtime1 = get_duty_deptime_arrtime(d) 
            for j in range(i + 1, len(self.subnetwork)):
                other_d = self.subnetwork[j]
                duty_deptime2, duty_arrtime2 = get_duty_deptime_arrtime(other_d)

                tt = self.turnaround_time
                if len(self.duties[d]) == 1 or len(self.duties[other_d]) == 1:
                    tt = 0
                #if len(self.duties[other_d]) == 1:
                #    tt = 0

                if duty_arrtime1 + tt <= duty_deptime2:
                    self.duties_graph.add_edge(d, other_d)
                if duty_arrtime2 + tt <= duty_deptime1:
                    self.duties_graph.add_edge(other_d, d)

    def solve(self):
        # Build leg-graph.
        self.build_duties_graph()

        res = []
        num_c = 0
        num_paths = 0
        duties_graph_und = self.duties_graph.to_undirected()
        for cc in nx.connected_components(duties_graph_und):
            subg = self.duties_graph.subgraph(cc).copy()

            dpi = DistinctPathsIterator(subg)
            dpi.build_bipartite_graph()
            dpi.maximum_matching()

            num_c += 1

            i = 1
            for path in dpi.paths():
                p = []
                for duty_id in path:
                    for leg_id in self.duties[duty_id]:
                        p.append(leg_id)
                res.append(p)
                print("{} {} {}".format(num_c, i, path))
                num_paths += 1
                i += 1

        print("Number of paths = {}".format(num_paths))

        return res






            
