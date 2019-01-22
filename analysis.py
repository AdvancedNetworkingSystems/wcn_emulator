import sys
import os
import numpy as np
import csv
def mean_exp(path):
    result = []
    for p in ["NOPOP", "POP", "POPPEN"]:
        with open("%s/%s/result.dat" % (path, p)) as f:
            data = []
            r = csv.reader(f)
            for l in r:
                data.append(int(l[0]))
            result.append(np.mean(data))
    return result


def mean_val(subpath):
    breaks = []
    dirs = os.listdir(subpath)
    for node in dirs:
        with open("%s/%s/breakage.dat" % (subpath, node)) as f:
            data = []
            reader = csv.reader(f)
            for row in reader:
                d = {}
                d['timestamp'] = int(row[0])
                d['correct'] = int(row[1])
                data.append(d)
            m_route = max(data, key=lambda x: x['correct'])['correct'] #Search for the max number of route (right one)
            filtered = data[5:-5] #Remove all the data before the wait time and the last 10 seconds
            stable = sorted([d['timestamp'] for d in filtered if d['correct'] != m_route])  # filter all about the fluctuations
            longest_seq = max(np.split(stable, np.where(np.diff(stable) != 1)[0]+5), key=len).tolist()
            print "%.2f,%s" %(float(len(longest_seq)) * 0.5, node) #ds
            # diff = [x1 - x2 - 1 for (x1, x2) in zip(stable[1:], stable[:-1])] #make a vector of differences
            # print >> fw, max(diff)


def main(path):
    for p in ["NOPOP", "POP", "POPPEN"]:
        print(p)
        mean_val("%s/%s" % (path, p))

if __name__ == '__main__':
    main(sys.argv[1])
