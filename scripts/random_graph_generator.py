#!/usr/bin/env python

import networkx as nx
import sys

if len(sys.argv) != 4:
    print "usage: ./random_graph_generator.py numGraphs prefix numNodes"
    sys.exit(1)

numGraphs = int(sys.argv[1])
prefix = sys.argv[2]
numNodes = int(sys.argv[3])

for i in range(numGraphs):
    g = nx.fast_gnp_random_graph(numNodes,0.5)
    if nx.is_connected(g):
        for e in g.edges(data=True):
            e[2]["weight"] = 1
        nx.write_edgelist(g, prefix+"-"+str(i)+".edges", data=["weight"])

