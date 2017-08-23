#!/usr/bin/env python
import sys
from os import path
import inherit_config_parser
import ConfigParser
import inspect
import StringIO
from time import time
from parameters_parser import parameters


# add the nepa_test directory to sys path
sys.path.append(path.dirname(sys.argv[0]))
sys.path.append('test_code')
sys.path.insert(0, './')


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
            error("Can not find configuration " + stanza +
                  " in file " + fileName + "\n")
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

    def link_conf(self):
        link_opts = {}
        if self.getConfigurations("link_bw"):
            link_opts["bw"] = int(self.getConfigurations("link_bw"))
        if self.getConfigurations("link_mean_delay"):
            link_opts["delay"] = (self.getConfigurations("link_mean_delay"))
        if self.getConfigurations("link_delay_sd"):
            link_opts["jitter"] = (self.getConfigurations("link_delay_sd"))
        if self.getConfigurations("link_delay_distribution"):
            link_opts["delay_distribution"] = \
                (self.getConfigurations("link_delay_distribution"))
        if self.getConfigurations("link_loss"):
            link_opts["loss"] = (self.getConfigurations("link_loss"))
        return link_opts
