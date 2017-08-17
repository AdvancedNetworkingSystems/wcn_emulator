import networkx as nx
import sys, os
import numpy as np

def main():
    args = sys.argv
    folder = args[1]
    g = nx.read_adjlist(folder+"/topology.adj")
    bcs = nx.betweenness_centrality(g, endpoints=True)
    print "Node\tNX\tPrince+olsrv1"
    for node, value in bcs.iteritems():
        print "%s\t%f\t%f" %(node, value, get_mean_centrality(folder+"/"+node))



def get_mean_centrality(nodename):
    with open(nodename+"_prince.log") as f:
        values=np.loadtxt(f)
        #import pdb; pdb.set_trace()
        if values.shape[0]>6:
            return np.mean(values[-5:,4])
    return 0
    #print content[-5:0]

if __name__ == "__main__":
    main()
