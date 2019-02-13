import os
import sys
import networkx as nx


def substitute_ids(graph):
    ip_id = {}
    n_id = 0
    for n in graph.nodes():
        print(n)


def main(path):
    dirs = os.listdir(path)
    nets = []
    for f in dirs:
        g = nx.read_graphml(path + '/' + f)
        ccs = sorted(nx.connected_components(g), key=len)
        #nets.append((Gc, f))
        print(f)
        for cc in ccs:
            print(len(cc))
        print("\n\n")
        #print("size:%s,\t\t Network:%s\n\n\n"%(ccs, f))
    #nets.sort(key=lambda x: len(x[0].nodes()))
    #for n in nets:
        #print (len(n[0]), n[1])
    #substitute_ids(nets[-1][0])

if __name__ == '__main__':
    args = sys.argv
    main(path=args[1])
