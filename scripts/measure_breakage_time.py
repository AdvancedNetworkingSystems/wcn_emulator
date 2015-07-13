#!/usr/bin/env python

import sys
sys.path.append('../community_networks_analysis')

from misclibs import navigateRoutingTables, LoopError
from collections import defaultdict, Counter
import glob
import json
import copy

class resultParser():

    def readTopology(self, pathPrefix, matchPath=""):
        """ load all the .json files with the logged routing tables, 
        return the global time-varying routing table """
        jsonRt = {}
        nodeSet = set()
        failedNodes = {}
        signallingSent = 0
        timeBasedRoute = {}
        logFrequency = 0
        helloTimers = []
        tcTimers = []
        # FIXME add read from zip files here
        files = glob.glob(pathPrefix + "*" + matchPath + ".json")
        print pathPrefix + "*" + matchPath + ".json"
        for topoFile in files:
            try:
                f = open(topoFile, "r")
                j = json.load(f)
                f.close()
            except Exception as e:
                print "NOK", str(e)
                print topoFile
                try:
                    f.close()
                except:
                    pass
                return {},0,0,0,0,0
            #nodeIP = ".".join(j["node"].split(":")[0].split(".")[:3])
            nodeIP = j["node"].split(":")[0]
            rt = j["log"]
            # number of samples per second
            logFrequency = j["logFrequency"]
            helloTimers.append(float(j["hello_timer"]))
            tcTimers.append(float(j["tc_timer"]))
            # number of loss in a second
            runId = j["failureId"]
            if runId not in timeBasedRoute:
                timeBasedRoute[runId] = defaultdict(dict)
            if runId not in failedNodes:
                failedNodes[runId] = {}
            if j["fail"] == True:
                failedNodes[runId][nodeIP] = float(j["failtime"])
            if runId not in jsonRt:
                jsonRt[runId] = defaultdict(dict)
            try:
                for logId, logDump in rt.items():
                    jsonRt[runId][logId][nodeIP] = logDump["RT"]
                    if "time" not in jsonRt[runId][logId] or \
                            jsonRt[runId][logId]["time"] > float(logDump["time"]):
                        jsonRt[runId][logId]["time"] = float(logDump["time"])
                    timeBasedRoute[runId][logId][nodeIP] = [float(logDump["time"]), logId]
            except KeyError:
                print "ERROR: topo file", topoFile, "on run_id", runId,\
                      "contins wrong keys"
                del jsonRt[runId]
            nodeSet.add(str(nodeIP))
        # alignedJsonRt = self.reorderLogs(timeBasedRoute, jsonRt, failedNodes, nodeSet)
        return jsonRt, nodeSet, failedNodes, signallingSent, \
                logFrequency

    def reorderLogs(self, timeBasedRoute, jsonRt, failedNodes, nodeSet):

        logWindow = {} 
        orderedLogSequence = []
        alignedJsonRt = {}


        for runId in timeBasedRoute:
            # just a big time
            earliestFailure = (2050-1970)*365*24*60*60
            for node, failTime in failedNodes[runId].items():
                if failTime < earliestFailure:
                    earliestFailure = failTime
            # for each time,  a list of [IP, logId] that logged at that time
            logSequence = defaultdict(list)
            for logId in timeBasedRoute[runId]:
                for nodeIP in timeBasedRoute[runId][logId]:
                    try:
                        nodeLogId = timeBasedRoute[runId][logId][nodeIP][1]
                        nodeLogTime = timeBasedRoute[runId][logId][nodeIP][0]
                        logSequence[nodeLogTime].append([nodeIP, nodeLogId])
                    except KeyError:
                        print "WARNING, key", nodeIP, "not present in logId", \
                              logId
            orderedLogSequence = sorted(logSequence.items(),
                                        key=lambda x: x[0])
            newJsonRt = defaultdict(dict)
            newJsonRtCheck = defaultdict(dict)

            currLogId = 1
            includeFailed = True
            logWindow = dict.fromkeys(nodeSet, 0)
            for (t, data) in orderedLogSequence:
                for [ip, nodeRunId] in data:
                    # right end of time window arrived to the failure time
                    # we have to remove from current time-window all the failed
                    # nodes if they have no log currently assigned, as they
                    # will not have any more saved log
                    if t > earliestFailure:
                        if includeFailed:  # this bool is needed to repeat the
                                           # next routing only once
                            for ip in list(logWindow.keys()):
                                if ip in failedNodes[runId].keys() and\
                                   logWindow[ip] == 0:
                                        # we have a failed node that did
                                        # not save
                                        # log in this time window, so we will
                                        # remove all failed nodes from the
                                        # current window
                                        print "removing failed nodes",
                                        for ip in failedNodes[runId].keys():
                                            del logWindow[ip]
                                            print ip,
                                        print "failtime", earliestFailure
                                        includeFailed = False
                                        # we're looping on a modified structure
                                        break
                                else:
                                    logWindow[ip] = [t, nodeRunId]
                        elif ip not in failedNodes[runId]:
                            logWindow[ip] = [t, nodeRunId]
                    else:
                        logWindow[ip] = [t, nodeRunId]
                if 0 not in logWindow.values():
                    for ip, [tt, lid] in logWindow.items():
                        if ip not in jsonRt[runId][lid]:
                            print "WARNING: removing logId", lid
                            continue
                        newJsonRt[currLogId][ip] = jsonRt[runId][lid][ip]
                        if "time" not in newJsonRt[currLogId] or\
                            tt < newJsonRt[currLogId]["time"]:
                            newJsonRt[currLogId]["time"] = tt
                        newJsonRtCheck[currLogId][ip] = tt
                    currLogId += 1
                    # reset the logWindow
                    logWindow = dict.fromkeys(logWindow, 0)
            alignedJsonRt[runId] = copy.deepcopy(newJsonRt)
        return alignedJsonRt

    def checkRoutingTables(self, jsonRt, nodeSet, failedNodes, silent=True):
        errors = 0
        loops = 0
        # remove any non IP-like string from keys
        ipTest = lambda x: len(x.split(".")) == 4 and [int(b) for b in x.split(".")]
        nl = [k for k in jsonRt.keys() if ipTest(k)]
        routesOk = 0
        for i in range(len(nl)):
            sIP = nl[i]
            for j in range(len(nl)):
                if i == j:
                    continue
                dIP = nl[j]
                try:
                    route = navigateRoutingTables(jsonRt, sIP,
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
        return [routesOk, errors, loops]

    def gnuplotOutput(self, results, outFile="/tmp/res.gnuplot"):

        failTime = 0
        totFailures = 0
        ff = open(outFile, "w")
        for runId in results:
            for time in sorted(results[runId]):
                if sum(results[runId][time][1:3]):
                    failTime = time
                    break
            print >> ff, "time,", "broken,", "loop,", "total"
            for time in sorted(results[runId]):
                [ok, broken, loop, logId] = results[runId][time]
                print >> ff, time - failTime,  ",",  broken,\
                    ",", loop, ",", broken+loop
                totFailures += broken + loop
        ff.close()
        print "totFailures", totFailures


    def parseAllRuns(self, jsonRt, nodeSet, failedNodes, silent=True):

        retDict = {}
        # first we realign the logs, that can be 
        # misaligned at start or beginning, since the 
        # daemon starts and stops at different times

        # we also assure that the failure is contemporary for
        # all failed nodes, that is, from a certain logId 
        # all the jsonRt do not include the rt of the
        # failed nodes and we reset the failure time to the last 
        # available log time
        
        minFailTime = min(failedNodes.values())
        idToPurge = []
        for logId, rt in sorted(jsonRt.items(),
                key = lambda x: int(x[0])):
                for node in nodeSet:
                    if node not in rt.keys():
                        # this node is not in the rt
                        if node not in failedNodes:
                            # this node should be in the rt
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
            ret.append(logId)
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
    jsonRt, nodeSet, failedNodes, signallingSent,\
        logFrequency = p.readTopology(pathPrefix)

    if not nodeSet:
        print "NOK: can not read routing tables"
        sys.exit(1)


    results = {}
    for runId in jsonRt:
        results[runId] = p.parseAllRuns(jsonRt[runId], nodeSet, 
                failedNodes[runId], silent=True)
        print results

    p.gnuplotOutput(results)

