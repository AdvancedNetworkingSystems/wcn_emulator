import sys
import os
import numpy as np
import csv
import pandas

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
            stable = sorted([(d['timestamp'], d['correct']) for d in filtered if d['correct'] != m_route], key=lambda x: x[0])  # filter all about the fluctuations
            longest_seq = max(np.split(stable, np.where(np.diff(stable[0]) != 5)[0]+1), key=len).tolist()
            breakage = 0
            for l in longest_seq:
                breakage += 0.5*(m_route-l[1])
            breaks.append(breakage)
            #print "%.2fs,%s"%(breakage, node) #ds
    return breaks

def main(path, n_run, n_samples):
    samples = n_samples
    n_params = 3
    data = np.empty([n_run, n_params, samples])
    dirs = os.listdir(path)
    dirs.sort()
    i=0
    for d in dirs[:n_run]:
        j=0
        params = ["NOPOP", "POP", "POPPEN"]
        for p in params[:n_params]: 
            breaks =  mean_val("%s/%s/%s" % (path, d, p))
            data[i,j]=breaks
            j+=1
        i+=1

    #for i in range(n_run):
        #print pandas.DataFrame(data[i])
    #d = np.mean(data, (0))
    #print pandas.DataFrame(d)
    means = np.mean(data, (2))
    mean = np.mean(means, (0))
    std = np.std(means, (0))
    print("%f,%f,%f,%f,%f,%f"%(mean[0], std[0],mean[1],std[1],mean[2],std[2]))

if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
