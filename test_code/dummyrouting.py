
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

        if self.stopRandomNode != -1:
            rNode = random.sample(hostList, 1)[0]

        for h in hostList:
            args = ""
            if h == rNode:
                args = "6969 6969 " + str(self.stopRandomNode)
                info("\nGoing to stop node"+str(h)+" at time " + \
                        self.stopRandomNode + "\n")
            self.launchdummyRouting(h, args)
            if self.dump:
                self.launchSniffer(h)

        info("\nWaiting completion...\n")
        sleep(self.duration)
        self.killAll(signal.SIGTERM)
        self.killAll()

class dummyRoutingRandomTest(dummyRoutingTest):

    def __init__(self, mininet, name, args):

        if "dumpWithTCPDump" in args.keys():
            self.dump = True
        else:
            self.dump = False

        if "stopRandomNode" in args.keys():
            timeStop = args["stopRandomNode"]
            if timeStop[-1] == "s":
                self.stopRandomNode = timeStop[:-1]
            elif timeStop[-1] == "m":
                self.stopRandomNode = int(timeStop[:-1])*60
            else:
                self.stopRandomNode = timeStop
        else:
            self.stopRandomNode = -1

        duration = int(args["duration"])
        super(dummyRoutingRandomTest, self).__init__(mininet, duration)
        self.setPrefix(name)


