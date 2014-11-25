#!/usr/bin/env python
import sys
sys.path.append('../community_networks_analysis')
from gengraphs import loadGraph
from gengraphs import genGraph
from misclibs import showGraph

g = loadGraph(sys.argv[1])
#g = genGraph("UNIT", 200)
showGraph(g)
