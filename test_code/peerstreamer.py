import sys
import numpy as np
sys.path.append('../')
from network_builder import *
from os import kill, path, makedirs
from matplotlib.pyplot import ion
from random import sample, randint

from test_generic import *

class PSTest(MininetTest):
    def __init__(self, mininet, conf_args):
        if "duration" in conf_args:
            duration = int(conf_args["duration"])
        super(PSTest,self).__init__(mininet, path, duration)
        self.source = None
        self.hosts = []
        self.peer_opt_params = {}
        self.source_opt_params = {}
        self.set_opt_params(conf_args)
        self.test_label = "normal"

    def setTestLabel(self,s):
        self.test_label = s

    def launchPS(self,host,params,stdout,stderr):
        cmd = "./streamer"
        params.update(self.peer_opt_params)
        return self.bgCmd(host,True,cmd,*reduce(lambda x, y: x + y, params.items()) + ('>',stdout,'2>',stderr))

    def launchPeer(self,host,source):
        idps = randint(0,100)
        logfile = self.prefix+host.name.split('_')[0]+"-"+str(idps)+"_peerstreamer_"+self.test_label+"_$(date +%s).log"
        params = {}
        params['-i'] = source.defaultIntf().ip
        params['-I'] = host.defaultIntf().name
        params['-p'] = self.source_opt_params['-P'] 
        params['-P'] = str(randint(4000,8000))
        return self.launchPS(host,params,'/dev/null',logfile)

    def launchSource(self,host):
        idps = randint(0,100)
        logfile = self.prefix+host.name.split('_')[0]+"-"+str(idps)+"_source_"+self.test_label+"_$(date +%s).log"
        params = {}
        params['-I'] = host.defaultIntf().name
        params.update(self.source_opt_params)
        return self.launchPS(host,params,'/dev/null',logfile)

    def set_opt_params(self,conf_args):
        self.source_opt_params['-f'] = "bunny.ts,loop=1"
        if "aframe_per_chunk" in conf_args:
            self.source_opt_params['-f'] += ",aframe=" + conf_args["aframe_per_chunk"]
        if "source_chunk_multiplicity" in conf_args:
            self.source_opt_params['-m'] = conf_args["source_chunk_multiplicity"]
        if "source_port" in conf_args:
            self.source_opt_params['-P'] = conf_args["source_port"]
        else:
            self.source_opt_params['-P'] = str(7000)
        if "push_strategy" in conf_args:
            if conf_args["push_strategy"] != "0":
                self.peer_opt_params['--push_strategy'] = "" 


        if "chunks_per_second" in conf_args:
            self.peer_opt_params['-c'] = conf_args["chunks_per_second"]
        if "neigh_size" in conf_args:
            self.peer_opt_params['-M'] = conf_args["neigh_size"]
        if "chunks_per_offer" in conf_args:
            self.peer_opt_params['-O'] = conf_args["chunks_per_offer"]
        if "log_chunks" in conf_args:
            if conf_args["log_chunks"] != "0":
                self.peer_opt_params['--chunk_log'] = "" 
        if "log_signals" in conf_args:
            if conf_args["log_signals"] != "0":
                self.peer_opt_params['--signal_log'] = "" 
        if "xloptimization" in conf_args:
            if conf_args["xloptimization"] != "":
                self.peer_opt_params['--xloptimization'] =  conf_args["xloptimization"] 


    def runTest(self):
        info("*** Launching PeerStreamer test\n")
        info("Data folder: "+self.prefix+"\n")
        if self.source:
            self.launchSource(self.source)

        for h in self.hosts:
            self.launchPeer(h,self.source)
        info("Waiting completion...\n")
        sleep(self.duration)

        self.killAll()

class PSHostsTest(PSTest):
    def __init__(self, mininet, name, args):
        source_name = args["source_name"]
        peer_names = args["peer_names"]
        super(PSHostsTest, self).__init__(mininet, args)
        self.source = mininet.get(source_name)
        for n in peer_names.split():
            self.hosts.append(mininet.get(n))
        self.setPrefix(name)

class PSRandomTest(PSTest):
    def __init__(self, mininet, name, args):
        num_peers = int(args["num_peers"])
        super(PSRandomTest,self).__init__(mininet,args)
        self.hosts = self.getHostSample(num_peers)
        if len(self.hosts) > 0:
            self.source = self.hosts.pop()
        self.setPrefix(name)

