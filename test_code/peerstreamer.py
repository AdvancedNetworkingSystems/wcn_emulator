
import sys
sys.path.append('../')
from network_builder import *
from os import kill, path, makedirs
from matplotlib.pyplot import ion
from random import sample, randint

from test_generic import *

class PSTest(MininetTest):
    def __init__(self, mininet, duration=300):
        super(PSTest,self).__init__(mininet, path, duration)
        self.source = None
        self.hosts = []


    def launchPS(self,host,params,stdout,stderr):
        cmd = "./streamer"
        params['-c'] = '38'
#        params['-M'] = '5'
#        params['-O'] = '3'
        params['--chunk_log'] = ''
        params['>'] = stdout
        params['2>'] = stderr
        return self.bgCmd(host,True,cmd,*reduce(lambda x, y: x + y, params.items()))

    def launchPeer(self,host,source,source_port=7000):
        idps = randint(0,100)
        logfile = self.prefix+host.name.split('_')[0]+"-"+str(idps)+"_peerstreamer_normal_$(date +%s).log"
        params = {}
        params['-i'] = source.defaultIntf().ip
        params['-p'] = str(source_port)
        params['-P'] = str(randint(4000,8000))
        return self.launchPS(host,params,'/dev/null',logfile)

    def launchSource(self,host,chunk_mult=1,source_port=7000):
        idps = randint(0,100)
        video_file = "bunny.ts,loop=1"
        logfile = self.prefix+host.name.split('_')[0]+"-"+str(idps)+"_source_normal_$(date +%s).log"
        params = {}
        params['-I'] = host.defaultIntf().name
        params['-P'] = str(source_port)
        params['-f'] = video_file
        params['-m'] = str(chunk_mult)
        return self.launchPS(host,params,'/dev/null',logfile)

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
        duration = int(args["duration"])
        super(PSHostsTest, self).__init__(mininet, duration = duration)
        self.source = mininet.get(source_name)
        for n in peer_names.split():
            self.hosts.append(mininet.get(n))
        self.setPrefix(name)

class PSRandomTest(PSTest):
    def __init__(self, mininet, name, args):
        num_peers = int(args["num_peers"])
        duration = int(args["duration"])
        super(PSRandomTest,self).__init__(mininet,duration)
        self.hosts = self.getHostSample(num_peers)
        if len(self.hosts) > 0:
            self.source = self.hosts.pop()
        self.setPrefix(name)

class PSXLOptimization(PSRandomTest):
    def __init__(self, mininet, name, args):
        super(PSXLOptimization,self).__init__(mininet,name,args)
        sleep(1) 
        sent_packets,sent_bytes = self.generatedPackets()
        print "sent_packets: "+str(sent_packets)
        self.net.ping(self.getHostSample(2))
        sleep(1) 
        sent_packets,sent_bytes = self.generatedPackets()
        print "sent_packets: "+str(sent_packets)



