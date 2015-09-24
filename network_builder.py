import re
import sys
import networkx as nx

from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.node import OVSController
from mininet.cli import CLI
from mininet.log import info, error, debug, output
from mininet.node import CPULimitedHost
from mininet.link import TCLink

sys.path.append('community_networks_analysis')

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

    def getLinks(self):
        # returns the hosts couples representing the links
        links = []
        hosts = self.values()
        for h in hosts:
            intfs = h.intfList()
            for intf in intfs:
                if intf.link != None and intf.link not in links:
                    links.append(intf.link)
        return links

    def linkSentPackets(self,link):
        pstr1 = link.intf1.node.cmd("ifconfig ",link.intf1.name ,"| grep -Eo 'TX packets:[0-9]+' | cut -d':' -f 2")
        pstr2 = link.intf2.node.cmd("ifconfig ",link.intf2.name ,"| grep -Eo 'TX packets:[0-9]+' | cut -d':' -f 2")
	packets1 = int(pstr1.split("\n")[0])
	packets2 = int(pstr2.split("\n")[0])
        return packets1+packets2

    def linkSentBytes(self,link):
        pstr1 = link.intf1.node.cmd("ifconfig ",link.intf1.name ,"| grep -Eo 'TX bytes:[0-9]+' | cut -d':' -f 2")
        pstr2 = link.intf2.node.cmd("ifconfig ",link.intf2.name ,"| grep -Eo 'TX bytes:[0-9]+' | cut -d':' -f 2")
	bytes1 = int(pstr1.split("\n")[0].split(" ")[0])
	bytes2 = int(pstr2.split("\n")[0].split(" ")[0])
        return bytes2+bytes1

    def hostSentPackets(self,host):
        sent_packets = 0
        sent_bytes = 0
        intfs = host.intfNames()
        for intf in intfs:
            host.cmd("ifconfig",intf ,"| grep -Eo 'TX bytes:[0-9]+' | cut -d':' -f 2")
            sent_bytes += int(re.findall(r'\d+',host.cmd("ifconfig",intf ,"| grep -Eo 'TX bytes:[0-9]+' | cut -d':' -f 2"))[0])
            sent_packets += int(re.findall(r'\d+',host.cmd("ifconfig ",intf ,"| grep -Eo 'TX packets:[0-9]+' | cut -d':' -f 2"))[0])
        return (sent_packets,sent_bytes)

    def hostReceivedPackets(self,host):
        received_packets = 0
        received_bytes = 0
        intfs = host.intfNames()
        for intf in intfs:
            received_bytes += int(re.findall(r'\d+',host.cmd("ifconfig "+intf +" | grep -Eo 'RX bytes:[0-9]+' | cut -d':' -f 2"))[0])
            received_packets += int(re.findall(r'\d+',host.cmd("ifconfig "+intf +" | grep -Eo 'RX packets:[0-9]+' | cut -d':' -f 2"))[0])
        return (received_packets,received_bytes)
        
    def sentPackets(self):
        # if you experience assertion errors, you should
        # try to make sleep the mininet thread for a second
        sent_packets = 0
        sent_bytes = 0
        hosts = self.values()
        for h in hosts:
            p,b = self.hostSentPackets(h)
            sent_packets += p
            sent_bytes += b
        return (sent_packets,sent_bytes)

class GraphNet(PowerNet):
    def __init__(self, edges_file, draw=True, **params):
        if "link_opts" in params.keys():
            self.link_opts = params["link_opts"]
            del params["link_opts"]

        super(GraphNet, self).__init__(**params)
        info("\nReading "+edges_file+"\n")

        g = loadGraph(edges_file, connected=True)

        nodeCounter = 0
        nodeMap = {}
        # mininet bails if host names are longer than 10 chars
        max_name_len = 10 - len(str(len(g))) - 2
        for name in g.nodes():
            # remove unprintable chars from name
            nodeMap[name] = "h" + filter(str.isalnum, str(name))[-max_name_len:]\
                            + "_" + str(nodeCounter)
            nodeCounter += 1

        self.gg = nx.relabel_nodes(g, nodeMap)

        self.hosts_port = {}

        # add nodes
        for n in self.gg.nodes():
            self.addHost(n)
            self.hosts_port[n] = 1

        # add edges
        for e in self.gg.edges(data=True):
            quality_params = {}
            quality_params.update(self.link_opts)
            # allowed quality parameters bw, delay, jitter, delay_distribution
            if "loss" in quality_params.keys():
                if quality_params["loss"] == "wifi_loss":
                    quality_params["loss"] = \
                        100*((1-(1.0/(e[2]['weight'])))**7)
                else:
                    quality_params["loss"] = float(quality_params["loss"])
            # the number of retransmisison (4) derives from a parameter of the
            # 802.11 standard: dot11LongRetryLink (for Long Packets, are longer
            # than dot11RTSthreshold)
            quality_params["use_htb"] = True
            self.insertLink(self.get(e[0]), self.get(e[1]), quality_params)

        if draw:
            showGraph(self.gg)

    def pickHostAddrPort(self, node):
        port = self.hosts_port[node.name]
        addr = "10.0."+node.name.split('_')[-1]+"."+str(port)+"/8"
        self.hosts_port[node.name] += 1
        return addr, port

    def insertLink(self, n1, n2, quality_params={}):
        addr1, port1 = self.pickHostAddrPort(n1)
        addr2, port2 = self.pickHostAddrPort(n2)
        self.addLink(n1, n2,
                     port1=port1,
                     port2=port2,
                     params1=dict([('ip', addr1)] + quality_params.items()),
                     params2=dict([('ip', addr2)] + quality_params.items()))

    def setShortestRoutes(self):
        paths = nx.all_pairs_dijkstra_path(self.gg, weight='weight')
        for node1 in paths.keys():
            host1 = self.get(node1)
            debug("Starting node: "+node1+'\n')
            debug("\tpaths: "+str(paths[node1])+'\n')
            for node2 in paths[node1].keys():
                if node2 != node1:
                    if len(paths[node1][node2]) > 2:
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


