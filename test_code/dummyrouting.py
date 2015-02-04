
import sys
sys.path.append('../')
from network_builder import *
from os import kill, path, makedirs
from matplotlib.pyplot import ion
import random 
import time

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
            self.centList = self.getCentrality()[:self.stopAllNodes]


        for runid in range(len(self.centList)):
            info("\nStarting run " + str(runid) + "\n")
            self.runId = str(runid)
            if self.stopAllNodes:
                self.nodeCrashed = self.centList.pop(0)
            print "WWWWWWWWWWW", self.nodeCrashed

            if not self.startRun():
                # some times process are not killed in time, UDP
                # ports are still occupied and the next run can not
                # start correctly. I kill everything, wait some time, try 
                # to restart. If something still goes wrong i stop the emulation
                self.killAll()
                time.sleep(10)
                info("\nWARNING: run_id " + str(runid) + " could not start, retying...\n")
                if not self.startRun():
                    error("\nERROR: run_id " + str(runid) + " could not start!" + \
                            "please check the logs\n")
                    sys.exit(1)



            eventDict = {
                    self.startLog:["Start logging", self.sendSignal,
                        {"sig":signal.SIGUSR1}],
                    self.stopNode:["Stopping node(s) " + str(self.nodeCrashed) + " ",
                        self.sendSignal, {"sig":signal.SIGTSTP,
                        "hostName":self.nodeCrashed}],
                    self.stopLog:["Stop logging", self.sendSignal,
                        {"sig":signal.SIGUSR1}]}

            eventList = []
            relativeTime = 0
            for e in sorted(eventDict.keys()):
                if e > 0:
                    data = eventDict[e]
                    eventList.append([e - relativeTime] + data)
                    relativeTime += (e - relativeTime)

            waitTime = self.duration - relativeTime

            for event in eventList:
                sleep(event[0])
                print event
                event[2](**event[3])
                info(event[1] + str(time.time()) + "\n")
            sleep(waitTime)
            self.killAll(signal.SIGTERM)
            time.sleep(2)
            self.killAll()
            time.sleep(2)
            #sendSignal(signal.SIGUSR2)
            #if self.startLog > 0:
            #    duration -= self.startLog
            #    sleep(self.startLog)
            #    print "XX", self.startLog, duration, time.time()
            #    # this is interpreted by the daemons as 
            #    # "start (or stop) logging"
            #    self.sendSignal(signal.SIGUSR1)
            #    info("\nStart logging now!\n") 
            #if self.stopNode > 0:
            #    crashTime = self.stopNode - self.startLog
            #    duration -= crashTime
            #    sleep(crashTime)
            #    print "XX", self.stopNode, duration, time.time()
            #    # this is interpreted as "crash"
            #    self.sendSignal(signal.SIGTSTP, self.nodeCrashed)
            #    info("\nSent crash signal to node " + str(self.nodeCrashed))
            #if self.stopLog > 0:
            #    stopTime = self.stopLog - (self.startLog + self.stopNode)
            #    duration -= stopTime
            #    print "XX", stopTime, duration, time.time()
            #    sleep(stopTime)
            #    self.sendSignal(signal.SIGUSR1)
            #    info("\nStop logging now!\n") 
            #print "XX", time.time(), duration
            #sleep(duration)
            ## this is interpreted by the daemons as 
            ## "restart a new run"
            #self.sendSignal(signal.SIGUSR2)




    def getCentrality(self):
        """ return a list of nodes ordered by centrality. Return only nodes
        that can be removed from the network without partitioning the network,
        (excluding the leaf nodes attached to the node that is removed, which 
        are obviously partitioned when removing the core node) """

        centList =  sorted(
                [n for n in nx.betweenness_centrality(self.graph).items() \
                        if n[1] > 0], key = lambda x: -x[1])
        connected_centlist = []
        for idx, n in enumerate(centList):
            gg = self.graph.copy()
            neighs = gg.neighbors(n[0])
            leaf_neighs = []
            for neigh in neighs:
                if len(gg.neighbors(neigh)) == 1:
                    gg.remove_node(neigh)
                    leaf_neighs.append(neigh)
            gg.remove_node(n[0])
            conSize = len(nx.connected_components(gg)[0])
            if conSize == len(self.graph) - (len(leaf_neighs) + 1):
                connected_centlist.append([n[0]] + leaf_neighs)
        return connected_centlist

    def startRun(self):

        rNode = ""
        hostList = self.getAllHosts()

        if rNode:
            info("\nChosen node " + str(rNode) + " to fail\n")

        for h in hostList:
            args = " --runid=" + self.runId
            if self.logInterval != "":
                args += " " + self.logInterval
            if self.verbose != "":
                args += " " + self.verbose
            if self.centralityTuning != "":
                args += " " + self.centralityTuning

            launch_pid = self.launchdummyRouting(h, args)

            if self.dump:
                self.launchSniffer(h)

        if not self.nodeCrashed and rNode:
            self.nodeCrashed = [rNode]
        return launch_pid

    def sendSignal(self, sig, hostName=""):
        for pid, h in self.pendingProc.items():
            if hostName:
                for host in hostName:
                    if host == h.name:
                        print "sending signal to host:", host, ", pid", pid
                        self.sendSig(pid, sig)
            # send to all 
            else:
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
            self.stopNode = int(self.parseTime(args["stopNode"]))
        else:
            self.stopNode = -1

        if "nodeCrashed" in args.keys():
            self.nodeCrashed = [args["nodeCrashed"]]
        else:
            self.nodeCrashed = ""

        if "stopAllNodes" in args.keys():
            info("Going to stop all the nodes in sequence")
            if args["stopAllNodes"].isdigit():
                stop_n = int(args["stopAllNodes"])
                if stop_n <= 0:
                    error("\nPlease stopAllNodes must be > 0\n")
                    sys.exit(1)
                self.stopAllNodes = stop_n
                info("... limited to " + args["stopAllNodes"] + "nodes.")
            else:
                self.stopAllNodes = len(mininet.gg)
            self.nodeCrashed = []
        else:
            self.stopAllNodes = False

        self.runId = 0

        duration = int(self.parseTime(args["duration"]))

        super(dummyRoutingRandomTest, self).__init__(mininet, duration)
        self.localPrefix = os.path.basename(os.path.splitext(
            mininet.gg_name)[0])
        self.setPrefix(name + self.localPrefix)


