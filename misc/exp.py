from poprouting import ComputeTheoreticalValues
import networkx as nx
from collections import defaultdict
from theoricValues import TheoricValues
import sys
import numpy as np
import csv

# def get_bc(bcc, node):
#     return [bc for bc in bcc if node in bc]

def gen_graph_lin(n=1):
    G = nx.Graph()
    r = [5*x for x in range(n)]
    for i in r:
        G.add_edge(str(i+0), str(i+1), weight=1)
        G.add_edge(str(i+0), str(i+2), weight=1)
        G.add_edge(str(i+2), str(i+3), weight=1)
        G.add_edge(str(i+1), str(i+4), weight=1)
        G.add_edge(str(i+3), str(i+4), weight=1)
    for i in r[:-1]:
        G.add_edge(str(i+4), str(i+5), weight=1)
    #nx.write_graphml(G, path="data/%d_line.graphml" % (n))
    return G

def gen_graph_star(n=1):
    G = nx.Graph()
    r = [5*x for x in range(n)]
    for i in r:
        G.add_edge(str(i+0), str(i+1), weight=1)
        G.add_edge(str(i+0), str(i+2), weight=1)
        G.add_edge(str(i+2), str(i+3), weight=1)
        G.add_edge(str(i+1), str(i+4), weight=1)
        G.add_edge(str(i+3), str(i+4), weight=1)
    for i in r[:-1]:
        G.add_edge(str(4), str(i+5), weight=1)
    #nx.write_graphml(G, path="data/%d_diamond.graphml" % (n))
    return G

def gen_graph_flower(n=1):
    G = nx.Graph()
    r = [5*x for x in range(n)]
    for i in r:
        G.add_edge(str(i+0), str(i+1), weight=1)
        G.add_edge(str(i+0), str(i+2), weight=1)
        G.add_edge(str(i+2), str(i+3), weight=1)
        G.add_edge(str(i+1), str(i+4), weight=1)
        G.add_edge(str(i+3), str(i+4), weight=1)
    for i in r:
        G.add_edge(str(i+4), str(20), weight=1)
    #nx.write_graphml(G, path="data/%d_flower.graphml" % (n))
    return G
    
def gen_graph_flower2(n=1):
    G = nx.Graph()
    r = [5*x for x in range(n)]
    for i in r:
        G.add_edge(str(i+0), str(i+1), weight=1)
        G.add_edge(str(i+0), str(i+2), weight=1)
        G.add_edge(str(i+2), str(i+3), weight=1)
        G.add_edge(str(i+1), str(4), weight=1)
        G.add_edge(str(i+3), str(4), weight=1)
    #nx.write_graphml(G, path="data/%d_flower2.graphml" % (n))
    return G

if __name__ == '__main__':
    n = int(sys.argv[1])
    g_type = sys.argv[2]
    results = np.zeros((n+1, 5, 2))
    for i in range(2, n+1):
        if g_type=="Linear":
            graph = gen_graph_lin(i)
        elif g_type=="Star":
            graph = gen_graph_star(i)
        elif g_type=="Flower":
            graph = gen_graph_flower(i)
        elif g_type=="Flower2":
            graph = gen_graph_flower2(i)
        tV = TheoricValues(NXgraph=graph, weight=None)
        art = True
        #tV.check_consistency()
        results[i][0] = tV.compute_average_loss(how="NOpop", articulation_points=art)
        results[i][1] = tV.compute_average_loss(how="POP", articulation_points=art)
        results[i][2] = tV.compute_average_loss(how="POPPEN", articulation_points=art)
    results[2:, 3, :] = np.around(1-results[2:, 0, :]/results[2:, 1, :],decimals=3)
    results[2:, 4, :] = np.around(1-results[2:, 0, :]/results[2:, 2, :],decimals=3)
    #print np.divide(results[0, :, 0],results[2,:,0])
    print results[2:,:,0]
    #np.savetxt("Experiments/aligned/th_result_H.csv", results[1:, :, 0], delimiter=",", fmt='%2.3f', header='NOpop, POP, POPPEN, NOpop_on_POP, NOpop_on_POPPEN')
    #np.savetxt("Experiments/aligned/th_result_TC.csv", results[1:, :, 1], delimiter=",", fmt='%2.3f', header='NOpop, POP, POPPEN, NOpop_on_POP, NOpop_on_POPPEN')
    
    
