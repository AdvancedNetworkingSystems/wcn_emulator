#!/bin/python
import sys
sys.path.append('community_networks_analysis')

from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.node import OVSController
from mininet.cli import CLI
from mininet.log import info, error, debug, output
from mininet.node import CPULimitedHost
from mininet.link import TCLink

import networkx as nx
from time import sleep, time
from os import kill, path, makedirs
from psutil import Process
import signal
from matplotlib.pyplot import ion
from random import sample

from gengraphs import loadGraph
from misclibs import showGraph

class PowerNet(Mininet):
    def __init__(self,**params):
        if 'controller' not in params.keys():
            params['controller'] = OVSController
        if 'host' not in params.keys():
            params['host'] = CPULimitedHost
        if 'link' not in params.keys():
            params['link'] = TCLink
        super(PowerNet,self).__init__(**params)

    def enableForwarding(self):
        for node in self.values():
            node.cmd("echo 1 > /proc/sys/net/ipv4/ip_forward")

    def setNeighboursRoutes(self):
        for node in self.values():
            for intf in node.intfList():
                if intf.link:
                    rintf = self.remoteIntf(intf)
                    raddrs = self.getNodeAddrs(rintf.node)
                    for addr in raddrs:
                        node.setHostRoute(addr,intf.name)

    def getNodeAddrs(self,node):
        r = []
        for intf in node.intfList():
            if intf.link:
                r.append(intf.ip)
        return r

    def remoteIntf(self,intf):
        if intf.link:
            intfs = [ intf.link.intf1, intf.link.intf2 ]
            intfs.remove(intf)
            return intfs[0]
        return None


class GraphNet(PowerNet):
    def __init__(self,edges_file,draw=True,**params):
        super(GraphNet,self).__init__(**params)
        info("\nReading "+edges_file+"\n")

        g = loadGraph(edges_file, connected=True)

        nodeCounter = 0
        nodeMap = {}
        for name in g.nodes():
            nodeMap[name] = "h"+str(name)+"_"+str(nodeCounter)
            nodeCounter += 1

        self.gg = nx.relabel_nodes(g,nodeMap)

        self.hosts_port = {}

        # add nodes
        for n in self.gg.nodes():
            self.addHost(n)
            self.hosts_port[n] = 1 

        # add edges
        for e in self.gg.edges(data=True):
            # 10 Mbps, 5ms delay, 10% loss, 1000 packet queue
            # htp: Hierarchical Token Bucket rate limiter
#            quality_params = {"bw":10,"delay":'5ms', "loss":100-100.0/e[2]['weight'], "use_htb":True}
            quality_params = {}
#            quality_params["bw"] = 10
#            quality_params["delay"] = '5ms'
#            quality_params["loss"] = 100-100.0/e[2]['weight']
#            quality_params["use_htb"] = True
            self.insertLink(self.get(e[0]),self.get(e[1]),quality_params)

        if draw:
            ion()
            showGraph(self.gg)

    def pickHostAddrPort(self,node):
        port = self.hosts_port[node.name]
        addr = "10.0."+node.name.split('_')[-1]+"."+str(port)+"/8"
        self.hosts_port[node.name] += 1
        return addr,port

    def insertLink(self,n1,n2,quality_params={}):
        addr1, port1 = self.pickHostAddrPort(n1)
        addr2, port2 = self.pickHostAddrPort(n2)

        self.addLink(n1,n2,  \
                port1 = port1, \
                port2 = port2, \
                params1=dict([('ip',addr1)] + quality_params.items()), \
                params2=dict([('ip',addr2)] + quality_params.items()) \
                )

    def setShortestRoutes(self):
        paths = nx.shortest_path(self.gg,weight='weight')
        for node1 in paths.keys():
            host1 = self.get(node1)
            debug("Starting node: "+node1+'\n')
            debug("\tpaths: "+str(paths[node1])+'\n')
            for node2 in paths[node1].keys():
                if node2 != node1 :
                    if len(paths[node1][node2])>2:
                        debug("\tDestination node: "+node2+'\n')
                        nextHop = self.get(paths[node1][node2][1])
                        debug("\tNextHop node: "+nextHop.name+'\n')
                        dsts = self.getNodeAddrs(self.get(node2))
                        intfs = host1.connectionsTo(nextHop)
                        nextAddrs = [ couple[1].ip for couple in intfs ]
                        rintf = intfs[0][0] # WARNING we just consider one link
                        for dst in dsts:
                            for addr in nextAddrs:
                                host1.cmd("ip route add "+dst+" via "+addr+" dev "+rintf.name)
                                debug("\tip route add "+dst+" via "+addr+'\n')
                    else :
                        host2 = self.get(node2)
                        intfs = [ couple[0] for couple in host1.connectionsTo(host2) ]
                        rintf = intfs[0] # WARNING we just consider one link
                        raddrs = self.getNodeAddrs(host2)
                        for addr in raddrs:
                            host1.setHostRoute(addr,rintf.name)


