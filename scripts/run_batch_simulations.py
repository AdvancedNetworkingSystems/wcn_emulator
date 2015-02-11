#! /usr/bin/env python

import sys
import os
import time
import argparse
import glob
sys.path.append("../")
from inherit_config_parser import InheritConfigParser
import tarfile
import matplotlib.pyplot as plt
from subprocess import check_output, CalledProcessError, call
from collections import defaultdict

import json

from measure_breakage_time import resultParser

topology_override_string = "no_topology_override_see_config_file"

class EmulationRunner():

    def __init__(self):
        self.path_prefix = ""
        self.args = None

    def parse_args(self):
        parser = argparse.ArgumentParser(description = "batch simulation launcher"+ \
            " and analyser")
        parser.add_argument("-r", dest="runs", help="number of runs",
            default=1, type=int)
        parser.add_argument("-f", dest="confile", help="configuration file",
            default="conf/dummyrouting.ini", type=str)
        parser.add_argument("-t", dest="stanza", required=True,
                help="name of the configuration to run", type=str)
        parser.add_argument("-p", dest="parseonly", action="store_true",
                help="do not run the simulation, only parse results")
        parser.add_argument("-g", dest="graphfolder", action="append",
                help="a folder with .adj files from which to"\
                        +"extract topologies (multiple folders are supported)")
        self.args = parser.parse_args()


    def extract_simulation_type_from_conf(self, conf, file_name, stanza):
        parser = InheritConfigParser()
        parser.optionxform = str
        file_name = "../" + file_name
        parser.read(file_name)

        if stanza not in parser.sections():
            print file_name, stanza
            print "ERROR: I can't find the configuration specified! this run will fail"
            return True # this configuration will fail anyway!
        try:
            r = parser.get(stanza, conf)
            return True
        except:
            return False 

    def run_and_parse(self, size, type, res=None, 
            topo_files = [topology_override_string], auto_clean=False):
        if not self.args.parseonly and os.getuid() != 0:
            print "You should run this script as root"
            sys.exit(1)
        p = resultParser()
        self.path_prefix = "/tmp/dummyrouting-log"
        if res == None:
            res = defaultdict(dict)
        optimized = self.extract_simulation_type_from_conf("centralityTuning", 
                str(self.args.confile), str(self.args.stanza))

        prev_run_id = ""
        for topo in topo_files:
            if prev_run_id:
                self.save_environment(prev_run_id)
                prev_run_id = ""
            command = ["./wcn_simulator.py", "-f", str(self.args.confile), \
                    "-t", str(self.args.stanza)]
            #TODO: yes this sucks a bit...
            if topo != topology_override_string:
                command +=  ["-g", os.path.abspath(topo)]
                prev_run_id = os.path.splitext(os.path.basename(topo))[0] 
            prev_run_id += str(self.args.stanza)

            if not self.args.parseonly and not auto_clean:
                self.clean_environment()
                auto_clean=True
            elif auto_clean:
                self.clean_environment(auto=True)

            self.command = command
            if not self.args.parseonly:
                self.execute_run(command)
            jsonRt, nodeSet, failedNodes, signallingSent, sigPerSec,\
                logFrequency = p.readTopology(self.path_prefix)
            for runId in jsonRt:
                total_fail_samples = 0
                results = p.parseAllRuns(jsonRt[runId], nodeSet, 
                        failedNodes[runId], silent=True)
                failures = 0
                log_time_array = sorted(results)
                for tt in log_time_array:
                    failures += sum(results[tt][1:])
                    total_fail_samples += 1
                res[topo][runId] = {}
                res[topo][runId]["signalling"] = signallingSent
                res[topo][runId]["failures"] = failures
                res[topo][runId]["failed_nodes"] = failedNodes[runId]
                res[topo][runId]["sigPerSec"] = sigPerSec
                res[topo][runId]["logFrequency"] = logFrequency
                res[topo][runId]["network_size"] = size
                res[topo][runId]["topology_type"] = type
                res[topo][runId]["optimized"] = optimized
                res[topo][runId]["results"] = results
                res[topo][runId]["total_fail_samples"] = total_fail_samples
                res[topo][runId]["unrepaired_routes"] = \
                    sum(results[log_time_array[-1]][1:])

        return res

    def save_results(self, results):
        results["command"] = " ".join(self.command)
        results["time"] = time.time()
        out_string = json.dumps(results, indent=1)
        out_file_name = "/tmp/"+self.args.stanza+"_"+str(int(time.time()))+".results"
        try:
            out_file = open(out_file_name, 'w')
        except:
            print "Error: could not open file " + out_file
            raise
        print >> out_file, out_string
        out_file.close()
        return out_file_name

    def summarise_results(self, results):
        signalling_messages = 0
        failed_routes = 0
        sig_per_sec = 0
        counter = 0
        logFrequency = 0
        for k,v in results.items():
            if k in ["time", "command"]:
                continue
            # we assume all nodes log with the same freq
            logFrequency = v["logFrequency"]
            signalling_messages += v["signalling"]
            failed_routes += v["failures"]
            sig_per_sec += v["sigPerSec"]
            counter += 1
        ret_value = {}
        ret_value["signalling"] = signalling_messages
        ret_value["sigpersec"] = float(sig_per_sec)/counter
        ret_value["failures"] = failed_routes/logFrequency
        return ret_value

    def plot_results(self, results, title=""):
        x = []
        y = []
        xlabel = "Experiment Time"
        ylabel = "Broken Paths"
        for tt,vv in (sorted(results["results"].items(),
            key = lambda x: x[0])):
            x.append(tt)
            y.append(vv[1] + vv[2])
        plt.plot(x,y, label="Failed node:")
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        plt.savefig("/tmp/pp.png")


    def save_environment(self, path_name):
        log_files = glob.glob(self.path_prefix+"*")
        t = tarfile.open(path_name+"tar.gz", "w:gz")
        for f in log_files:
            t.add(f)
        t.close()


    def clean_environment(self, auto=False):
        commands = []
        log_files = glob.glob(self.path_prefix+"*")
        dump_files = glob.glob("../"+self.args.stanza+"*")
        c = []
        user_input = 'n'
        if log_files:
            commands.append(["rm", "-rf"]+log_files)
        if dump_files:
            commands.append(["rm", "-rf"]+dump_files)
        if not auto and commands:
            inputString = "I'm about to run:\n"
            for c in commands:
                inputString += " ".join(c) + "\n"
            inputString += "[y/n]:"
            user_input = raw_input(inputString)
        if auto or user_input == 'y':
            for c in commands:
                call(c)
        elif user_input != 'n' and not auto:
            user_input = raw_input("please choose y/n:")
            if user_input == 'y':
                for c in commands:
                    call(c)
            elif user_input != 'n':
                print "seems you're too dumb to choose between y/n, erasing nothing"

    def get_topo_list_from_folder(self):
        # I expect to have topo files in a structure like: 
        # data_path/TYPE_LABEL/SIZE/graph*.edges
        # TODO support a list of folders separated by comma
        topo_files = []
        type_label = []
        size = []

        if self.args.graphfolder:
            for folder in self.args.graphfolder:
                topo_files.append(glob.glob(
                    folder + "*.edges")[:self.args.runs])
                type_label.append(folder.split("/")[-3])
                size.append(folder.split("/")[-2])
        else:
            type_label = [topology_override_string]
            size = [topology_override_string]
            topo_files = [[topology_override_string]]
        return topo_files, size, type_label
        


    def execute_run(self, command):

        if not command:
            print "Please give me a command to run"
            sys.exit(1)
        try:
            output = check_output(command, cwd="../")
        except CalledProcessError:
            print "command: ", command , " exited with non-zero value"
            raise
        except:
            print "Could not run command ", command
            raise

if __name__ == "__main__":
    e = EmulationRunner()
    e.parse_args()
    topo_list, size_list, type_list = e.get_topo_list_from_folder()
    # TODO loop 
    # over the folders, pass results to the next run_and_parse
    results = defaultdict(dict)
    for index, file_list in enumerate(topo_list):
        e.run_and_parse(size_list[index],
            type_list[index], res=results, topo_files=file_list, 
            auto_clean = bool(index))
        #TODO fix also size and type
    #resultSerie = defaultdict(dict)
    for topo in results:
        for runId in results[topo]:
            #r = e.summarise_results(results[topo][runId])
            r = results[topo][runId]
            import code
            e.plot_results(results[topo][runId], 
                    title = "Optimized = " + str(r['optimized']) + ". Tot failures:" + str(r["failures"]/r["logFrequency"]) + \
                    ", tot signalling:" + str(r["signalling"]) + ", sig/sec:" + \
                    "%.2f" % round(r["sigPerSec"],2))
            #code.interact(local=locals())
            #resultSerie[topo]['failures'] = r['failures']
            #resultSerie[topo]['signalling'] = r['signalling']
            #resultSerie[topo]['sigpersec'] = r['sigpersec']
    e.save_results(results)
    #print resultSerie
