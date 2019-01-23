import math
import networkx as nx
import code
import sys
from collections import defaultdict
from pprint import pprint
#import MyUtil as myu
import operator
from collections import deque
from poprouting import ComputeTheoreticalValues
import matplotlib.pyplot as plt
import numpy as np

class TheoricValues():
    def __init__(self, NXgraph, weight=None, normPartCentr=None, cH=1.0, cTC=2.5):
        self.weight = weight
        self.decimal_values = 3
        self.G = NXgraph
        self.cH = cH
        self.cTC = cTC
        self.R = len(self.G.edges())
        self.deg_dict = self.G.degree()
        self.compute_overhead()
        self.bcc = list(nx.biconnected_components(self.G))
        self.pathsCounts = self.countPathsThroughNodes()
        self.artPoints = list(nx.articulation_points(self.G))
        self.CTV_P = ComputeTheoreticalValues(self.G, cent="B_Pen", cH=self.cH, cTC=self.cTC)
        #code.interact(local=dict(globals(), **locals()))
        

    def get_bc(self, node):
        return [bc for bc in self.bcc if node in bc]

    def countPathsThroughNodes(self):
        routesCount = defaultdict(int)
        paths = dict(nx.all_pairs_bellman_ford_path(self.G, weight=self.weight))
        for s in self.G.nodes():
            for bc in self.get_bc(s):
                for t in bc:
                    if s == t:
                        continue
                    for n in paths[s][t][1:-1]:
                        routesCount[n] += 1  
        return routesCount

    def compute_overhead(self):
        self.O_H = sum([self.deg_dict[l] for l in self.G.nodes()])/self.cH

    def compute_timers(self, how="NOpop"):
        self.Hi = {}
        self.TCi = {}
        # Assegna il default timer a tutti
        if how == "NOpop":
            self.CTV = ComputeTheoreticalValues(self.G, cent="B", weight=self.weight, cH=self.cH, cTC=self.cTC)
            for node in self.G.nodes():
                self.Hi[node] = self.cH
                self.TCi[node] = self.cTC
        elif how == "POP":
            self.CTV = ComputeTheoreticalValues(self.G, cent="B", weight=self.weight, cH=self.cH, cTC=self.cTC)
            self.Hi = self.CTV.Hi
            self.TCi = self.CTV.TCi
        elif how == "POPPEN":
            self.CTV = ComputeTheoreticalValues(self.G, cent="B_Pen", weight=self.weight, cH=self.cH, cTC=self.cTC)
            self.Hi = self.CTV.Hi
            self.TCi = self.CTV.TCi
        self.plot_timers(how)
        #self.print_timers()
        assert len(self.Hi) == len(self.G.nodes())
        return dict(self.Hi)

    def print_timers(self):
        print("H:", [h for h in sorted(self.Hi.items(), key=lambda x:x[0])])
        print("TC:", [h for h in sorted(self.TCi.items(), key=lambda x:x[0])])
        
    def plot_timers(self, how):
        fig, ax1 = plt.subplots()
        plt.title(how)
        timer_cent = []
        for t in self.artPoints:
            timer_cent.append((t, self.Hi[t], self.CTV.bet_dict[t], self.pathsCounts[t] * self.Hi[t], self.pathsCounts[t]))
        sorted_t_1 = [h for h in sorted(timer_cent, key=lambda x:x[2])]
        ax1.plot(zip(*sorted_t_1)[1], color='red')
        ax11 = ax1.twinx()
        ax11.plot(zip(*sorted_t_1)[2], color='blue')
        ax11.set_ylabel("BC", color='blue')
        ax11.spines["right"].set_position(("axes", 1.2))
        ax1.set_ylabel("Timers", color='red')
        ax2 = ax1.twinx()
        ax2.plot(zip(*sorted_t_1)[3], color='green')
        ax2.set_ylabel("Loss", color='green')
        ax1.set_xticks(np.arange(len(zip(*sorted_t_1)[0])))
        ax1.set_xticklabels(zip(*sorted_t_1)[0])
        # ax3 = ax1.twinx()
        # ax3.spines["right"].set_position(("axes", 0.5))
        # ax3.plot(zip(*sorted_t_1)[3], color="black")
        fig.tight_layout()
        plt.show()
        #plt.savefig("%s.png"%(how))

    def compute_average_loss(self, how="NOpop", leaf_nodes=False, articulation_points=False):
        # compute timers then compute duration of losses due to the failure of all nodes (leaf_nodes may be excluded)
        self.compute_timers(how)
        L_h = 0
        L_tc = 0
        for node in self.G.nodes():
            if not articulation_points:
                if node in self.artPoints:
                    continue
            if not leaf_nodes:
                if self.deg_dict[node] == 1:
                    continue
            L_h += self.Hi[node] * self.pathsCounts[node] # self.CTV_P.bet_dict[node]
            L_tc += self.R / self.TCi[node]
        return (round(L_h, self.decimal_values), round(L_tc, self.decimal_values))

    # def compute_critical_loss(self, how="NOpop", leaf_nodes=False, perc=10):
    #     # define critical nodes
    #     howmanyCritical = int(perc/100.0 * len(self.G.nodes()))
    #     critical = set()
    #     sorted_x = sorted(self.pathsCounts.items(),
    #                       key=operator.itemgetter(1), reverse=True)
    #     #srtnds = [e[0] for e in sorted_x]
    #     queue = deque(sorted_x)
    #     while(howmanyCritical != 0 and queue):
    #         critical.add(queue.popleft()[0])
    #         howmanyCritical -= 1
    #     # compute timers then compute duration of losses due to the failure of critical nodes
    #     if not critical:
    #         print("Non ho individuato la percentuale richiesta di nodi critici!")
    #     self.compute_timers(how)
    #     L_h = 0
    #     for node in critical:
    #         if not leaf_nodes:
    #             if self.deg_dict[node] == 1:
    #                 continue
    #         L_h += self.Hi[node] * self.pathsCounts[node]
    #     
    #     return round(L_h, self.decimal_values)

    def compute_average_load(self, how):
        O_h = 0
        timers = self.compute_timers(how=how)
        #print(how)
        #myu.summary(timers.values())
        for node in timers:
            O_h += self.deg_dict[node]/timers[node]
        return round(O_h, self.decimal_values)

    def check_consistency(self):
        """ Check that the generated overhead is the same with
        and without pop """
        L_def = self.compute_average_load(how="NOpop")
        L_POP = self.compute_average_load(how="POP")
        L_POPPEN = self.compute_average_load(how="POPPEN")
        print("Load with NOpop/POP timers: %.3f - %.3f - %.3f" % (L_def, L_POP, L_POPPEN))
        return L_def == L_POP == L_POPPEN


if __name__ == '__main__':
    graph = nx.read_graphml(sys.argv[1])

    tV = TheoricValues(NXgraph=graph, weight=None)
    art = True
    #tV.check_consistency()
    NOpop = tV.compute_average_loss(how="NOpop", articulation_points=art)
    print("\n")
    POP = tV.compute_average_loss(how="POP", articulation_points=art)
    print("\n")
    POPPEN = tV.compute_average_loss(how="POPPEN", articulation_points=art)
    print("\n")
    print("Avg loss\nNOpop: %.3f/%.3f\nPOP: %.3f/%.3f\nPOPPen:%.3f/%.3f\n" % (NOpop[0], NOpop[1], POP[0], POP[1], POPPEN[0], POPPEN[1]))
    # NOpop = tV.compute_critical_loss(how="NOpop")
    # POP = tV.compute_critical_loss(how="POP")
    # print("Critical loss\nNOpop: %.3f\nPOP: %.3f\nratio:%.3f\n " % (NOpop, POP, NOpop/POP))
