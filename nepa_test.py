#!/usr/bin/env python
import sys
import graph_utils as gu
import networkx as nx
from config import conf, ConfigurationFile
from os import path, listdir
from time import time
from parameters_parser import parameters
from network_builder import *
from test_code import *
from mininet.log import setLogLevel
import csv
import numpy as np
# add the nepa_test directory to sys path
sys.path.append(path.dirname(sys.argv[0]))
sys.path.append('test_code')
sys.path.insert(0, './')


def mean_exp(path):
    result = []
    for p in ["NOPOP", "POP", "POPPEN"]:
        with open("%s/%s/result.dat" % (path, p)) as f:
            data = []
            r = csv.reader(f)
            for l in r:
                data.append(int(l[0]))
            result.append(np.mean(data))
    return result


def mean_val(subpath, wait):
    with open("%s/result.dat" % (subpath), "w") as fw:
        breaks = []
        dirs = listdir(subpath)
        dirs.remove("result.dat")
        for node in dirs:
            with open("%s/%s/breakage.dat" % (subpath, node)) as f:
                data = []
                reader = csv.reader(f)
                for row in reader:
                    d = {}
                    d['timestamp'] = int(row[0])
                    d['correct'] = float(row[1])
                    data.append(d)
                m_route = max(data, key=lambda x: x['correct'])['correct'] #Search for the max number of route (right one)
                filtered = data[5:-5] #Remove all the data before the wait time and the last 10 seconds
                stable = sorted([d['timestamp'] for d in filtered if d['correct'] != m_route])  # filter all about the fluctuations
                longest_seq = max(np.split(stable, np.where(np.diff(stable) != 1)[0]+5), key=len).tolist()
                print >> fw, "%.2f,%s" %(float(len(longest_seq))*2.5, node) #ds
                # diff = [x1 - x2 - 1 for (x1, x2) in zip(stable[1:], stable[:-1])] #make a vector of differences
                # print >> fw, max(diff)


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
        multitestpath = "Experiments/%s_%d" % (testName, time())
        times = int(self.C.getConfigurations("times"))
        for i in range(times):
            info("+++++++ Round: %d of %d " % ((i + 1), times))
            if graphKind:
                self.generate_topology(graphKind)
            elif graphFile:
                self.load_topology(graphFile)
            elif graphDef:
                self.load_topology(graphDef)
            else:
                print("A source for the graph must be specified")
            params = [(0, 0, "NOPOP"), (1, 0, "POP"), (1, 1, "POPPEN")]  # (poprouting, cutpoint)
            testPath = "%s/%s_%d" % (multitestpath, self.graphname, time())
            kill_nodes = self.C.getConfigurations("kill_nodes")
            if not kill_nodes:
                kill_nodes = [n for n in self.g.nodes() if self.g.degree(n) > 1]  # Filter out leaves
            else:
                kill_nodes = map(int, kill_nodes[1:-1].split(','))
            for p in params:
                self.C.confParams['poprouting'] = p[0]
                self.C.confParams['cutpoint_pen'] = p[1]
                subPath = "%s/%s" % (testPath, p[2])
                for n in kill_nodes:
                    kill_node = "h%d_%d" % (n, n)
                    if drawGraph:
                        nx.draw(self.g)
                        plt.show()
            
                    link_opts = self.C.link_conf()
                    net = GraphNet(self.g, link_opts=link_opts)
                    net.start()
                    net.enableForwarding()
                    # CLI(net)
                    runPath = "%s/%s" %(subPath, kill_node)
                    test = self.C.className(mininet=net, kill=kill_node, name=runPath, args=self.C.confParams)
                    test.runTest()
                    net.stop()
                    test.changePermissions()
                info("*** Done with subcase %s" % (p[2]))
                #mean_val(subPath, int(self.C.confParams['kill_wait']))
            #with open(multitestpath + "/result.dat", 'a') as fw:
                #means = mean_exp(testPath)
                #print >> fw, "%f,%f,%f" % (means[0], means[1], means[2])
        info("*** Done with experiment: " + testName + "\n")
if __name__ == "__main__":
    N = Nepa()
    N.nepa_test()
