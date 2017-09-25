import sys
from network_builder import *
from os import kill, path, makedirs
from matplotlib.pyplot import ion
from random import sample, randint
from mininet.util import pmonitor
from poprouting import ComputeTheoreticalValues

import time
import graph_utils as gu
import networkx as nx
import numpy as np
from test_generic import *
sys.path.append('../')


class princeTest(MininetTest):
    def __init__(self, mininet, duration=10):
        super(princeTest, self).__init__(mininet, path, duration)
        self.mininet = mininet
        self.centList = []
        self.stopNodes = []
        self.stopNodeList = []
        self.graph = mininet.gg
        self.prince_conf_template = """
        {
            "proto": {
                "protocol": "test",
                "host": "%s",
                "port": 2009,
                "timer_port": 1234,
                "refresh": 1,
                "log_file": "%s"
            },
            "graph-parser": {
                "heuristic": %i,
                "weights": %i,
                "recursive": 0,
                "stop_unchanged": 0,
                "multithreaded": 0
            }
        }
        """

    def launch_sniffer(self, host):
        dumpfile = self.prefix + host.name + "-dump.cap"
        cmd = "tcpdump -i any -n -X -e -w %s" % (dumpfile)
        return self.bgCmd(host, True, cmd)

    def launchPrince(self, host):
        prince_conf_file = self.prefix + host.name + "_prince.json"
        f_prince = open(prince_conf_file, "w")
        logfile = os.path.abspath(self.prefix + host.name + "_prince.log")
        with open(logfile, "w+") as fh:
            fh.close()
        os.chmod(logfile, 0o777)
        print >> f_prince, self.prince_conf_template % (host.defaultIntf().ip, logfile, self.heuristic, self.weights)
        f_prince.close()
        args = os.path.abspath(prince_conf_file)
        logfile = self.prefix + host.name + "_prince_out.log"
        cmd = "exec ../poprouting/output/prince " + args

        log_str = "Host " + host.name + " launching command:\n"
        info(log_str)
        info(cmd + "\n")
        params = {}
        params['>'] = logfile
        params['2>'] = logfile

        return self.bgCmd(host, True, cmd,
                          *reduce(lambda x, y: x + y, params.items()))

    def runTest(self):
        info("*** Launching Prince test\n")
        info("Data folder: " + self.prefix + "\n")
        plt.show()
        self.setupNetwork()
        self.performTests()
        info("Waiting completion...\n")
        self.wait(float(self.duration), log_resources={'net': 'netusage.csv'})
        self.tearDownNetwork()
        self.analyzeResults()

    def setupNetwork(self):
        for idx, host in enumerate(self.getAllHosts()):
            intf = host.intfList()
            self.intf_list = ' '.join(["\"" + i.name + "\"" for i in intf])
            launch_pid = self.launchRouting(host)
            if self.poprouting:
                pid = self.launchPrince(host)
            if self.dump:
                self.launch_sniffer(host)
            self.dumpNeigh(host)
            nx.write_adjlist(self.graph, self.prefix + "topology.adj")
            gu.save_netjson(self.graph, self.prefix)

    def dumpNeigh(self, host):
        idps = randint(0, 100)
        logfile = self.prefix + host.name.split('_')[0] + \
            "-" + str(idps) + "_neigh_$(date +%s).log"

        cmd = "./dumpNeigh.sh"
        params = {}
        params['>'] = logfile
        params['2>'] = logfile

        return self.bgCmd(host, True, cmd,
                          *reduce(lambda x, y: x + y, params.items()))

    def performTests(self):
        None  # to implement in subclass

    def launchRouting(self):
        None

    def tearDownNetwork(self):
        self.killAll()

    def analyzeResults(self):
        bcs = nx.betweenness_centrality(self.graph, endpoints=True)
        ctv = ComputeTheoreticalValues(graph=self.graph)
        with open(self.prefix + "centrality.dat", "w") as report:
            print >> report, "Node\tNX\tPrince+olsrv1"
            for node, value in bcs.iteritems():
                print >> report, "%s\t%f\t%f" % (node, value, self.get_mean_column(self.prefix + node, 4))

        with open(self.prefix + "timers.dat", "w") as report:
            print >> report, "Node\tHello NX\tHello Prince\tTC NX\tTC Prince"
            for node in self.graph.nodes():
                print >> report, "%s\t%f\t%f\t%f\t%f" % (node, ctv.Hi[node], self.get_mean_column(self.prefix + "/" + node, 2), ctv.TCi[node], self.get_mean_column(self.prefix + "/" + node, 1))
        return

    def get_mean_column(self, nodename, column):
        with open(nodename + "_prince.log") as f:
            values = np.loadtxt(f)
            if values.shape[0] > 4:
                return np.mean(values[-5:, column])
        return 0

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



