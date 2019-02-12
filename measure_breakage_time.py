#!/usr/bin/env python
import networkx as nx
import sys
from collections import defaultdict, Counter
import itertools as it
import glob
import simplejson as json
import copy
import os
import datetime


def mid(ip):
    octects = ip.split('.')
    midded_ip = "%s.%s.%s.%s" % (octects[0], octects[1], octects[2], 1)
    return midded_ip


class resultParser():

    def __init__(self):
        self.nodeSet = set()
        self.routing_tables = defaultdict(dict)  # node_id, timestamp, rt
        self.sorted_routing_tables = {}  # timestamp, node_id, rt
        self.dump_interval = 1
        self.latest_time = 0
        self.earliest_time = (2020-1970)*365*24*60*60*1000  # ms
        self.data_series = []
        self.precision = 1  # ds deciseconds
        self.id_ip = {}
        self.init_data()
        self.killed_node = ""

    def init_data(self):
        self.data = {'loops': 0, 'broken_paths': 0, 'correct_paths': 0,
                     'missing_dest': 0}

    def read_topologies_from_node(self, pathPrefix, limit_to=-1):
        """ load all the .json files with the logged routing tables """
        nodeSet = set()
        timeBasedRoute = {}
        helloTimers = []
        tcTimers = []
        dirs = os.listdir(pathPrefix)
        files = []
        for d in dirs:
            files += glob.glob(pathPrefix + d + "/*")

        print "will parse", len(files), "files"
        counter = 0
        now = int(datetime.datetime.now().strftime("%s"))
        for topoFile in files:
            counter += 1
            jsonRt = {}
            try:
                f = open(topoFile, "r")
                j = json.load(f)
                f.close()
            except Exception as e:
                #print "NOK", str(e)
                try:
                    f.close()
                except Exception:
                    pass
                continue
            timestamp = int(os.path.basename(topoFile))
            if timestamp < self.earliest_time:
                self.earliest_time = timestamp
            if timestamp > self.latest_time:
                self.latest_time = timestamp
            node_id = j["router_id"]
            rt = j["routes"]
            for route in rt:
                if route["destination"] == "0.0.0.0/0":
                    continue
                try:
                    jsonRt[route["destination"][:-3]] = mid(route["next"])
                except Exception:
                    print topoFile
                    raise
            node_i = "h%s_%s" %(node_id.split('.')[2], node_id.split('.')[2])
            self.id_ip[node_i] = node_id

            self.nodeSet.add(str(node_id))
            self.routing_tables[str(node_id)][timestamp] = jsonRt

    def reorder_logs(self):
        logWindow = {}
        orderedLogSequence = []
        alignedJsonRt = {}
        for i in range(0, self.latest_time - self.earliest_time + 1, self.precision):
            self.sorted_routing_tables[i+self.earliest_time] = {}
        time_list = self.sorted_routing_tables.keys()
        for node_id, rt_dict in self.routing_tables.items():
            ord_rt_dict = sorted(rt_dict.items(), key=lambda x: x[0])
            last_added = ord_rt_dict[0][0]
            for timestamp, rt in ord_rt_dict:
                for i in range(last_added + self.precision, timestamp, self.precision):
                    self.sorted_routing_tables[i] = self.sorted_routing_tables[last_added]
                self.sorted_routing_tables[timestamp][node_id] = dict(rt)
                last_added = timestamp

    def navigate_rt(self, s, d, timestamp, current_path=[]):
        if s == d:
            self.data['correct_paths'] += 1
            current_path.append(d)
            return current_path
        try:
            nh = self.sorted_routing_tables[timestamp][s][d]
        except KeyError:
            if s == self.id_ip[p.killed_node]:
                self.data['broken_paths'] += 1
            else:
                self.data['missing_dest'] +=1
            #print self.sorted_routing_tables[timestamp][s]
            print timestamp, s, d, current_path
            import pdb
            #pdb.set_trace()
            #code.interact(local=locals())
            return []
        if nh in current_path:
            self.data['loops'] += 1
            return []
        current_path.append(nh)
        return self.navigate_rt(nh, d, timestamp,
               current_path=current_path)

    def navigate_all_paths(self, timestamp):
        self.init_data()
        node_list = list(self.nodeSet)
        counter = 0
        for cc in self.cc_list:
            routes = it.permutations(cc, 2)
            for r in routes:
                counter += 1
                path = self.navigate_rt(r[0], r[1], timestamp,
                                     current_path=[r[0]])
        self.data_series.append([timestamp, self.data["correct_paths"],
                               self.data['loops'], self.data['broken_paths'],
                               self.data['missing_dest']])

    def navigate_all_timestamps(self, limit_to=-1):
        for t in self.sorted_routing_tables.keys()[:limit_to]:
            self.navigate_all_paths(t)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "This script parses dumps of routing tables, recomputes all the shortest paths"
        print "and finds the number and time of breakage of the network"
        print "usage: ./measure_breakage_time.py broken_node",\
                "path_prefix"
        print "path_prefix is the prefix of the routing table files generated"
        sys.exit(1)

    pathPrefix = sys.argv[1]
    p = resultParser()
    p.killed_node = sys.argv[2]
    p.cc_list = []
    p.read_topologies_from_node(pathPrefix+ "/rtables/")
    p.reorder_logs()
    graph = nx.read_adjlist(pathPrefix + "/topology.adj")
    if graph.nodes()[graph.nodes().index(p.killed_node)] in nx.articulation_points(graph):
        # verify against its BCC
        bccs = [bc for bc in nx.biconnected_components(graph) if p.killed_node in bc]
        for bcc in bccs:
            bcc.remove(p.killed_node)
        for bcc in bccs:
            p.cc_list.append(map(lambda x: p.id_ip[x], bcc))
    else:
        #Normal node
        graph.remove_node(p.killed_node)
        print(list(nx.connected_components(graph)))
        p.cc_list.append(map(lambda x:p.id_ip[x], graph.nodes()))
    p.navigate_all_timestamps()
    p.data_series.sort(key=lambda x: x[0])
    print "correct_paths, loops, broken_paths, missing_dest"
    for l in p.data_series:
        print ",".join(map(str, l))
