import networkx as nx
import sys
import numpy as np
from poprouting import ComputeTheoreticalValues


def main():
    args = sys.argv
    folder = args[1]
    graph = nx.read_adjlist(folder + "/topology.adj")
    ctv = ComputeTheoreticalValues(graph=graph)

    print "Node\tHello NX\t Hello Prince"
    for node in graph.nodes():
        print "%s\t%f\t%f" % (node, ctv.Hi[node], get_mean_hello(folder + "/" + node))


def get_mean_hello(nodename):
    with open(nodename + "_prince.log") as f:
        values = np.loadtxt(f)
        if values.shape[0] > 5:
            return np.mean(values[-5:, 2])
    return 0

if __name__ == "__main__":
    main()
