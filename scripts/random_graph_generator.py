#!/usr/bin/env python

import networkx as nx
import sys
import argparse

class GraphGenerator():

    graph_types = {"RA":"graph_generator_RA",
            "PL":"graph_generator_PL",
            "RE":"graph_generator_RE",
            "SW":"graph_generator_SW"}

    def __init__(self):
        self.args = None
        self.graph_generator = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description = "graph generator")
        parser.add_argument("-t", dest="type", help="type of graph (RAndom, "+\
                "Power Law, REgular, Small World)",
                choices = self.graph_types.keys(), required=True)
        parser.add_argument("-n", dest="num_nodes", help="number of nodes",
            required=True, type=int)
        parser.add_argument("-g", dest="num_graphs", 
                help="number of graphs to generate",
                required=True, type=int)
        parser.add_argument("-p", dest="prefix", required=True,
                help="prefix to add to output files", type=str)
        self.args = parser.parse_args()

    def graph_generator_SW(self):
        return nx.connected_watts_strogatz_graph(self.args.num_nodes,
                self.args.num_nodes/5, 0.1)

    def graph_generator_RA(self):
        return nx.fast_gnp_random_graph(self.args.num_nodes,0.1)

    def graph_generator_RE(self):
        return nx.random_regular_graph(4, self.args.num_nodes)

    def graph_generator_PL(self):
        return nx.barabasi_albert_graph(self.args.num_nodes, 2)

    def generate_graphs(self):
        generate_graph_function = getattr(self, self.graph_types[self.args.type])
        ret_graphs = []
        for i in range(self.args.num_graphs):
            g = generate_graph_function()
            #if nx.is_connected(g):
            #    for e in g.edges(data=True):
            #        e[2]["weight"] = 1
            #nx.write_edgelist(g, self.prefix+"-"+str(i)+".edges", 
            #        data=["weight"])
            ret_graphs.append(g)
        return ret_graphs

    def add_weight(self, g):
        for e in g.edges(data=True):
            e[2]["weight"] = 1

if __name__ == "__main__":
    gn = GraphGenerator()
    gn.parse_args()
    for i, g in enumerate(gn.generate_graphs()):
        graph_name = gn.args.prefix + "_" + str(gn.args.num_nodes) + \
            "_" + gn.args.type + "_" + str(i) + ".edges"
        gn.add_weight(g)
        nx.write_edgelist(g, graph_name, data=["weight"])
