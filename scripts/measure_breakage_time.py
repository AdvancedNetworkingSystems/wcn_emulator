#!/usr/bin/env python

import sys
sys.path.append('../community_networks_analysis')

from misclibs import navigateRoutingTables, LoopError
from collections import defaultdict
import glob
import json
import copy

def readTopology(pathPrefix):
    jsonRt = defaultdict(dict)
    nodeSet = set()
    failedNodes = {}
    for topoFile in glob.glob(pathPrefix+"*.json"):
        try:
            f = open(topoFile, "r")
            j = json.load(f)
        except Exception as e:
            print "NOK", str(e)
            sys.exit(1)
        #nodeIP = ".".join(j["node"].split(":")[0].split(".")[:3])
        nodeIP = j["node"].split(":")[0]
        if j["fail"] == True:
            failedNodes[nodeIP] = j["failtime"]
        rt = j["log"]
        for logId, logDump in rt.items():
            jsonRt[logId][nodeIP] = logDump["RT"]
            jsonRt[logId]["time"] = logDump["time"]
        nodeSet.add(str(nodeIP))
    return jsonRt, nodeSet, failedNodes


def checkRoutingTables(jsonRt, ns, failedNodes):
    errors = 0
    loops = 0
    jsonRtPurged = copy.deepcopy(jsonRt)

    for failedNode, failureTime in failedNodes.items():
        if jsonRt["time"] > failureTime and failedNode in ns:
            ns.remove(failedNode)

    nl = list(ns)
    routesOk = 0
    for i in range(len(nl)):
        sIP = nl[i]
        for j in range(len(nl)):
            if i == j:
                continue
            dIP = nl[j]
            try:
                route = navigateRoutingTables(jsonRtPurged, sIP,
                    dIP, [], 0)
            except KeyError as e:
                errors += 1
                print str(e)
                print sIP, jsonRt[sIP]
                print dIP, jsonRt[dIP]
                print "NOK!: there is no route from ", sIP, "to", dIP
                continue
            except LoopError:
                print "NOK: there is a loop from", sIP, "to", dIP
                loops += 1
                continue
            print "OK!: route", route
            routesOk += 1
    return routesOk, errors, loops




if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "This script parses dumps of routing tables, recomputes all the shortest paths"
        print "and finds the number and time of breakage of the network"
        print "usage: ./measure_breakage_time.py ",\
                "path_prefix"
        print "path_prefix is the prefix of the routing table files generated by dummyrouting"
        sys.exit(1)


    pathPrefix = sys.argv[1]

    jsonRt, nodeSet, failedNodes = readTopology(pathPrefix)
    print nodeSet, failedNodes

    if not nodeSet:
        print "NOK: can not read routing tables"
        sys.exit(1)

    for logId, rt in sorted(jsonRt.items(), key = lambda x: int(x[0]))[:-1]:
        # skip the last one, misalignments with random timers can 
        # produce partial data
        routesOk, routeErrors, loopErrors = \
                checkRoutingTables(jsonRt[logId], nodeSet,
                        failedNodes)
        print "XX", jsonRt[logId]["time"], routesOk, routeErrors, loopErrors

