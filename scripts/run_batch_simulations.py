#! /usr/bin/env python

import sys
import os
import time
import argparse
import glob
import matplotlib.pyplot as plt
from subprocess import check_output, CalledProcessError, call
from collections import defaultdict

import json

from measure_breakage_time import resultParser

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
        self.args = parser.parse_args()


    def run_and_parse(self):
        # FIXME change the number of runs with a sequence of 
        # different configurations (runs have been included in the simulator)
        if not self.args.parseonly and os.getuid() != 0:
            print "You should run this script as root"
            sys.exit(1)
        p = resultParser()
        self.path_prefix = "/tmp/dummyrouting-log"
        ret_value = defaultdict(dict)
        for i in range(self.args.runs):
            if not self.args.parseonly and i == 0:
                self.clean_environment()
            elif i != 0:
                self.clean_environment(auto=True)
            command = ["./wcn_simulator.py", "-f", str(self.args.confile), \
                    "-t", str(self.args.stanza)]
            self.command = command
            if not self.args.parseonly:
                self.execute_run(command)
            jsonRt, nodeSet, failedNodes, signallingSent, sigPerSec,\
                logFrequency = p.readTopology(self.path_prefix)
            for runId in jsonRt:
                print "QQQQQQQQQQQQQQ ", runId
                results = p.parseAllRuns(jsonRt[runId], nodeSet, 
                        failedNodes[runId], silent=True)
                failures = 0
                for tt in sorted(results):
                    failures += sum(results[tt][1:])
                ret_value[runId][i] = {}
                ret_value[runId][i]["results"] = results
                ret_value[runId][i]["signalling"] = signallingSent
                ret_value[runId][i]["failures"] = failures
                ret_value[runId][i]["failed_nodes"] = failedNodes
                ret_value[runId][i]["sigPerSec"] = sigPerSec
                ret_value[runId][i]["logFrequency"] = logFrequency
        return ret_value

    def save_results(self, results):
        results["time"] = time.time()
        results["command"] = " ".join(self.command)
        out_string = json.dumps(results, indent=1)
        out_file_name = "/tmp/"+self.args.stanza+"_"+str(int(time.time()))+".results"
        try:
            out_file = open(out_file_name, 'w')
        except:
            print "Error: could not open file " + out_file
            raise
        print >> out_file, out_string
        out_file.close()

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
        run_number = 0
        for runId,v in results.items():
            if runId in ["time", "command"]:
                continue
            run_x = []
            run_y = []
            for tt,vv in (sorted(v["results"].items(),
                key = lambda x: x[0])):
                run_x.append(tt)
                run_y.append(vv[1] + vv[2])
            run_number += 1
            x.append(run_x)
            y.append(run_y)
        print x,y
        for runId in range(run_number):
            plt.plot(x[runId],y[runId], label="Failed node:")
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        title += " runs:" + str(run_number)
        plt.title(title)
        plt.savefig("/tmp/pp.png")
        plt.show()


    def clean_environment(self, auto=False):
        commands = []
        log_files = glob.glob(self.path_prefix+"*")
        dump_files = glob.glob("../"+self.args.stanza+"*")
        c = []
        if log_files:
            commands.append(["rm", "-rf"]+log_files)
        if dump_files:
            commands.append(["rm", "-rf"]+dump_files)
        if not auto:
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
    results = e.run_and_parse()
    resultSerie = defaultdict(dict)
    for runId in results:
        r = e.summarise_results(results[runId])
        e.plot_results(results[runId], title = "Tot failures:" + str(r["failures"]) + \
                ", tot signalling:" + str(r["signalling"]) + ", sig/sec:" + \
                "%.2f" % round(r["sigpersec"],2))
        resultSerie[runId]['failures'] = r['failures']
        resultSerie[runId]['signalling'] = r['signalling']
        resultSerie[runId]['sigpersec'] = r['sigpersec']
    e.save_results(results)
    print resultSerie
