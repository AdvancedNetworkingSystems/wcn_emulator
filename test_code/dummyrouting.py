
import sys
sys.path.append('../')
from network_builder import *
from os import kill, path, makedirs
from matplotlib.pyplot import ion
import random 

import signal

from test_generic import *

class dummyRoutingTest(MininetTest):

    def __init__(self, mininet, duration=10):

        super(dummyRoutingTest, self).__init__(mininet, path, duration)


    def launchSniffer(self, host):

        cmd = "tcpdump -i any -n -X -e "

        logfile = self.prefix + host.name + "-dump.log"

        params = {}
        params['>'] = logfile
        params['2>'] = logfile


        return self.bgCmd(host, True, cmd,
            *reduce(lambda x, y: x + y, params.items()))


    def launchdummyRouting(self, host,  args):

        cmd = "../dummy_routing_protocol/routingdaemon.py " + \
                args

        logfile = self.prefix + host.name + ".log"

        params = {}
        params['>'] = logfile
        params['2>'] = logfile


        return self.bgCmd(host, True, cmd,
            *reduce(lambda x, y: x + y, params.items()))

    def runTest(self):

        info("*** Launching dummyRouting test\n")
        info("Data folder: "+self.prefix+"\n")

        rNode = ""

        hostList = self.getAllHosts()

        if self.stopNode and self.nodeCrashed == "":
            rNode = random.sample(hostList, 1)[0]
        if self.stopNode and self.nodeCrashed != "":
            info("Chosen node " + str(self.nodeCrashed) + " to fail\n")
            rNode = hostList[self.nodeCrashed]

        for h in hostList:
            args = ""
            if h == rNode:
                args = str(self.stopNode)
                info("\nGoing to stop node "+str(h)+" with argument " + \
                        self.stopNode + "\n")
            if self.startLog != "":
                args += " " + self.startLog
            if self.stopLog != "":
                args += " " + self.stopLog
            if self.logInterval != "":
                args += " " + self.logInterval
            if self.verbose != "":
                args += " " + self.verbose
            if self.centralityTuning != "":
                args += " " + self.centralityTuning

            self.launchdummyRouting(h, args)
            if self.dump:
                self.launchSniffer(h)

        info("\nWaiting completion...\n")
        sleep(self.duration)
        self.killAll(signal.SIGTERM)
        self.killAll()

    def parseTime(self, timeString):

        retString = ""
        if timeString.endswith('s'):
            retString = timeString[:-1]
        elif timeString.endswith('m'):
            retString = int(timeString[:-1])*60
        else:
            retString = timeString
        return str(retString)

class dummyRoutingRandomTest(dummyRoutingTest):

    def __init__(self, mininet, name, args):

        if "dumpWithTCPDump" in args.keys():
            self.dump = True
        else:
            self.dump = False

        if "startLog" in args.keys():
            self.startLog = "--startlog " + self.parseTime(args["startLog"])
        else:
            self.startLog = ""

        if "stopLog" in args.keys():
            self.stopLog = "--stoplog " + self.parseTime(args["stopLog"])
        else:
            self.stopLog = ""

        if "logInterval" in args.keys():
            self.logInterval = "--loginterval " \
                    + self.parseTime(args["logInterval"])
        else:
            self.logInterval = ""

        if "verbose" in args.keys():
            self.verbose = "-v "
        else:
            self.verbose = ""

        if "centralityTuning" in args.keys():
            self.centralityTuning = "-c "
        else:
            self.centralityTuning = ""

        if "stopNode" in args.keys():
            self.stopNode = "--crash "\
                    + self.parseTime(args["stopNode"])
        else:
            self.stopNode = ""

        if "nodeCrashed" in args.keys():
            self.nodeCrashed = int(args["nodeCrashed"])
        else:
            self.nodeCrashed = ""


        duration = int(self.parseTime(args["duration"]))

        super(dummyRoutingRandomTest, self).__init__(mininet, duration)
        self.setPrefix(name)

