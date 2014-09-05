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
from matplotlib.pyplot import ion
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
            quality_params = {"bw":10,"delay":'5ms', "loss":100-100.0/e[2]['weight'], "max_queue_size":1000, "use_htb":True}
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
        self.setNeighboursRoutes()
        paths = nx.shortest_path(self.gg,weight='weight')
        for node1 in paths.keys():
            debug("Starting node: "+node1+'\n')
            debug("\tpaths: "+str(paths[node1])+'\n')
            for node2 in paths[node1].keys():
                if node2 != node1 and len(paths[node1][node2])>2:
                    debug("\tDestination node: "+node2+'\n')
                    nextHop = self.get(paths[node1][node2][1])
                    debug("\tNextHop node: "+nextHop.name+'\n')
                    dsts = self.getNodeAddrs(self.get(node2))
                    intfs = self.get(node1).connectionsTo(nextHop)
                    nextAddrs = [ couple[1].ip for couple in intfs ]
                    for dst in dsts:
                        for addr in nextAddrs:
                            self.get(node1).cmd("ip route add "+dst+" via "+addr)
                            debug("\tip route add "+dst+" via "+addr+'\n')
                

if __name__ == '__main__':
    setLogLevel('info')
    net = GraphNet("test.edges")
    net.start()
    net.enableForwarding()
    net.setShortestRoutes()
    CLI(net)
    net.stop()

#    setLogLevel('info')
#    topo = TopoFactory("minitest.edges")
#    net = Mininet(topo,controller = OVSController,host=CPULimitedHost, link=TCLink)
#    net.start()
#    CLI(net)
#    net.stop()