class princeOLSR(princeTest):
    def __init__(self, mininet, name, args):
        super(princeOLSR, self).__init__(mininet)
        self.duration = int(args["duration"])
        self.setPrefix(name)
        self.olsr_conf_template = """
        DebugLevel  1
        IpVersion 4
        FIBMetric "flat"
        LinkQualityFishEye  0
        LockFile "%s"
        Hna4{}
        Hna6{}

        #This plugin is bugged
        #LoadPlugin "../olsrd/lib/netjson/olsrd_netjson.so.1.1"{
        #    PlParam "accept" "0.0.0.0"
        #    PlParam "port" "2010"
        #}

        LoadPlugin "../olsrd/lib/txtinfo/olsrd_txtinfo.so.1.1"{
            PlParam "accept" "0.0.0.0"
            PlParam "port" "2008"
        }

        LoadPlugin "../olsrd/lib/jsoninfo/olsrd_jsoninfo.so.1.1"{
            PlParam "accept" "0.0.0.0"
            PlParam "port" "2009"
        }

        LoadPlugin "../olsrd/lib/poprouting/olsrd_poprouting.so.0.1"{
            PlParam "accept" "0.0.0.0"
            PlParam "port" "1234"
        }

        InterfaceDefaults {
            TcInterval 5.0
            TcValidityTime  500.0
            HelloInterval   2.0
            HelloValidityTime 20.0
        }

        Interface %s {}
        """

    def launchRouting(self, host):
        olsr_conf_file = self.prefix + host.name + "_olsr.conf"
        olsr_lock_file = "/var/run/" + host.name + str(time.time()) + ".lock"
        f_olsr = open(olsr_conf_file, "w")
        print >> f_olsr, self.olsr_conf_template % (olsr_lock_file, self.intf_list)
        f_olsr.close()
        args = "-f " + os.path.abspath(olsr_conf_file)
        cmd = "../olsrd/olsrd " + args
        log_str = "Host " + host.name + " launching command:\n"
        info(log_str)
        info(cmd + "\n")
        logfile = self.prefix + host.name + "_olsr.log"

        params = {}
        params['>'] = logfile
        params['2>'] = logfile

        return self.bgCmd(host, True, cmd,
                          *reduce(lambda x, y: x + y, params.items()))


class princeHeuristic(princeOLSR):
    def __init__(self, mininet, name, args):
        super(princeHeuristic, self).__init__(mininet, name, args)
        self.heuristic = 1
        self.weights = 1
        self.poprouting = 1
        self.dump = 1


class princeNoHeuristic(princeOLSR):
    def __init__(self, mininet, name, args):
        super(princeNoHeuristic, self).__init__(mininet, name, args)
        self.heuristic = 0
        self.weights = 0
        self.poprouting = 1
        self.dump = 1


class princeTimers(princeOLSR):
    def __init__(self, mininet, name, args):
        super(princeTimers, self).__init__(mininet, name, args)
        self.poprouting = 0
        self.dump = 1

    def analyzeResults(self):
        None

    def performTests(self):
        self.wait(30)
        timer = 5.0
        cmd = "echo \"/HelloTimer=%f\" | nc 127.0.0.1 1234" % (timer,)
        params = {}
        for idx, host in enumerate(self.getAllHosts()):
            logfile = self.prefix + host.name + "_netcat.log"
            params['>'] = logfile
            params['2>'] = logfile
            print "Setting hello timer to host %s to 10.00" % host
            self.bgCmd(host, True, cmd,
                       *reduce(lambda x, y: x + y, params.items()))


class princeOONF(princeTest):
    def __init__(self, mininet, name, args):
        super(princeOONF, self).__init__(mininet, duration)
        duration = int(args["duration"])
        self.setPrefix(name)
        self.olsr = 2
        self.olsr2_conf_template = """
        [global]
            plugin remotecontrol
            lockfile %s
            fork false
        [telnet]
            bindto  127.0.0.1
            port 2009

        [interface=lo]
        """

    def launchRouting(self, host):
        olsr_conf_file = self.prefix + host.name + "_olsr2.conf"
        olsr_lock_file = "/var/run/" + host.name + str(time.time()) + ".lock"
        f_olsr = open(olsr_conf_file, "w")
        print >> f_olsr, self.olsr2_conf_template % (olsr_lock_file)
        for inf in host.intfList():
            print >> f_olsr, "[interface=%s]\n" % (inf)
        f_olsr.close()
        args = "-l " + os.path.abspath(olsr_conf_file)
        cmd = "../OONF/build/olsrd2_static " + args

        log_str = "Host " + host.name + " launching command:\n"
        info(log_str)
        info(cmd + "\n")
        logfile = self.prefix + host.name + "_olsr2.log"

        params = {}
        params['>'] = logfile
        params['2>'] = logfile

        return self.bgCmd(host, True, cmd,
                          *reduce(lambda x, y: x + y, params.items()))



class crashPingTest(princeNoHeuristic):
    def __init__(self, mininet, name, args):
        super(crashPingTest, self).__init__(mininet, name, args)
        self.killwait = int(args["kill_wait"])
        self.kill = self.getHostSample(1)[0].defaultIntf().ip
        #self.destination = self.getHostSample(1)[0].defaultIntf().ip
        #self.stopNodeList = self.getCentrality()

    def performTests(self):
        self.wait(float(self.killwait))
        self.nodeCrashed = "h2_2"
        if self.nodeCrashed:
            print "Killing " + str(self.nodeCrashed) + "\n"
            self.sendSignal(signal.SIGKILL, hostName=[self.nodeCrashed])

    def launchPing(self, host):
        idps = randint(0, 100)
        logfile = self.prefix + host.name.split('_')[0] + \
            "-" + str(idps) + "_ping_$(date +%s).log"

        cmd = "ping " + self.destination
        params = {}
        params['>'] = logfile
        params['2>'] = logfile

        return self.bgCmd(host, True, cmd,
                          *reduce(lambda x, y: x + y, params.items()))

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
            comp = sorted(unsorted_comp, key=lambda x: -len(x))
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
        betw = [x for x in nx.betweenness_centrality(self.graph).items()
                if x[1] > 0 and node_centrality_posteriori[x[0]][0] > 0]

        return [node_centrality_posteriori[k[0]][1] for k in sorted(betw, key=lambda x: -x[1])]
