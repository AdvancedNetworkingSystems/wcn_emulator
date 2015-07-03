
import sys
sys.path.append('../')
from network_builder import *
import random
import time
from dummyrouting import dummyRoutingRandomTest

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

        if self.stopAllNodes:
            if type(self.stopAllNodes) == int:
                self.centList = self.getCentrality()[:self.stopAllNodes]
            elif type(self.stopAllNodes) == list:
                for idx in self.stopAllNodes:
                    self.centList.append(self.getCentrality()[idx])

        for run_id in range(len(self.centList)):
            info("\nStarting run " + str(run_id) + "\n")
            if self.stopAllNodes:
                self.nodeCrashed = self.centList.pop(0)

            if not self.startRun():
                # some times process are not killed in time, UDP
                # ports are still occupied and the next run can not
                # start correctly. I kill everything, wait some time, try
                # to restart. If something still goes wrong i stop
                # the emulation

                self.killAll()
                time.sleep(10)
                info("\nWARNING: run_id " + str(run_id) +
                     " could not start, retrying...\n")
                if not self.startRun():
                    error("\nERROR: run_id " + str(run_id) +
                          " could not start!" +
                          "please check the logs\n")
                    sys.exit(1)

            eventDict = {
                self.startLog: ["Start logging \n", self.start_ping,
                                {"exclude": self.nodeCrashed, "run_id": run_id}
                                ],
                self.stopLog: ["Stopping logging ",
                               self.sendSignal, {"sig": signal.SIGINT}
                               ],
                self.stopNode: ["Stopping node(s) " + str(self.nodeCrashed) +
                                "\n", self.sendSignal,
                                {"sig": signal.SIGTERM,
                                 "hostName": self.nodeCrashed}
                                ]
            }
            eventDict = {}

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

    def get_centrality(self):
        o = OptimizeGraphChoice()
        return o.get_emulation_runs_per_topology(self.graph)

    def startRun(self):

        rNode = ""
        host_list = self.getAllHosts()

        if rNode:
            info("\nChosen node " + str(rNode) + " to fail\n")

        for h in host_list:
            intf = h.intfList()
            intf_list = ' '.join(["\"" + i.name + "\"" for i in intf])
            olsr_conf_file = self.prefix + h.name + ".conf"
            olsr_lock_file = "/var/run/" + h.name + ".log"
            f = open(olsr_conf_file, "w")
            print >> f, self.conf_file % (olsr_lock_file, intf_list)
            f.close()
            args = "-f " + os.path.abspath(olsr_conf_file)
            # CLI(self.mininet)
            if self.HelloInterval:
                args += " -hint " + str(self.HelloInterval)
            if self.TcInterval:
                args += " -tcint " + str(self.TcInterval)

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
                self.sendSig(pid, sig)

    def __init__(self, mininet, name, args):

        super(OLSRTest, self).__init__(mininet, name, args)

        self.mininet = mininet
        self.centList = []

        self.conf_file = """
        #DebugLevel  1
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
        LoadPlugin "../olsrd/lib/dumprt/olsrd_dumprt.so.0.0"{}

        InterfaceDefaults {
        }

        Interface %s
        {
        }
        """

        if "NumPing" in args.keys():
            self.NumPing = int(args["NumPing"])
        else:
            self.NumPing = 1

        if "HelloInterval" in args.keys():
            self.HelloInterval = float(args["HelloInterval"])
        else:
            self.HelloInterval = 0

        if "TcInterval" in args.keys():
            self.TcInterval = float(args["TcInterval"])
        else:
            self.TcInterval = 0


