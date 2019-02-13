#!/usr/bin/env python
import networkx as nx
import math
import json
from GraphParser import GraphParser
from collections import OrderedDict
import random


def composeNetJson(graph, weight=None):
        """ Parameters
        graph: nx graph object
        """
        Netjson = OrderedDict()
        Netjson['type'] = 'NetworkGraph'
        Netjson['protocol'] = 'olsrv2'
        Netjson['version'] = 'poprouting custom'
        Netjson['revision'] = '0.11.3'
        Netjson['metric'] = 'ff_dat_metric'
        node = random.sample(graph.nodes(), 1)[0]
        Netjson['router_id'] = graph.nodes()[node]
        Netjson['nodes'] = []
        for node in graph.nodes():
            n = {}
            n['id'] = str(node)
            Netjson['nodes'].append(n)

        Netjson['links'] = []
        for link in graph.edges(data=True):
            e = {}
            e['source'] = str(link[0])
            e['target'] = str(link[1])
            if weight:
                e['cost'] = link[2][weight]
            else:
                e['cost'] = 1
            Netjson['links'].append(e)
        return Netjson


class ComputeTheoreticalValues():

    def __init__(self, graph, weight=None, cent="B", cH=2.0, cTC=5.0):
        self.G = graph
        self.cent = cent
        self.cH = cH
        self.cTC = cTC
        self.deg_dict = {}
        self.decimal_values = 3
        self.node_list = filter(lambda x: self.G.degree()[x] > 0, self.G)
        if cent == "B":
            self.bet_dict = nx.betweenness_centrality(self.G, weight=weight, endpoints=True)
            for n in self.node_list:
                self.deg_dict[n] = self.G.degree()[n]
        elif cent == "B_Pen":
            self.bet_dict = GraphParser(json.dumps(composeNetJson(self.G)), True, True, True)
            for n in self.node_list:
                self.deg_dict[n] = self.G.degree()[n]
        self.bet_ordered_nodes = [i[0] for i in sorted(
            self.bet_dict.items(), key=lambda x: x[1])]

        self.R = len(self.G.edges())
        self.compute_constants()
        self.compute_timers()

    def compute_constants(self):
        # self.lambda_H, self.lambda_TC, self.O_H, self.O_TC = \
        self.O_H = sum([self.deg_dict[l] for l in self.node_list]) / self.cH
        self.O_TC = len(self.node_list) * self.R / self.cTC
        sqrt_sum = 0
        for node in self.node_list:
            sqrt_sum += math.sqrt(self.deg_dict[node] * self.bet_dict[node])
        self.sq_lambda_H = sqrt_sum / self.O_H
        sqrt_sum = 0
        for node in self.node_list:
            sqrt_sum += math.sqrt(self.R * self.bet_dict[node])
        self.sq_lambda_TC = sqrt_sum / self.O_TC

    def get_graph_size(self):
        return len(self.G.nodes())

    def compute_timers(self):
        self.Hi = {}
        self.TCi = {}
        for node in self.node_list:
            # print str(node) + "  " + str(self.bet_dict[node])
            self.Hi[node] = \
                math.sqrt(self.deg_dict[node] / self.bet_dict[node]) * self.sq_lambda_H
            self.TCi[node] = \
                math.sqrt(self.R / self.bet_dict[node]) * self.sq_lambda_TC
