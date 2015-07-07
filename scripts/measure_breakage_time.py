#!/usr/bin/env python

import sys
sys.path.append('../community_networks_analysis')

from misclibs import navigateRoutingTables, LoopError
from collections import defaultdict
import glob
import json
import copy

class resultParser():

    def readTopology(self, pathPrefix):
        """ load all the .json files with the logged routing tables, 
        return the global time-varying routing table """
        jsonRt = {}
        nodeSet = set()
        failedNodes = {}
        signallingSent = 0
        timeBasedRoute = defaultdict(dict)
        sigPerSec = 0
        logFrequency = 0
        for topoFile in glob.glob(pathPrefix+"*.json"):
            try:
                f = open(topoFile, "r")
                j = json.load(f)
            except Exception as e:
                print "NOK", str(e)
                print topoFile
                return {},0,0,0,0,0
            #nodeIP = ".".join(j["node"].split(":")[0].split(".")[:3])
            nodeIP = j["node"].split(":")[0]
            rt = j["log"]
            # number of samples per second
            logFrequency = j["logFrequency"]
            # number of loss in a second
            signallingSent += j["signalling"]
            sigPerSec = j["signalling"]/j["logInterval"]
            runId = j["runId"]
            if runId not in failedNodes:
                failedNodes[runId] = {}
            if j["fail"] == True:
                failedNodes[runId][nodeIP] = j["failtime"]
            if runId not in jsonRt:
                jsonRt[runId] = defaultdict(dict)
            try:
                for logId, logDump in rt.items():
                    jsonRt[runId][logId][nodeIP] = logDump["RT"]
                    jsonRt[runId][logId]["time"] = logDump["time"]
                    timeBasedRoute[runId][logDump["time"]] = {}
                    timeBasedRoute[runId][logDump["time"]][nodeIP] = logDump["RT"]
            except KeyError:
                print "ERROR: topo file", topoFile, "on run_id", runId,\
                      "contins wrong keys"
                del jsonRt[runId]
            nodeSet.add(str(nodeIP))
            #print topoFile, failedNodes, nodeSet
        return jsonRt, nodeSet, failedNodes, signallingSent, sigPerSec, \
                logFrequency

    def checkRoutingTables(self, jsonRt, nodeSet, failedNodes, silent=True):
        errors = 0
        loops = 0
        jsonRtPurged = copy.deepcopy(jsonRt)
        failedNodeSet = set()
        ns = copy.deepcopy(nodeSet)

        for failedNode, failureTime in failedNodes.items():
            if jsonRt["time"] > failureTime and failedNode in ns:
                ns.remove(failedNode)
                failedNodeSet.add(failedNode)

        print "Failed nodes ", failedNodeSet

        nl = list(ns)
        routesOk = 0
        for i in range(len(nl)):
            sIP = nl[i]
            for j in range(len(nl)):
                if i == j:
                    continue
                dIP = nl[j]
                print "routing from", sIP, "to", dIP
                try:
                    route = navigateRoutingTables(jsonRtPurged, sIP,
                        dIP, [], 0, silent, use_base_ip=True)
                except KeyError:
                    errors += 1
                    if not silent:
                        print "NOK!: there is no route from ", sIP, "to", dIP
                    continue
                except LoopError:
                    if not silent:
                        print "NOK: there is a loop from", sIP, "to", dIP
                    loops += 1
                    continue
                if not silent:
                    print "OK!: route", route
                routesOk += 1
        return routesOk, errors, loops

    def parseAllRuns(self, jsonRt, nodeSet, failedNodes, silent=True):

        retDict = {}
        # first we realign the logs, that can be 
        # misaligned at start or beginning:
        idToPurge = []
        for logId, rt in sorted(jsonRt.items(),
                key = lambda x: int(x[0])):
                for node in nodeSet:
                    if node not in rt.keys():
                        # this node is not in the rt
                        if node not in failedNodes or \
                                (node in failedNodes and \
                                failedNodes[node] > rt["time"]):
                            # something did not work in this run
                            idToPurge.append(logId)
                            break
        for idx in idToPurge:
            print "WARNING: Purged run", idx
            del jsonRt[idx]

        for logId, rt in sorted(jsonRt.items(),
                key = lambda x: int(x[0])):
            print "===========", logId, "=========="
            ret = self.checkRoutingTables(
                    jsonRt[logId], nodeSet, failedNodes, silent=silent)
            retDict[jsonRt[logId]["time"]] = ret
        return retDict


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "This script parses dumps of routing tables, recomputes all the shortest paths"
        print "and finds the number and time of breakage of the network"
        print "usage: ./measure_breakage_time.py ",\
                "path_prefix"
        print "path_prefix is the prefix of the routing table files generated by dummyrouting"
        sys.exit(1)


    pathPrefix = sys.argv[1]

    p = resultParser()
    jsonRt, nodeSet, failedNodes, signallingSent, sigPerSec,\
        logFrequency = p.readTopology(pathPrefix)

    if not nodeSet:
        print "NOK: can not read routing tables"
        sys.exit(1)


    results = {}
    for runId in jsonRt:
        results[runId] = p.parseAllRuns(jsonRt[runId], nodeSet, 
                failedNodes[runId], silent=False)

    for runId in results:
        for time in sorted(results[runId]):
            print "FailedRoutes", time, results[runId][time]
    print "Signalling: ", signallingSent


