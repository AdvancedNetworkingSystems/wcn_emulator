#!/usr/bin/env python

import sys
sys.path.append('../community_networks_analysis')

from misclibs import navigateRoutingTables
from gengraphs import loadGraph
import glob
import json
import networkx as nx

if len(sys.argv) != 3:
    print "usage: ./compare_topologies_recursively.py ",\
            "path_prefix full_topology"
    sys.exit(1)

pathPrefix = sys.argv[1]
topoFile = sys.argv[2]
g = loadGraph(topoFile, remap=True)
print g.nodes()

jsonRt = {}
nodeList = set()

for topoFile in glob.glob(pathPrefix+"*.rt"):
    try:
        f = open(topoFile, "r")
        j = json.load(f)
    except Exception as e:
        print "NOK", str(e)
        sys.exit(1)
    nodeIP = ".".join(j["node"].split(":")[0].split(".")[:3])
    rt = j["rt"]
    jsonRt[nodeIP] = {}
    for dest, nh in rt.items():
        shortDest = ".".join(dest.split(".")[:3])
        shortNh = ".".join(nh[0].split(".")[:3])
        jsonRt[nodeIP][shortDest] = [shortNh] + nh[1:]

    nodeList.add(str(nodeIP))


nl = list(nodeList)


#for node, rt  in jsonRt.items():
#    if len(rt) != len(nl) - 1:
#        print "node ", node, "misses some routes"
#        print json.dumps(jsonRt, indent=1)
#        sys.exit(1)

#print json.dumps(jsonRt, indent=1)
errors = 0
for i in range(len(nl)):
    for j in range(i+1, len(nl)):
        s = int(nl[i].split(".")[2])
        d = int(nl[j].split(".")[2])
        print "== rt ", s, d
        route = navigateRoutingTables(jsonRt, nl[i],
                nl[j], [], 0)
        allroutes = [p for p in nx.all_shortest_paths(g, s, d)]

        shortedRoute =  [int(r.split(".")[2]) for r in route[0]]
        print "XX", shortedRoute
        print "YY", allroutes

        if shortedRoute not in allroutes:
            print "NOK!: route", shortedRoute, "not in ", allroutes
            errors += 1

print "Found ", errors, "errors"







