#!/usr/bin/env python
import sys
from inherit_config_parser import InheritConfigParser
import ConfigParser
import inspect

sys.path.append('test_code')

import os 
import StringIO

from time import time

from parameters_parser import parameters
from network_builder import *
from test_code import *



class conf(parameters):
    def checkCorrectness(self):
        self.checkNeededParams()
        return True

class configurationFile():

    mandatoryOptions = {"testModule":None
            , "testClass":None}
    confParams = {}
    className = None
    def __init__(self, fileName, stanza, overrideOption=""):
        """ receives the configuration fileName and the stanza to be 
        parsed """

        if not os.path.isfile(fileName):
            error("Can not open the configuration file: " + fileName\
                + "\n")
            sys.exit(1)
        self.parser = InheritConfigParser()
        self.parser.optionxform = str
        self.parser.read(fileName)
        self.testName = stanza 

        if stanza not in self.parser.sections():
            error("Can not find configuration " + stanza \
                    + " in file " + fileName + "\n")
            sys.exit(1)

        for o in self.mandatoryOptions:
            self.mandatoryOptions[o] = \
                self.getConfigurations(o, raiseError=True)

        # this builds a module with the correct path in python namespace
        moduleName = "test_code." + self.mandatoryOptions['testModule']

        if moduleName not in sys.modules:
            errorString = "ERROR: no " \
                + self.mandatoryOptions['testModule'] \
                + " module  has been loaded!\n"
            error(errorString)
            sys.exit(1)

        if self.mandatoryOptions['testClass'] not in \
                zip(*inspect.getmembers(sys.modules[moduleName]))[0]:
            errorString = "ERROR: no " \
                + self.mandatoryOptions['testClass'] \
                + " simulation class is present in "\
                + moduleName.replace(".","/")+".py" + "\n"
            error(errorString)
            sys.exit(1)

        self.className = getattr(sys.modules[moduleName],
            self.mandatoryOptions['testClass'])

        for name, value in self.parser.items(self.testName):
            self.confParams[name] = value

        if overrideOption:
            overrideConf = StringIO.StringIO("[DEFAULT]\n"+ overrideOption)
            tmpParser = ConfigParser.ConfigParser()
            tmpParser.optionxform = str
            tmpParser.readfp(overrideConf)
            for name, value in tmpParser.defaults().items():
                print name, value
                self.confParams[name] = value

    def getConfigurations(self, name, raiseError=False):
        try:
            r = self.parser.get(self.testName, name)
        except ConfigParser.NoOptionError:
            if raiseError:
                error("No option \'" + name + "\' found!\n")
                sys.exit()
            else:
                return None
        return r

if __name__ == '__main__':
    setLogLevel('info')
    need = [
            ("-f", ["configFile", True, "",
                "file with the available configurations", str]),
            ("-t", ["testName", True, "",
                "name of the configuration to run", str])
           ]
    opt = [
            ("-d", ["drawGraph", False, False,
                "draw the graph before you run the test", int]),
            ("-g", ["graphFile", True, "",
                "file with the topology (overrides configuration)", str]),
            ("-s", ["shortestPaths", True, True,
                "fill the routing tables with the shortest route"\
                + " to any node", int]),
            ("-o", ["overrideOption", True, "",
                "some string option to override the ini file", str]),
          ]

    P = conf(os.path.basename(__file__),need, opt)
    P.parseArgs()
    if P.checkCorrectness() == False:
        P.printUsage()
        sys.exit(1)

    configFile = P.getParam("configFile")
    testName = P.getParam("testName")
    C = configurationFile(configFile, testName, P.getParam("overrideOption"))
    networkGraph = P.getParam("graphFile")
    if networkGraph == "":
        networkGraph = C.getConfigurations("graphDefinition")
        if networkGraph == None:
            error("No graph topology specified in config file or command " + \
                "line!\n")
            sys.exit(1)
    drawGraph = P.getParam("drawGraph")

    net = GraphNet(networkGraph, draw = drawGraph)
    net.start()
    net.enableForwarding()

    if P.getParam("shortestPaths") == True:
        net.setShortestRoutes()
    testPath = testName+"_"+str(int(time()))
    repeat = C.getConfigurations("times")
    if repeat == None:
        repeat = 1
    else:
        repeat = int(repeat)
    for i in range(repeat):
        info("+++++++ Round: "+str(i+1) + '\n')
        test = C.className(net, testPath, C.confParams)
        test.runTest()
    net.stop()
    test.changePermissions()
    info("*** Done with experiment: " + testName + "\n")
