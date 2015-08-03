
import sys
sys.path.append('../')
import os
sys.path.append('scripts/pop-routing/')
from network_builder import *
import random
import time
from dummyrouting import dummyRoutingRandomTest
from compute_theoretical_values import ComputeTheoreticalValues

import signal

from test_generic import *


class OLSRTest(dummyRoutingRandomTest):

    def launch_sniffer(self, host):

        cmd = "tcpdump -i any -n -X -e "

        logfile = self.prefix + host.name + "-dump.log"

        params = {}
        params['>'] = logfile
        params['2>'] = logfile

        return self.bgCmd(host, True, cmd,
                          *reduce(lambda x, y: x + y, params.items()))

    def launch_ping(self, host, dest_array, run_id=0):

        for idx, ip in enumerate(dest_array):
            cmd = "ping " + ip

            log_str = "Host " + host.name + " launching command:\n"
            info(log_str)
            info(cmd + "\n")
            logfile = self.prefix + host.name + \
                "_ping_" + str(idx) + "_runId_" + str(run_id) + ".log"
            params = {}
            params['>'] = logfile
            params['2>'] = logfile
            self.bgCmd(host, True, cmd,
                       reduce(lambda x, y: x + y, params.items()))

    def launch_OLSR(self, host,  args):

        cmd = "../olsrd/olsrd " + args

        log_str = "Host " + host.name + " launching command:\n"
        info(log_str)
        info(cmd + "\n")
        logfile = self.prefix + host.name + ".log"

        params = {}
        params['>'] = logfile
        params['2>'] = logfile

        return self.bgCmd(host, True, cmd,
                          *reduce(lambda x, y: x + y, params.items()))

    def runTest(self):

        info("*** Launching OLSR test\n")
        info("Data folder: "+self.prefix+"\n")

        self.stopNodeList = []
        if self.stopAllNodes:
            self.stopNodeList = self.getCentrality()[:self.stopAllNodes]
        elif self.stopList:
            self.stopNodeList = [[self.number_to_host(i) for i in self.stopList]]
        run_ids = range(len(self.stopNodeList))

        if not run_ids:
            # do at least one run
            run_ids = [0]
        for run_id in run_ids:
            info("\nStarting run " + str(run_id) + "\n")
            if self.stopNodeList:
                self.nodeCrashed = self.stopNodeList.pop(0)
            else:
                self.nodeCrashed = None

            if not self.startRun(run_id=run_id):
                # some times process are not killed in time, UDP
                # ports are still occupied and the next run can not
                # start correctly. I kill everything, wait some time, try
                # to restart. If something still goes wrong i stop
                # the emulation

                self.killAll()
                time.sleep(10)
                info("\nWARNING: run_id " + str(run_id) +
                     " could not start, retrying...\n")
                if not self.startRun(run_id):
                    error("\nERROR: run_id " + str(run_id) +
                          " could not start!" +
                          "please check the logs\n")
                    sys.exit(1)

            eventDict = {
                self.startLog: ["start/stop logging ",
                                self.sendSignal, {"sig": signal.SIGUSR1}
                                ],
                self.stopLog: ["Start/stop logging ",
                               self.sendSignal, {"sig": signal.SIGUSR1}
                               ]
                }

            if self.nodeCrashed:
                eventDict[self.stopTime] = ["Stopping node(s) " + str(self.nodeCrashed) +
                                " at time " + str(self.stopTime) + "\n", 
                                self.sendSignal,
                                {"sig": signal.SIGUSR2,
                                 "hostName": self.nodeCrashed}
                                ]


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
                event[2](**event[3])
                info(event[1] + str(time.time()) + "\n")
            sleep(waitTime)
            for pid in self.pendingProc.keys():
                self.sendSig(pid, signal.SIGTERM)
            time.sleep(2)
            self.killAll()
            time.sleep(2)


    def getCentrality(self):

        node_centrality_posteriori = {}
        centrality = {}
        for n in self.graph.nodes():
            gg = self.graph.copy()
            edges = self.graph.edges([n]) 
            gg.remove_node(n)
            # compute the connected components
            # WARNING: connected_components should return a list 
            # sorted by size, largest first. It does not, so i resort them
            unsorted_comp = list(nx.connected_components(gg))
            comp = sorted(unsorted_comp, key = lambda x: -len(x))
            # re-add the node
            gg.add_node(n)
            # re-add the edges to nodes in the main component
            for (fr, to) in edges:
                if fr in comp[0]:
                    gg.add_edge(fr, n)
                if to in comp[0]:
                    gg.add_edge(n, to)
            # now compute the centrality. This tells how important is the node
            # for the main connected component. If this is 0, it is not worth
            # to remove this node
            cent = nx.betweenness_centrality(gg)[n]
            isolated_nodes = [x for component in comp[1:] for x in component]
            node_centrality_posteriori[n] = [cent, [n] + isolated_nodes]
            centrality[n] = cent
        betw = [x for x in nx.betweenness_centrality(self.graph).items()\
                if x[1] > 0 and node_centrality_posteriori[x[0]][0] > 0]

        return [node_centrality_posteriori[k[0]][1] for k in sorted(betw, key=lambda x: -x[1])]

    def startRun(self, run_id=0):

        rNode = ""
        host_list = self.getAllHosts()

        # default values
        hello_timer = self.HelloInterval
        tc_timer = self.TcInterval

        if rNode:
            info("\nChosen node " + str(rNode) + " to fail\n")

        if self.popRouting:
            c = ComputeTheoreticalValues(graph_file=None, graph=self.graph,
                    cH=hello_timer, cTC=tc_timer)
            cent = nx.betweenness_centrality(self.graph)
            deg = nx.degree(self.graph)
            for (h, cc) in sorted(cent.items(), key = lambda x: -x[1]):
                print deg[h],",", cent[h], ",", c.Hi[h], ",", c.TCi[h]

        # h_load_pop = 0
        # h_load_nopop = 0
        # tc_load_pop = 0
        # tc_load_nopop = 0
        #for h in host_list:
        #    h_load_pop += len(self.graph[h.name])/c.Hi[h.name]
        #    h_load_nopop += len(self.graph[h.name])/hello_timer
        #    tc_load_pop += len(self.graph.edges())/c.TCi[h.name]
        #    tc_load_nopop += len(self.graph.edges())/tc_timer
        #print "XXXXXXXXX POP, h,tc", h_load_pop, tc_load_pop
        #print "XXXXXXXXX NOPOP, h,tc", h_load_nopop, tc_load_nopop
        for idx, h in enumerate(host_list):
            intf = h.intfList()
            intf_list = ' '.join(["\"" + i.name + "\"" for i in intf])

            # set the main IP of the host to the one ending with .1
            main_ip = ""

            log_folder = self.logPrefix + "OLSR-log-" + str(self.runId) + "/"
            try:
                os.makedirs(log_folder)
            except:
                pass
            olsr_conf_file = self.prefix + h.name + ".conf"
            olsr_json_file = log_folder + h.name
            olsr_lock_file = "/var/run/" + h.name + str(time.time()) + ".lock"
            f = open(olsr_conf_file, "w")
            if self.popRouting:
                hello_timer = c.Hi[h.name]
                tc_timer = c.TCi[h.name]
            hello_validity = hello_timer * 3
            tc_validity = tc_timer * 3
            print >> f, self.conf_file % (olsr_lock_file, run_id,
                                          olsr_json_file, intf_list,
                                          hello_timer, hello_validity,
                                          tc_timer, tc_validity)
            f.close()
            args = "-f " + os.path.abspath(olsr_conf_file)

            launch_pid = self.launch_OLSR(h, args)

            if self.dump:
                self.launch_sniffer(h)

        if not self.nodeCrashed and rNode:
            self.nodeCrashed = [rNode]
        return launch_pid

    def start_ping(self, exclude=[], number=1, run_id=0):

        print exclude
        host_list = self.getAllHosts()
        exclude_ips = []
        destinations = {}

        for h in host_list:
            if h.name in exclude:
                exclude_ips.append(h.intfList()[0].ip)
            else:
                destinations[h] = []

        for h in destinations:
            intf = h.intfList()
            counter = 1000
            while len(destinations[h]) < self.NumPing:
                d = self.get_random_destination()
                if d != intf[0].ip and d not in exclude_ips:
                    destinations[h].append(d)
                counter -= 1
                if counter < 0:
                    error("Can not find ping destination for host " +
                          h.name + " and NumPing " + str(self.NumPing) +
                          " your configuration may be wicked." +
                          "Nodes that will fail are:" + str(exclude))
                    exit(1)

        for (h, ip_list) in destinations.items():
                self.launch_ping(h, ip_list, run_id=run_id)

    def number_to_host(self, host_number):

        host_list = self.getAllHosts()
        for host in host_list:
            number = int(host.name.split("_")[0][1:])
            if host_number == number:
                return host.name
        print "ERROR: no host number", host_number, "in host_list:"
        print "  ", self.getAllHosts()
        return None

    def get_random_destination(self):

        host_list = self.getAllHosts()
        d = random.sample(host_list, 1)[0]
        dest_ip = d.intfList()[0].ip
        return dest_ip

    def sendSignal(self, sig, hostName=""):
        for pid, h in self.pendingProc.items():
            if hostName:
                for host in hostName:
                    if host == h.name:
                        print "sending signal to host:", host, ", pid", pid
                        self.sendSig(pid, sig)
            # send to all
            else:
                print "sending signal to all hosts:", sig
                self.sendSig(pid, sig)

    def __init__(self, mininet, name, args):

        super(OLSRTest, self).__init__(mininet, name, args)

        self.mininet = mininet
        self.centList = []
        self.stopNodes = []
        self.stopNodeList = []

        self.conf_file = """
        DebugLevel  1
        IpVersion 4
        FIBMetric "flat"
        LinkQualityFishEye  0
        LockFile "%s"
        Hna4
        {
        }
        Hna6
        {
        }
        LoadPlugin "../olsrd/lib/dumprt/olsrd_dumprt.so.0.0"{
        PlParam "run_id" "%d"
        PlParam "log_file" "%s"
        PlParam "log_interval_msec" "300"
        }

        InterfaceDefaults {
        }

        Interface %s
        {
        HelloInterval       %f
        HelloValidityTime   %f
        TcInterval          %f
        TcValidityTime      %f
        }
        """
        if "logPrefix" in args.keys():
            self.logPrefix = args["logPrefix"]
        else:
            self.logPrefix = "/tmp/"

        if "runId" in args.keys():
            self.runId = args["runId"]
        else:
            self.runId = 0

        if "popRouting" in args.keys() and\
                args['popRouting'] == 'True':
            self.popRouting = True
        else:
            self.popRouting = False

        if "NumPing" in args.keys():
            self.NumPing = int(args["NumPing"])
        else:
            self.NumPing = 1

        if "HelloInterval" in args.keys():
            self.HelloInterval = float(args["HelloInterval"])
        else:
            self.HelloInterval = 2

        if "TcInterval" in args.keys():
            self.TcInterval = float(args["TcInterval"])
        else:
            self.TcInterval = 5

        if "stopAllNodes" in args.keys():
            self.stopAllNodes = int(args["stopAllNodes"])
        else:
            self.stopAllNodes = []

        if "stopList" in args.keys():
            self.stopList = map(int, args["stopList"].split(","))
        else:
            self.stopList = []

        # TODO import parseTime from dummyrouting
        if "stopTime" in args.keys():
            self.stopTime = float(args["stopTime"])
        elif self.stopAllNodes or self.stopList:
            print "ERROR: you set one of stopAllNodes/stopList" +\
                  "but did not set stopTime"
            exit()
        else:
            self.stopTime = 0
