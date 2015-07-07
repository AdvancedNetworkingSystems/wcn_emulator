#!/usr/bin/env python
import json
import time
import argparse
import pprint
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np

class ResultsComparer():

    def print_error(self, error):
        print "ERROR:", error

    def __init__(self, file_name):
        try:
            f = open(file_name, 'r')
            self.json = json.load(f)
        except IOError:
            self.print_error("could not open file"+file_name)
            exit()
        except ValueError:
            self.print_error(file_name + "contains no valid JSON")
            exit()
        self.data = defaultdict(dict)

    def parse_results(self):
        """ FIXME describe the format of the JSON files here """
        for topo_file in self.json:
            if topo_file in ['command', 'time']:
                continue
            # we want just numerical run ids, not other fields
            run_ids = sorted([x for x in self.json[topo_file].keys() \
                    if x.isdigit()])
            for runId in run_ids:
                g_type = self.json[topo_file][runId]["topology_type"]
                size = self.json[topo_file][runId]["network_size"]
                if not self.json[topo_file][runId]["failed_nodes"]:
                    continue
                failed_node = \
                    self.json[topo_file][runId]["failed_nodes"].keys()[0]
                failures = \
                    self.json[topo_file][runId]["failures"]
                results = self.json[topo_file][runId]["results"]
                s = sorted(results.keys(), key = lambda x: float(x))

                self.optimized = self.json[topo_file][runId]["optimized"]

                if sum(results[s[-1]][1:]):
                    print "Graph:", topo_file, "run id:", runId, \
                            "optimized:",self.optimized, \
                            "has unrepaired routes, skipping."
                    continue

                if not s:
                    continue
                min_time = float(s[0])
                max_time = float(s[-1])

                frequency = (max_time - min_time)/len(results.keys())
                if size not in self.data[g_type]:
                    self.data[g_type][size] = {'x':defaultdict(list), \
                            'y':defaultdict(list), 'topo_file':defaultdict(list)}
                self.data[g_type][size]['x'][runId].append(failed_node)
                self.data[g_type][size]['y'][runId].append(failures*frequency)
                self.data[g_type][size]['topo_file'][runId].append(topo_file)
                self.simulation_time = self.json["time"]

    def print_raw_data(self):
        for g_type in self.data:
            for size in self.data[g_type]:
                print "Type:", g_type, "Size: ", size
                for runId in self.data[g_type][size]['y']['topo_file']:
                    print self.data[g_type][size]['x']['topo_file'][runId]
                    print self.data[g_type][size]['y']['topo_file'][runId]
        
    def average_data(self):
        self.average_data = defaultdict(dict) 
        for g_type in self.data:
            for size in self.data[g_type]:
                crashes = [x for x in self.data[g_type][size]['y'].keys() \
                        if x.isdigit()]
                graphs = \
                    min([len(self.data[g_type][size]['y'][c]) for c in crashes])
                avg_y = []
                for i in sorted([int(x) for x in crashes]):
                    avg_v = 0
                    for run in range(graphs):
                        avg_v += self.data[g_type][size]['y'][str(i)][run]
                    avg_y.append(1.0*avg_v/graphs)
                self.average_data[size][g_type] = {'y':avg_y, 'runs':graphs}



    def format_data_for_plot(self, desc=""):
        self.formatted_data = {}
        for size in self.average_data:
            data = {}
            data["plot"] = {}
            data["desc"] = desc
            title = "nodes: " + str(size) 
            runs = self.average_data[size].items()[0][1]['runs']
            title += ", runs:" + str(runs)
            data["title"] = title
            data["time"] = time.ctime(int(self.simulation_time))
            data["optimized"] = self.optimized
            for g_type in self.average_data[size]:
                data["plot"][g_type] = self.average_data[size][g_type]['y']
            self.formatted_data[size] = data


