
import sys
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

    def launchPS(self,host,params,stdout,stderr):
        cmd = "./streamer"
        params.update(self.peer_opt_params)
        return self.bgCmd(host,True,cmd,*reduce(lambda x, y: x + y, params.items()) + ('>',stdout,'2>',stderr))

    def launchPeer(self,host,source):
        idps = randint(0,100)
        logfile = self.prefix+host.name.split('_')[0]+"-"+str(idps)+"_peerstreamer_normal_$(date +%s).log"
        params = {}
        params['-i'] = source.defaultIntf().ip
        params['-p'] = self.source_opt_params['-P'] 
        params['-P'] = str(randint(4000,8000))
        return self.launchPS(host,params,'/dev/null',logfile)

    def launchSource(self,host):
        idps = randint(0,100)
        logfile = self.prefix+host.name.split('_')[0]+"-"+str(idps)+"_source_normal_$(date +%s).log"
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

class PSXLOptimization(PSRandomTest):
    def __init__(self, mininet, name, args):
        super(PSXLOptimization,self).__init__(mininet,name,args)

    def runTest(self):
        sent_packets,sent_bytes = self.net.sentPackets()
        print "sent_packets: "+str(sent_packets)
        super(PSXLOptimization,self).runTest()
        sent_packets,sent_bytes = self.net.sentPackets()
        print "sent_packets: "+str(sent_packets)