class MininetTest(object):
    def __init__(self,mininet):
        self.net = mininet
        self.pendingProc = {} 
    
    def getHostSample(self,num):
        hosts = sample(self.net.values(),num)
        return hosts[:num]

    def bgCmd(self,host,*args):
        # here it's a little workaround for tracing the resulting pid
        # it launch the new process using the mininet interface
        # but it check the newly created process id using psutil
        host_proc = Process(host.pid)
        host_ps = set(host_proc.get_children())
        host.sendCmd(*(args+("&",)))
        sleep(0.5)
        pid = (set(host_proc.get_children()).difference(host_ps)).pop().pid
        info("BGProcess: "+str(pid)+"; ")
        self.pendingProc[pid] = host
        return pid

    def sendSig(self,pid,sig=signal.SIGTERM):
        try:
            info("Killing BGProcess: "+str(pid)+"; ")
            kill( pid, sig )
        except OSError:
            error("Error while killing process "+str(pid))
            pass

    def killAll(self):
        for pid in self.pendingProc.keys():
            self.sendSig(pid,signal.SIGKILL)
            self.pendingProc[pid].monitor() # wait exiting
        self.pendingProc.clear()

class PSTest(MininetTest):
    def __init__(self,mininet,duration=300):
        super(PSTest,self).__init__(mininet)
        self.source = None
        self.hosts = []
        self.duration = duration
        self.prefix = ''

    def setPrefix(self,name):
        self.prefix = str(name)+'_'+str(self.duration)+'_'+str(len(self.hosts)+1)+'hosts/' 
        if not path.exists(self.prefix):
                makedirs(self.prefix)

    def launchPS(self,host,params):
        cmd = "./streamer"
        self.bgCmd(host,cmd,*reduce(lambda x, y: x + y, params.items()))

    def launchPeer(self,host,source,source_port=7000):
        logfile = self.prefix+host.name.split('_')[0]+"_peerstreamer_normal_$(date +%s).log"
        params = {}
        params['-i'] = source.defaultIntf().ip
        params['-p'] = str(source_port)
        params['-c'] = '38'
        params['--chunk_log'] = ''
        params['>'] = '/dev/null'
        params['2>'] = logfile
        self.launchPS(host,params)

    def launchSource(self,host,chunk_mult=1,source_port=7000):
        video_file = "bunny.ts,loop=1"
        logfile = self.prefix+host.name.split('_')[0]+"_source_normal_$(date +%s).log"
        params = {}
        params['-I'] = host.defaultIntf().name
        params['-P'] = str(source_port)
        params['-m'] = str(chunk_mult)
        params['-f'] = video_file
        params['-c'] = '38'
        params['--chunk_log'] = ''
        params['>'] = '/dev/null'
        params['2>'] = logfile
        self.launchPS(host,params)

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
    def __init__(self,mininet,source_name,peer_names,duration=300,name=None):
        super(PSHostsTest,self).__init__(mininet,duration=duration)
        self.source = mininet.get(source_name)
        for n in peer_names:
            self.hosts.append(mininet.get(n))
        self.setPrefix(name)

class PSRandomTest(PSTest):
    def __init__(self,mininet,duration=300,num_peers=5,name=None):
        super(PSRandomTest,self).__init__(mininet,duration)
        self.hosts = self.getHostSample(num_peers)
        if len(self.hosts) > 0:
            self.source = self.hosts.pop()
        self.setPrefix(name)

if __name__ == '__main__':
    setLogLevel('info')
    net = GraphNet("LeoNets/FFGraz0.edges",draw=True)
    net.start()
    net.enableForwarding()
    net.setShortestRoutes()
    test_name = "FFGRAZ0_parameterless_"+str(int(time()))
    for i in range(1):
        info( "+++++++ Round: "+str(i+1) + '\n')
        #test = PSTest(net,duration=600,name=test_name,num_peers=(10-i))
        test = PSHostsTest(net,'h46_46',['h121_121','h28_28'],duration=30,name=test_name)
        test.runTest()
      #  sleep(60)
    net.stop()
