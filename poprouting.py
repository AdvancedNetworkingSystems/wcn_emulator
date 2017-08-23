#!/usr/bin/env python
import networkx as nx
import math


class ComputeTheoreticalValues():

    def __init__(self, graph, cent="B", cH=2.0, cTC=5.0):
        self.G = graph
        self.cent = cent
        self.cH = cH
        self.cTC = cTC
        self.decimal_values = 3
        if cent == "B":
            self.bet_dict = nx.betweenness_centrality(self.G, endpoints=True)
            self.bet_ordered_nodes = [i[0] for i in sorted(
                self.bet_dict.items(), key=lambda x: x[1])]
        elif cent == "C":
            self.bet_dict = nx.betweenness_centrality(self.G, endpoints=True)
            self.bet_ordered_nodes = [i[0] for i in sorted(
                self.bet_dict.items(), key=lambda x: x[1])]
            self.cent_dict = nx.closeness_centrality(self.G)
            self.cent_ordered_nodes = [i[0] for i in sorted(
                self.cent_dict.items(), key=lambda x: x[1])]
        self.deg_dict = self.G.degree()
        self.node_list = filter(lambda x: self.deg_dict[x] > 0, self.G)
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
