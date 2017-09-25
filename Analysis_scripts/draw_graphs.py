import networkx as nx
import sys
import matplotlib.pyplot as plt


def main():
    args = sys.argv
    folder = args[1]
    g = nx.read_adjlist(folder + "/topology.adj")
    nx.draw_circular(g)
    plt.show()



if __name__ == "__main__":
    main()
