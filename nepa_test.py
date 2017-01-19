#!/usr/bin/env python
import sys
import inherit_config_parser
import ConfigParser
import inspect

sys.path.append('test_code')

from os import path
from time import time

from parameters_parser import parameters
from network_builder import *
from test_code import *


class conf(parameters):
    def checkCorrectness(self):
        self.checkNeededParams()
        return True


class ConfigurationFile():

    mandatoryOptions = {"testModule": None, "testClass": None, "times": 1}
    confParams = {}
    className = None

    def __init__(self, fileName, stanza, overrideOption=""):
        # check if filename esists
        if not path.isfile(fileName):
            error("Can not open the configuration file: " + fileName + "\n")
            sys.exit(1)
        self.parser = inherit_config_parser.InheritConfigParser()
        self.parser.optionxform = str
        self.parser.read(fileName)

        self.testName = stanza
        if stanza not in self.parser.sections():
            error("Can not find configuration " + stanza
                  + " in file " + fileName + "\n")
            sys.exit(1)
        for o in self.mandatoryOptions:
            self.mandatoryOptions[o] = \
                self.getConfigurations(o, raiseError=True)

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
                + moduleName + "\n"
            error(errorString)
            sys.exit(1)

        self.className = getattr(sys.modules[moduleName],
                                 self.mandatoryOptions['testClass'])

        for name, value in self.parser.items(self.testName):
            self.confParams[name] = value

        if overrideOption:
            options = overrideOption.replace(",", "\n")
            overrideConf = StringIO.StringIO("[DEFAULT]\n" + options + "\n")
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


def link_conf(conf):
    link_opts = {}
    if conf.getConfigurations("link_bw"):
        link_opts["bw"] = int(conf.getConfigurations("link_bw"))
    if conf.getConfigurations("link_mean_delay"):
        link_opts["delay"] = (conf.getConfigurations("link_mean_delay"))
    if conf.getConfigurations("link_delay_sd"):
        link_opts["jitter"] = (conf.getConfigurations("link_delay_sd"))
    if conf.getConfigurations("link_delay_distribution"):
        link_opts["delay_distribution"] = \
            (conf.getConfigurations("link_delay_distribution"))
    if conf.getConfigurations("link_loss"):
        link_opts["loss"] = (conf.getConfigurations("link_loss"))
    return link_opts


def nepa_test():
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
    C = ConfigurationFile(configFile, testName, P.getParam("overrideOption"))
    # parse the conf file
    networkGraph = P.getParam("graphFile")
    if networkGraph == "":
        networkGraph = C.getConfigurations("graphDefinition")
        if not networkGraph:
            error("No graph topology specified in conf file or command line!\n")
            sys.exit(1)
    drawGraph = P.getParam("drawGraph")

    link_opts = link_conf(C)

    net = GraphNet(networkGraph, draw=drawGraph, link_opts=link_opts)
    net.start()
    net.enableForwarding()
    enableShortestRoutes = C.getConfigurations("enableShortestRoutes")
    if not enableShortestRoutes or enableShortestRoutes.lower() == "true":
        net.setShortestRoutes()
    # CLI(net)
    graphname = networkGraph.split('/')[-1].split('.')[0]
    testPath = testName + "_" + graphname + "_" + str(int(time()))
    for i in range(int(C.getConfigurations("times"))):
        info("+++++++ Round: "+str(i+1) + '\n')
        test = C.className(net, testPath, C.confParams)
        test.runTest()
    net.stop()
    test.changePermissions()
    info("*** Done with experiment: " + testName + "\n")

if __name__ == "__main__":
    nepa_test()
