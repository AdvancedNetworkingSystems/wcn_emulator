#!/usr/bin/env python
import networkx as nx
import sys
from matplotlib import pyplot as plt


g = nx.read_weighted_edgelist(sys.argv[1])

g.remove_edges_from(g.selfloop_edges())
c = nx.k_core(g, 2)

a = [n for n in nx.articulation_points(c)]

fail_candidates = [ n for n in c.nodes() if n not in a]

for n in fail_candidates:
    gg = g.copy()
    gg.remove_node(n)
    comp = nx.connected_components(gg)
    print n, comp
    isolated_nodes = [x for component in comp[1:] for x in component]
    print "XX", isolated_nodes


nx.draw(g)
plt.show()
nx.draw(c)
plt.show()


