import networkx as nx
import sys
import numpy as np
from poprouting import ComputeTheoreticalValues
import os


def main():
    args = sys.argv
    folder = args[1]
    [process_folder(x[0] + "/") for x in list(os.walk(folder))[1:]]


def process_folder(folder):
    g = nx.read_adjlist(folder + "/topology.adj")
    results = np.zeros([len(g.nodes()), 2])
    ctv = ComputeTheoreticalValues(graph=g)
    #conv_i = find_convergence(folder, g)
    conv_i = -10
    bcs = nx.betweenness_centrality(g, endpoints=True)
    i = 0
    print "\n\n%s converged at %d\n" % (folder, conv_i)
    print "Node\tHello NX\tPrince+olsrv1"
    with open(folder[:-1] + "_result_hello.dat", "w") as f:
        for node in g.nodes():
            mean_hello = get_mean_hello(folder + node, conv_i)
            results[i, :] = [ctv.Hi[node], mean_hello]
            print >> f, "%s\t%f\t%f" % (node, ctv.Hi[node], mean_hello)
            i += 1
    print np.max((np.diff(results, 1)[:].transpose() / np.abs(results)[:, 1])*100)


def get_mean_hello(nodename, conv_i):
    with open(nodename + "_prince.log") as f:
        values = np.loadtxt(f)
        if values.shape[0] > 5:
            return np.mean(values[-conv_i:, 2])
    return 0


def find_convergence(folder, g):
        base_val = 2
        indexes = np.zeros(len(g.nodes()))
        i = 0
        for node in g.nodes():
            with open(folder + node + "_prince.log") as f:
                values = np.loadtxt(f)
                indexes[i] = find_stable_row(values[2:, 4], 3, 0.001)
                i += 1
        return int(np.max(indexes + base_val))


def find_stable_row(data, window, tresh):
    pc = np.abs(np.diff(data[window - 1:]) / np.abs(data[:-window]))
    for i in range(0, len(pc)):
        if pc[i] <= tresh:
            return i
    return None


if __name__ == "__main__":
    main()
