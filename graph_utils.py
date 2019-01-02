import json
import sys
import networkx as nx
from graph_lib.graph_generator import Gen


def generate_graph(gkind, size):
    ge = Gen()
    if gkind == "CN":
        ge.genCNGraph(N=int(size), T=size*2)
    elif gkind == "NPART":
        ge.genMeshGraph(N=size, seed=False)
    else:
        ge.genGraph(graphKind=gkind, numNodes=size)
    return ge.graph


def save_netjson(graph, path):
    ge = Gen()
    nj = ge.composeNetJson(graph)
    with open(path + "/topolgy.json", 'w') as outfile:
        json.dump(nj, outfile)
        return True
    return False

def load_json(json_file):
    """ import a json file in NetJSON format, convert to Graph class
    Parameters
    ----------
    json_file : string with file path
    """

    try:
        file_p = open(json_file, "r")
    except IOError:
        raise
    try:
        netjson_net = json.load(file_p)
    except ValueError as err:
        print "Could not decode file", err
    # TODO add a schema to validate the subset of features we are
    # able to consider

    G = nx.Graph()
    cost_label = ""
    if "metric" in netjson_net and netjson_net["metric"] == "ff_dat_metric":
        cost_label = "cost"
    for node in netjson_net["nodes"]:
        if "properties" in node:
            if node["properties"]["type"] == "local" or node["properties"]["type"] == "node":
                G.add_node(node["id"])
        else:
            G.add_node(node["id"])
    for link in netjson_net["links"]:
        if "properties" in link:
            if link["properties"]["type"] == "local" or link["properties"]["type"] == "node":
                if cost_label:
                    cost = float(link["cost"])
                else:
                    cost = 1.0
                G.add_edge(link["source"], link["target"], {"weight": cost})
        else:
            if cost_label:
                cost = float(link["cost"])
            else:
                cost = 1.0
            G.add_edge(link["source"], link["target"], {"weight": cost})
    return G


def loadGraph(fname, remap=False, connected=True, silent=False):
    """ Parameters
    --------------
    fname : string
        filname to open
    remap : bool
        remap the labels to a sequence of integers
    connected : bool
        return only the larges component subgraph

    """
    G = nx.Graph()
    if not silent:
        print "Loading/Generating Graph"
    # load a file using networkX adjacency matrix structure
    if fname.lower().endswith(".adj"):
        try:
            G = nx.read_adjlist(fname, nodetype=int)
        except IOError as err:
            print
            print err
            sys.exit(1)
    # load a file using networkX .edges structure
    elif fname.lower().endswith(".edges"):
        try:
            G = nx.read_weighted_edgelist(fname, nodetype=int)
        except IOError as err:
            print
            print err
            sys.exit(1)
    # load a a network in NetJSON format
    elif fname.lower().endswith(".json"):
        try:
            G = load_json(fname)
        except IOError as err:
            print
            print err
            sys.exit(1)
    else:
        print >> sys.stderr, "Error: Allowed file extensions are .adj for",\
            "adjacency matrix, .json for netjson and .edges for edge-list"
        sys.exit(1)
    if connected:
        C = sorted(list(nx.connected_component_subgraphs(G)),
                   key=len, reverse=True)[0]
        G = C
    if not silent:
        print >> sys.stderr, "Graph", fname, "loaded",
    # remap node labels so we don't have "holes" in the numbering
    if remap:
        mapping = dict(zip(G.nodes(), range(G.order())))
        H = nx.relabel_nodes(G, mapping)
        return H
    return G