class PSXLOptimizationTest(PSRandomTest):
    def __init__(self, mininet, name, args):
        super(PSXLOptimizationTest,self).__init__(mininet,name,args)
        self.paths_file = "shortest.paths"
        self.dumpShortestPaths()
        self.resetNetStatistics()

    def dumpShortestPaths(self):
        assert(self.net.gg)
        sp = open(self.paths_file,'w')
        paths = nx.shortest_path(self.net.gg)
        nodes = paths.keys()
        while len(nodes):
            node1 = nodes.pop()
            for node2 in nodes:
                path = paths[node1][node2]
                for n in path:
                    h = self.net.get(n)
                    sp.write(h.defaultIntf().ip)
                    if n != path[len(path)-1]:
                        sp.write(",")
                    else:
                        sp.write("\n")
        sp.close()
        
    def resetNetStatistics(self):
        self.sent_packets, self.sent_bytes = self.net.sentPackets() # base value
        self.links = {}
        for l in self.net.getLinks():
          self.links[l] = self.net.linkSentPackets(l) # base value

    def networkImpact(self):
        linkos = {}
        linkos.update(self.links)
        for l in linkos.keys():
            linkos[l] = self.net.linkSentPackets(l) - self.links[l]
        return np.linalg.norm(linkos.values(),2)

    def sentPackets(self):
        sp,sb = self.net.sentPackets() 
        return sp - self.sent_packets

    def runTest(self):
        if '--xloptimization' in self.peer_opt_params.keys():
            self.peer_opt_params.pop('--xloptimization')
        print "sent_packets: "+str(self.sentPackets())
        print "network impact: "+str(self.networkImpact())

        self.setTestLabel("normal")
        super(PSXLOptimizationTest,self).runTest()
        self.norm_res = (self.sentPackets(), self.networkImpact())

        if '--xloptimization' not in self.peer_opt_params.keys():
            self.peer_opt_params['--xloptimization'] = self.paths_file
        self.resetNetStatistics()
        self.setTestLabel("optimized")
        super(PSXLOptimizationTest,self).runTest()
        self.optim_res = (self.sentPackets(), self.networkImpact())

        print "Normal case: " + str(self.norm_res)
        print "Optimized case: " + str(self.optim_res)

class PSXLOptimizationNTest(PSXLOptimizationTest):
    def __init__(self, mininet, name, args):
        super(PSXLOptimizationNTest,self).__init__(mininet,name,args)
        self.min_nodes = int(args["min_nodes_num"])
        self.max_nodes = int(args["max_nodes_num"])
        self.nodes_inc = int(args["nodes_num_inc"])

    def setTestLabel(self,s):
        self.test_label = s + "_"+str(len(self.hosts)+1)+"peers"

    def runTest(self):
        fp = open(self.prefix+"NTestResults.csv",'w')
        for n in range(self.min_nodes,self.max_nodes,self.nodes_inc):
            self.hosts = self.getHostSample(n)
            self.source = self.hosts.pop()
            super(PSXLOptimizationNTest,self).runTest()
            fp.write(str(n)+",")
            fp.write(str(self.norm_res[0])+","+str(self.norm_res[1])+",")
            fp.write(str(self.optim_res[0])+","+str(self.optim_res[1])+"\n")
        fp.close()

class PSXLOptimizationNeighTest(PSXLOptimizationTest):
    def __init__(self, mininet, name, args):
        super(PSXLOptimizationNeighTest,self).__init__(mininet,name,args)
        self.min_neigh = int(args["min_neigh_num"])
        self.max_neigh = int(args["max_neigh_num"])
        self.neigh_inc = int(args["neigh_num_inc"])

    def setTestLabel(self,s):
        self.test_label = s + "_"+str(len(self.hosts)+1)+"neigh"

    def runTest(self):
        fp = open(self.prefix+"NeighTestResults.csv",'w')
        for n in range(self.min_neigh,self.max_neigh,self.neigh_inc):
            super(PSXLOptimizationNeighTest,self).runTest()
            fp.write(str(n)+",")
            fp.write(str(self.norm_res[0])+","+str(self.norm_res[1])+",")
            fp.write(str(self.optim_res[0])+","+str(self.optim_res[1])+"\n")
        fp.close()
