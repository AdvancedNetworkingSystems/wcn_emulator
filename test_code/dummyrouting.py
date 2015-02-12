
import sys
sys.path.append('../')
from network_builder import *
from os import kill, path, makedirs
from matplotlib.pyplot import ion
from collections import defaultdict
import random 
import time
import ast
import networkx as nx

import signal

from test_generic import *

class OptimizeGraphChoice:
    """ helper class to optimize the choice of the 
    graphs to run the simulations """

    def compute_topology_failure_maps(self, graph_dict, min_run_number):
        failure_map = defaultdict(list)
        topo_failures = {}
        for topo, graph in graph_dict.items():
            failure_list = self.get_emulation_runs_per_topology(graph)
            failure_number = len(failure_list)
            for idx in range(failure_number):
                failure_map[idx].append(topo)
                topo_failures[topo] = failure_number

        min_fail = len(
                filter(lambda z: z>min_run_number,
                [len(y[1]) for y in sorted(
                    failure_map.items(), key = lambda x: x[0])]) 
                )
        print "The maximum number of failures avilable with "
        print min_run_number, "runs, is ", min_fail

        # file -> failure list
        file_dict = defaultdict(list)

        print filter(lambda z: z>min_run_number,
                [len(y[1]) for y in sorted(
                    failure_map.items(), key = lambda x: x[0])]) 

        failure_counter = [0]*min_fail

        for (idx, file_list) in \
            sorted(failure_map.items(), key = lambda x: x[0])[:min_fail]:
                random.shuffle(file_list)
                for f in file_list:
                    if f in file_dict:
                        continue
                    rem_runs = range(idx, min(topo_failures[f], min_fail))
                    file_dict[f] = rem_runs
                    for r in rem_runs:
                        failure_counter[r] += 1
                    if failure_counter[idx] >=  min_run_number:
                        break

        for f,runs in sorted(file_dict.items(), key = lambda x: len(x[1])):
            print f, [1 if x in runs else 0 for x in range(min_fail)]

        return file_dict

    def get_emulation_runs_per_topology(self, graph):
        """ return a list of nodes ordered by centrality that can be removed.
        Return only nodes in the core graph (no leaves) that can be removed
        from the network without partitioning the network, (excluding the leaf
        nodes attached to the node that is removed, which are obviously
        partitioned when removing the core node). 
        In this script this is necessary because not all the graphs support 
        the same number or run_ids. Some graph may allow 10 runs (10 failures)
        while other 8 failures. I pre-parse the topology to identify this number, 
        then i run the simulations with the sufficient number of graphs that 
        allow me to have a minimum number of repetitions for each run_id (for each
        failure). The minimum number is taken from the runs parameter in 
        command line """

        purged_graph = graph.copy()
        centList =  sorted(
                [n for n in nx.betweenness_centrality(purged_graph).items() \
                        if n[1] > 0], key = lambda x: -x[1])
        deg_dict = purged_graph.degree()
        for node, deg in deg_dict.items():
            if deg == 1:
                purged_graph.remove_node(node)

        fallible_nodes = []
        for idx, n in enumerate(centList):
            gg = purged_graph.copy()
            gg.remove_node(n[0])
            conSize = len(nx.connected_components(gg)[0])
            if conSize == len(gg):
                purgable_nodes = [n[0]] + \
                        [n for n in graph.neighbors(n[0]) if graph.degree(n) == 1]
                fallible_nodes.append(purgable_nodes)
        return fallible_nodes


class dummyRoutingTest(MininetTest):

    def __init__(self, mininet, duration=10):

        super(dummyRoutingTest, self).__init__(mininet, path, duration)
        self.centList = []


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
            if type(self.stopAllNodes) == int:
                self.centList = self.getCentrality()[:self.stopAllNodes]
            elif type(self.stopAllNodes) == list:
                for idx in self.stopAllNodes:
                    self.centList.append(self.getCentrality()[idx])

        for runid in range(len(self.centList)):
            info("\nStarting run " + str(runid) + "\n")
            self.runId = str(runid)
            if self.stopAllNodes:
                self.nodeCrashed = self.centList.pop(0)

            if not self.startRun():
                # some times process are not killed in time, UDP
                # ports are still occupied and the next run can not
                # start correctly. I kill everything, wait some time, try 
                # to restart. If something still goes wrong i stop the emulation
                self.killAll()
                time.sleep(10)
                info("\nWARNING: run_id " + str(runid) + " could not start, retrying...\n")
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
            for pid in self.pendingProc.keys():
                self.sendSig(pid, signal.SIGTERM)
            time.sleep(2)
            # in case some process got stuck:
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
        o = OptimizeGraphChoice()
        return o.get_emulation_runs_per_topology(self.graph)

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
            # convert option in a python object
            if args['stopAllNodes'] == '':
                # stop all the nodes 
                self.stopAllNodes = len(self.graph)
            else:
                try:
                    s = ast.literal_eval(args["stopAllNodes"])
                except ValueError:
                    error("Option " + args["stopAllNodes"] + " is not valid")
                    exit(1)
                if type(s) == int:
                    if s <= 0:
                        error("\nPlease stopAllNodes must be > 0\n")
                        sys.exit(1)
                    self.stopAllNodes = s
                    info("... limited to " + args["stopAllNodes"] + "nodes.")
                elif type(s) == list and s:
                    self.stopAllNodes = s
                    info("... limited to the list of nodes:" + str(s))
                else:
                    error("Option " + args["stopAllNodes"] + " is not valid")

            self.nodeCrashed = []
        else:
            self.stopAllNodes = False

        self.runId = 0

        duration = int(self.parseTime(args["duration"]))

        super(dummyRoutingRandomTest, self).__init__(mininet, duration)
        self.localPrefix = os.path.basename(os.path.splitext(
            mininet.gg_name)[0])
        self.setPrefix(name + self.localPrefix)