class DataMerger():

    def __init__(self):
        self.data = {}

    def merge_data(self, r_c):
        results_comparer = r_c.data
        for g_type in results_comparer:
            for size in results_comparer[g_type]:
                if size not in self.data:
                    self.data[size] = {}
                if g_type not in self.data[size]:
                    self.data[size][g_type] = {}
                opt = r_c.optimized
                if opt not in self.data[size][g_type]:
                    self.data[size][g_type][opt] = {}
                for run_id, run_id_vec in results_comparer[g_type][size]['y'].items():
                    # run_id follows the order in the sequence of failures
                    # so it mirrors the order by centrality of failed nodes
                    if run_id not in self.data[size][g_type][opt]:
                        self.data[size][g_type][opt][run_id] = {}
                        for idx, failed_routes in enumerate(run_id_vec):
                            graph = \
                                results_comparer[g_type][size]['topo_file'][run_id][idx]
                            if graph not in self.data[size][g_type][opt][run_id]:
                                self.data[size][g_type][opt][run_id][graph] = \
                                    failed_routes

    def compare_data(self, rem_extremes=False):
        data_c = defaultdict(dict)
        for size in self.data:
            for g_type in self.data[size]:
                data_c[size][g_type] = {'y':{}}
                if len(self.data[size][g_type]) == 2:
                    y = []
                    for run_id in sorted(self.data[size][g_type][True], key = lambda(x) : int(x)):
                        for graph in self.data[size][g_type][False][run_id]:
                            if graph in self.data[size][g_type][True][run_id]:
                                if self.data[size][g_type][True][run_id][graph]:
                                    try:
                                        y.append(self.data[size][g_type][True][run_id][graph] \
                                                / self.data[size][g_type][False][run_id][graph])
                                    except ZeroDivisionError:
                                        pass
                        data_c[size][g_type]['y'][int(run_id)] = \
                                np.average(y)
        return data_c



    def plot_data(self, data):
        # TODO add info to the graph
        for size in data:
            f = plt.figure()
            plt.title("Size:"+size)
            for g_type in data[size]:
                plt.plot(data[size][g_type]['y'].keys(), 
                        data[size][g_type]['y'].values(), label=g_type)
            plt.legend()
            plt.show()

    def print_data(self):
        pp = pprint.PrettyPrinter()
        pp.pprint(self.data)



def parse_args():
     parser = argparse.ArgumentParser(description = \
             "parser of results file generated by run_batch_simulations.py")
     parser.add_argument('-d', dest='description', help="a description to "+\
             "be added to the results", default="", type=str)
     parser.add_argument('-f', dest='res_file',
             help="the file with the results", action="append",
             required=True, type=str)
     parser.add_argument('-s', dest='show_graph',
             help="show the plot", action="store_true",
             required=False, default=False)
     #parser.add_argument('-o', dest='res_file_opt',
     #        help="the file with the results for the optimized run",
     #        required=False, type=str)
     args = parser.parse_args()
     return args

    

args = parse_args()
m = DataMerger()
for res_file in args.res_file:
    r = ResultsComparer(res_file)
    r.parse_results()
    r.average_data()
    r.format_data_for_plot()
    m.merge_data(r)
c = m.compare_data()
if args.show_graph:
    m.plot_data(c)
m.print_data()
#if args.res_file_opt:
#    ro = ResultsComparer(args.res_file_opt)
#    ro.parse_results()
#    ro.average_data()
             #    ro.format_data_for_plot()
#    m = generate_relative_dataset(r.formatted_data, ro.formatted_data)
#    print_data(m)

#
#def generate_relative_dataset(non_opt, opt):
#
#    # let's check the size of the result set
#    if opt.keys() == non_opt.keys():
#        for size in opt:
#            if opt[size]['plot'].keys() == non_opt[size]['plot'].keys():
#                for g_type in opt[size]['plot']:
#                    if len(opt[size]['plot'][g_type]) == \
#                            len(non_opt[size]['plot'][g_type]):
#                        continue
#                    else:
#                        print opt[size]['plot'][g_type], "is not as long as", \
#                                non_opt[size]['plot'][g_type]
#                    return {}
#            else:
#                print opt[size]['plot'], " differs from ", non_opt[size]['plot']
#                return {}
#    else:
#        print opt.keys(), "differs from", non_opt.keys()
#        return {}
#
#    merged_data = opt.copy()
#    for size in opt:
#        for g_type in opt[size]['plot']:
#            merged_data[size]['plot'][g_type] = np.array(
#                    opt[size]['plot'][g_type])/np.array(
#                    non_opt[size]['plot'][g_type])
#            merged_data[size]['title'] += "size:" + str(size)
#    return  merged_data
#
#def print_data(merged_data):
#    for size in merged_data:
#        f = plt.figure()
#        f.title = merged_data[size]['title']
#        for g_type in merged_data[size]['plot']:
#            y = merged_data[size]['plot'][g_type]
#            plt.plot(range(len(y)), y, 'o', label=g_type)
#        plt.xlabel("Crashed node, orderd by betweenness")
#        plt.ylabel("Failed routes")
#        plt.ylim([0,1])
#        plt.legend()
#        plt.show()
