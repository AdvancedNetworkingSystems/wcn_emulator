#!/usr/bin/env python
import sys

sys.path.append('test_code')

from network_builder import *
from test_code import *

from os import path
from time import time


from parameters_parser import parameters


class conf(parameters):
    def checkCorrectness(self):
        self.checkNeededParams()
        return True

if __name__ == '__main__':
    setLogLevel('info')
    need = [
            ("-f", ["graphDefinition", True, "", "path of the graph definition", str]),
            ("-t", ["testName", True, "", "base name for test output", str])
           ]
    opt = [
            ("-d", ["drawGraph", False, False, 
                "draw the graph before you run the test", int])
          ]

    P = conf(path.basename(__file__),need, opt)
    P.parseArgs()
    drawGraph = P.getParam("drawGraph")
    if P.checkCorrectness() == False:
        P.printUsage()
        sys.exit(1)
    net = GraphNet(P.getParam("graphDefinition"), draw = drawGraph)
    net.start()
    net.enableForwarding()
    net.setShortestRoutes()
#    CLI(net)
    test_name = P.getParam("testName")+"_"+str(int(time()))
    for i in range(1):
        info("+++++++ Round: "+str(i+1) + '\n')
        #test = PSRandomTest(net,duration=6,name=test_name,num_peers=2)
        test = peerstreamer.PSHostsTest(net, 'h0_0', ['h1_1','h1_1','h2_2'],
                duration = 600, name = test_name)
        test.runTest()
      #  sleep(60)
    net.stop()
    info("*** Done with experiment: "+test_name+"\n")
