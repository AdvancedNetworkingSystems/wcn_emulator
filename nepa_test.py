#!/usr/bin/env python
import sys
import graph_utils as gu
import networkx as nx
from config import conf, ConfigurationFile
from os import path
from time import time
from parameters_parser import parameters
from network_builder import *
from test_code import *
from mininet.log import setLogLevel
# add the nepa_test directory to sys path
sys.path.append(path.dirname(sys.argv[0]))
sys.path.append('test_code')
sys.path.insert(0, './')


class Nepa():
    def generate_topology(self, graph_kind):
        print("No graph topology specified in conf file or command line! Will generate a " + graph_kind + " Graph\n")
        graph_size = self.C.getConfigurations("graph_size")
        self.g = gu.generate_graph(gkind=graph_kind, size=int(graph_size))
        self.graphname = graph_kind + str(graph_size)

    def load_topology(self, graphFile):
        info("\nReading " + graphFile + "\n")
        self.g = gu.loadGraph(graphFile, connected=True)
        self.graphname = graphFile.split('/')[-1].split('.')[0]

    def nepa_test(self):
        setLogLevel('info')
        need = [
            ("-f", ["configFile", True, "",
             "file with the available configurations", str]),
            ("-t", ["testName", True, "",
             "base name for test output", str])
        ]
        opt = [
            ("-d", ["drawGraph", False, False,
             "draw the graph before you run the test", int]),
            ("-g", ["graphFile", True, "",
             "file with the topology (overrides configuration)", str]),
            ("-o", ["overrideOption", True, "",
             "comma separated list of options to override in the ini file \
             (ex: a=10,b=100)", str]),
        ]

        P = conf(path.basename(__file__), need, opt)
        P.parseArgs()
        if not P.checkCorrectness():
            P.printUsage()
            sys.exit(1)

        configFile = P.getParam("configFile")
        testName = P.getParam("testName")
        graphFile = P.getParam("graphFile")
        drawGraph = P.getParam("drawGraph")
        self.C = ConfigurationFile(configFile, testName, P.getParam("overrideOption"))
        graphDef = self.C.getConfigurations("graphDefinition")
        graphKind = self.C.getConfigurations("graph_kind")
        enableShortestRoutes = self.C.getConfigurations("enableShortestRoutes")

        if graphKind:
            self.generate_topology(graphKind)
        elif graphFile:
            self.load_topology(graphFile)
        elif graphDef:
            self.load_topology(graphDef)
        else:
            print("A source for the graph must be specified")

        if drawGraph:
            nx.draw(self.g)
            plt.show()

        link_opts = self.C.link_conf()
        net = GraphNet(self.g, link_opts=link_opts)
        net.start()
        net.enableForwarding()
        if not enableShortestRoutes or enableShortestRoutes.lower() == "true":
            net.setShortestRoutes()
        # CLI(net)

        testPath = testName + "_" + self.graphname + "_" + str(int(time()))
        for i in range(int(self.C.getConfigurations("times"))):
            info("+++++++ Round: " + str(i + 1) + '\n')
            test = self.C.className(net, testPath, self.C.confParams)
            test.runTest()
        net.stop()
        test.changePermissions()
        info("*** Done with experiment: " + testName + "\n")

if __name__ == "__main__":
    N = Nepa()
    N.nepa_test()
