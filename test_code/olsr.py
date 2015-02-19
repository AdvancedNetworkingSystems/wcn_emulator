
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


    def save_config_file(self, host, args):
        return 

    def launch_ping(self, host,  args):

        cmd = "ping " + args

        log_str = "Host " + host.name + " lounching command:\n"
        info(log_str)
        info(cmd + "\n")
        logfile = self.prefix + host.name + "_ping.log"

        params = {}
        params['>'] = logfile
        params['2>'] = logfile


        return self.bgCmd(host, True, cmd,
            *reduce(lambda x, y: x + y, params.items()))


    def launch_OLSR(self, host,  args):

        cmd = "../olsrd-0.6.8/olsrd " + \
                args

        log_str = "Host " + host.name + " lounching command:\n"
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
        self.startRun()
        sleep(self.duration)
        self.killAll()

    #def runTest(self):

    #    info("*** Launching OLSR test\n")
    #    info("Data folder: "+self.prefix+"\n")

    #    
    #    if self.stop_all_nodes:
    #        if type(self.stop_all_nodes) == int:
    #            self.centList = self.getCentrality()[:self.stop_all_nodes]
    #        elif type(self.stop_all_nodes) == list:
    #            for idx in self.stop_all_nodes:
    #                self.centList.append(self.getCentrality()[idx])

    #    for runid in range(len(self.centList)):
    #        info("\nStarting run " + str(runid) + "\n")
    #        self.runId = str(runid)
    #        if self.stop_all_nodes:
    #            self.nodeCrashed = self.centList.pop(0)

    #        if not self.startRun():
    #            # some times process are not killed in time, UDP
    #            # ports are still occupied and the next run can not
    #            # start correctly. I kill everything, wait some time, try 
    #            # to restart. If something still goes wrong i stop the emulation
    #            self.killAll()
    #            time.sleep(10)
    #            info("\nWARNING: run_id " + str(runid) + " could not start, retrying...\n")
    #            if not self.startRun():
    #                error("\nERROR: run_id " + str(runid) + " could not start!" + \
    #                        "please check the logs\n")
    #                sys.exit(1)



    #        eventDict = {
    #                self.startLog:["Start logging", self.sendSignal,
    #                    {"sig":signal.SIGUSR1}],
    #                self.stopNode:["Stopping node(s) " + str(self.nodeCrashed) + " ",
    #                    self.sendSignal, {"sig":signal.SIGTSTP,
    #                    "hostName":self.nodeCrashed}],
    #                self.stopLog:["Stop logging", self.sendSignal,
    #                    {"sig":signal.SIGUSR1}]}

    #        eventList = []
    #        relativeTime = 0
    #        for e in sorted(eventDict.keys()):
    #            if e > 0:
    #                data = eventDict[e]
    #                eventList.append([e - relativeTime] + data)
    #                relativeTime += (e - relativeTime)

    #        waitTime = self.duration - relativeTime

    #        for event in eventList:
    #            sleep(event[0])
    #            print event
    #            event[2](**event[3])
    #            info(event[1] + str(time.time()) + "\n")
    #        sleep(waitTime)
    #        for pid in self.pendingProc.keys():
    #            self.sendSig(pid, signal.SIGTERM)
    #        time.sleep(2)
    #        # in case some process got stuck:
    #        self.killAll()
    #        time.sleep(2)
    #        #sendSignal(signal.SIGUSR2)
    #        #if self.startLog > 0:
    #        #    duration -= self.startLog
    #        #    sleep(self.startLog)
    #        #    print "XX", self.startLog, duration, time.time()
    #        #    # this is interpreted by the daemons as 
    #        #    # "start (or stop) logging"
    #        #    self.sendSignal(signal.SIGUSR1)
    #        #    info("\nStart logging now!\n") 
    #        #if self.stopNode > 0:
    #        #    crashTime = self.stopNode - self.startLog
    #        #    duration -= crashTime
    #        #    sleep(crashTime)
    #        #    print "XX", self.stopNode, duration, time.time()
    #        #    # this is interpreted as "crash"
    #        #    self.sendSignal(signal.SIGTSTP, self.nodeCrashed)
    #        #    info("\nSent crash signal to node " + str(self.nodeCrashed))
    #        #if self.stopLog > 0:
    #        #    stopTime = self.stopLog - (self.startLog + self.stopNode)
    #        #    duration -= stopTime
    #        #    print "XX", stopTime, duration, time.time()
    #        #    sleep(stopTime)
    #        #    self.sendSignal(signal.SIGUSR1)
    #        #    info("\nStop logging now!\n") 
    #        #print "XX", time.time(), duration
    #        #sleep(duration)
    #        ## this is interpreted by the daemons as 
    #        ## "restart a new run"
    #        #self.sendSignal(signal.SIGUSR2)




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
            info(str(intf))
            info(str([i.name for i in intf]))
            intf_list =  ' '.join(["\"" + i.name + "\""  for i in intf])
            olsr_conf_file = self.prefix + h.name + ".conf"
            olsr_lock_file =  "/var/run/" + h.name + ".log"
            f = open(olsr_conf_file, "w")
            print >> f, self.conf_file % (olsr_lock_file, intf_list)
            f.close()
            args = "-f " + os.path.abspath(olsr_conf_file)
            #CLI(self.mininet)
            if self.HelloInterval:
                args += " -hint " + str(self.HelloInterval)
            if self.TcInterval:
                args += " -tcint " + str(self.TcInterval)

            
            launch_pid = self.launch_OLSR(h, args)

            if self.dump:
                self.launch_sniffer(h)

        sleep(10)
        if len(host_list) > 1:
            for h in host_list:
                intf = h.intfList()
                while True:
                    d = self.get_random_destination() 
                    if d != intf[0].ip:
                        break
                self.launch_ping(h, d)


        if not self.nodeCrashed and rNode:
            self.nodeCrashed = [rNode]
        return launch_pid

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
        DebugLevel  6
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
        #LoadPlugin "olsrd_txtinfo.so.0.1"
        #
        #{
        #}


        InterfaceDefaults {
        }

        Interface %s
        {
        }
        """

        if "HelloInterval" in args.keys():
            self.HelloInterval = float(args["HelloInterval"])
        else:
            self.HelloInterval = 0

        if "TcInterval" in args.keys():
            self.TcInterval = float(args["TcInterval"])
        else:
            self.TcInterval = 0



