
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

        if self.stopAllNodes:
            self.centList = self.getCentrality()
            # FIXME this is just for testing, remove this
            self.numRuns = 3 #len(self.centList)

        for runid in range(self.numRuns):
            info("\nStarting run " + str(runid) + "\n")
            self.runId = runid
            if self.stopAllNodes:
                nc = self.centList.pop()[0]
                for idx, h in enumerate(self.getAllHosts()):
                    if h.name == nc:
                        self.nodeCrashed = idx
                        break

            self.startRun()

            # FIXME can not send make things fail if i don't restart
            # the processes. So i should remove the stopNode option
            # and use another signal that i send only to the node
            # that is supposed to die  
            info("\nWaiting completion...\n")
            duration = self.duration
            import time
            print "XX", duration, time.time()
            if self.startLog > 0:
                duration -= self.startLog
                sleep(self.startLog)
                print "XX", self.startLog, duration, time.time()
                # this is interpreted by the daemons as 
                # "start (or stop) logging"
                self.sendSignal(signal.SIGUSR1)
                info("\nStart logging now!\n") 
            if self.stopLog > 0:
                stopTime = self.stopLog - self.startLog
                duration -= stopTime
                print "XX", stopTime, duration, time.time()
                sleep(stopTime)
                self.sendSignal(signal.SIGUSR1)
                info("\nStop logging now!\n") 
            print "XX", time.time(), duration
            sleep(duration)
            # this is interpreted by the daemons as 
            # "restart a new run"
            self.sendSignal(signal.SIGUSR2)

        self.killAll(signal.SIGTERM)
        self.killAll()



    def getCentrality(self):
        """ return a list of nodes ordered by centrality. Return only nodes
        that can be removed from the network without partitioning the network """

        centList =  sorted(
                [n for n in nx.betweenness_centrality(self.graph).items() if n[1] > 0],
                key = lambda x: x[1])
        for idx, n in enumerate(centList[:]):
            gg = self.graph.copy()
            gg.remove_node(n[0])
            conSize = len(nx.connected_components(gg)[0])
            if conSize != len(self.graph) - 1:
                del centList[idx]
        return centList

    def startRun(self):

        rNode = ""
        hostList = self.getAllHosts()
        if self.stopNode and self.stopCentralNode != -1:
            # split the degree list in 5 parts ordered for their degree
            # the input value selects one of the parts, and one
            # random node in this part will be returned
            deg = sorted(
                    [n for n in self.graph.degree().items() if n[1] > 1],
                    key = lambda x: x[1])
            partLength = len(deg)/4
            rr = random.sample(range(self.stopCentralNode*partLength, 
                min((self.stopCentralNode+1)*partLength, len(deg))), 1)[0]
            nodeName = deg[rr][0]
            sys.exit(1)
            for h in hostList:
                if h.name == nodeName:
                    rNode = h
                    break

        elif self.stopNode and self.nodeCrashed == "":
            rNode = random.sample(hostList, 1)[0]

        elif self.stopNode and self.nodeCrashed != "":
            rNode = hostList[self.nodeCrashed]

        if rNode:
            info("\nChosen node " + str(rNode) + " to fail\n")

        if self.runId == 0:
            for h in hostList:
                args = ""
                if h == rNode:
                    args = str(self.stopNode)
                if self.logInterval != "":
                    args += " " + self.logInterval
                if self.verbose != "":
                    args += " " + self.verbose
                if self.centralityTuning != "":
                    args += " " + self.centralityTuning

                self.launchdummyRouting(h, args)
                if self.dump:
                    self.launchSniffer(h)

    def sendSignal(self, sig):
        for pid in self.pendingProc.keys():
            self.sendSig(pid, sig)

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

        self.graph = mininet.gg
        if "dumpWithTCPDump" in args.keys():
            self.dump = True
        else:
            self.dump = False
        # Doesn't work. If processes are started one after the other
        # there is misalignment in the relative log time. I use 
        # a signal instead.
        #if "startLog" in args.keys():
        #    self.startLog = "--startlog " + self.parseTime(args["startLog"])
        #else:
        #    self.startLog = ""

        if "startLog" in args.keys():
            self.startLog = float(self.parseTime(args["startLog"]))
        else:
            self.startLog = -1

        if "stopLog" in args.keys():
            self.stopLog = float(self.parseTime(args["stopLog"]))
        else:
            self.stopLog = -1

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

        if "stopAllNodes" in args.keys():
            self.stopAllNodes = True
            self.nodeCrashed = ""
            info("Going to stop all the nodes in sequence")
        else:
            self.stopAllNodes = False

        if "stopCentralNode" in args.keys():
            self.stopCentralNode = int(args["stopCentralNode"])
            if self.stopCentralNode < 0 or self.stopCentralNode > 3:
                error("\nPlease stopCentralNode must be between 0 and 3\n")
                sys.exit(1)
        else:
            self.stopCentralNode = -1

        # stopAllNodes will confilct with numRuns!
        if "numRuns" in args.keys():
            if self.stopAllNodes == True:
                error("Cannot set stopAllNodes and numRuns in the same configuration")
                sys.exit(1)
            self.numRuns = int(args["numRuns"])
        else:
            self.numRuns = 1

        self.runId = 0

        duration = int(self.parseTime(args["duration"]))

        super(dummyRoutingRandomTest, self).__init__(mininet, duration)
        self.setPrefix(name)


