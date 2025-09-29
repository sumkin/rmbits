import copy
import pickle
import networkx as nx
from networkx.algorithms import bipartite


class DistinctPathsIterator:


    def __init__(self, g):
        self.g = g

    
    def build_bipartite_graph(self):
        """
        Builds the bipartitie graph for DAG.
        """
        self.b_g = nx.DiGraph()

        # Add nodes.
        for node in self.g.nodes():
            # Each node is split into two.
            self.b_g.add_node(str(node) + "-origin", bipartite = 0)
            self.b_g.add_node(str(node) + "-destination", bipartite = 1)

        # Add edges.
        for edge in self.g.edges():
            node_from, node_to = edge 
            node_from = str(node_from) + "-origin"
            node_to = str(node_to) + "-destination"
            self.b_g.add_edge(node_from, node_to)

 
    def maximum_matching(self):
        """
        Makes maximum matching.
        """
        und_b_g = self.b_g.to_undirected()
        assert bipartite.is_bipartite(und_b_g)
        u = [n for n in und_b_g.nodes if und_b_g.nodes[n]["bipartite"] == 0]
        self.matching = bipartite.matching.maximum_matching(und_b_g, top_nodes = u)


    def paths(self):
        """
        Generator for paths.
        """ 
        self.g_copy = copy.deepcopy(self.g)
        self.nodes_wo_pred = []
        for node in self.g_copy.nodes:
            node_name = str(node) + "-destination"
            if node_name in self.matching.keys():
                continue 
            self.nodes_wo_pred.append(node)
        
        if len(self.g_copy.nodes()) == 0:
            return

        for node in self.nodes_wo_pred:
            path = []
            path.append(int(node))
            node_b = str(node) + "-origin"
            while node_b in self.matching.keys():
                n = self.matching[node_b].split("-")[0]
                path.append(int(n))
                node_b = n + "-origin"
            yield path

        return  


if __name__ == "__main__":
    pkl_fname = "../data/legs.pkl"
    with open(pkl_fname, "rb") as f:
        legs = pickle.load(f)

    pkl_fname = "../data/cc_E90_0.pkl"
    with open(pkl_fname, "rb") as f:
        g = pickle.load(f)
        dpi = DistinctPathsIterator(g)
        dpi.build_bipartite_graph()     
        dpi.maximum_matching()  

        paths = iter(dpi)
        i = 1
        for path in paths:
            print(i, path) 
            i += 1
 

