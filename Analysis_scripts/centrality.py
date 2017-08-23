import networkx as nx
import sys
import os
import numpy as np


def main():
    args = sys.argv
    folder = args[1]
    g = nx.read_adjlist(folder + "/topology.adj")
    bcs = nx.betweenness_centrality(g, endpoints=True)
    print "Node\tNX\tPrince+olsrv1"
    for node, value in bcs.iteritems():
        print "%s\t%f\t%f" % (node, value, get_mean_centrality(folder + "/" + node))


def get_mean_centrality(nodename):
    with open(nodename + "_prince.log") as f:
        values = np.loadtxt(f)
        if values.shape[0] > 4:
            stable_value = find_stable_row(values[5:, 4], 10, 1e-4)
            return np.mean(values[stable_value:, 4])
    return 0


def find_stable_row(data, window, tresh):
    stdevs = np.std(rolling_window(data, window), -1)
    for i in range(0, len(stdevs)):
        if stdevs[i] <= tresh:
            return i
    return -1


def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

if __name__ == "__main__":
    main()
