import csv
import numpy as np
import sys
for p in ["NOPOP", "POP", "POPPEN"]:
    with open("%s/%s/result.dat" % (sys.argv[1], p)) as f:
        data = []
        r = csv.reader(f)
        for l in r:
            data.append(int(l[0]))
        print("%s mean is %f" % (p, np.mean(data)))
        
