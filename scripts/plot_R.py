#!/usr/bin/env python
import json
import sys

try:
    pop_file = sys.argv[1]
    nonpop_file = sys.argv[2]
except:
    print "usage: ./plot_R.py popfile.results nonpopfile.results"
    exit(1)


try:
    f = open(pop_file, "r")
    p = json.load(f)
    f.close()
    f = open(nonpop_file, "r")
    np = json.load(f)
    f.close()
except:
    print "could not load json files!"
    exit(1)

pop_failures = {}
nonpop_failures = {}

for failure_id, data in p.items():
    try:
        idx = int(failure_id)
        pop_failures[idx] = float(data["failures"])
    except ValueError:
        pass

for failure_id, data in np.items():
    try:
        idx = int(failure_id)
        nonpop_failures[idx] = float(data["failures"])
    except ValueError:
        pass

data_file_name = "/tmp/data_file.txt"
data_file = open(data_file_name, "w")
gnuplot_file = open("/tmp/gnuplot_file.txt", "w")

print  >> data_file, "h,", "R" 
sorted_values = []
relative_values = []
avg = 0.0
global_loss_r_num = 0
global_loss_r_den = 0
for failure_id in sorted(pop_failures.keys()):
    #print >> data_file, failure_id, ",",\
    # nonpop_failures[failure_id]-pop_failures[failure_id]
    try:
        if int(pop_failures[failure_id]) == 0 or int(nonpop_failures[failure_id]) == 0:
            relative_values.append(0)
            sorted_values.append(0)
        else:
            sorted_values.append(nonpop_failures[failure_id]-pop_failures[failure_id])
            relative_values.append(1 - pop_failures[failure_id]/nonpop_failures[failure_id])
            global_loss_r_num += pop_failures[failure_id]
            global_loss_r_den += nonpop_failures[failure_id]
            avg += nonpop_failures[failure_id]-pop_failures[failure_id]
            print failure_id, pop_failures[failure_id], nonpop_failures[failure_id], pop_failures[failure_id]-nonpop_failures[failure_id]
    except:
        print "XXX", failure_id
        pass

avg /= len(pop_failures)
print "global loss reduction",  1 - global_loss_r_num/global_loss_r_den

for (ext_idx, (idx, data)) in enumerate(sorted(enumerate(sorted_values), key = lambda x: x[1], reverse=True)):
    print >> data_file, ext_idx, ",",\
         data, ",", relative_values[idx]

print >> gnuplot_file,\
"""
set term eps enhanced
set output "/tmp/absolute_failures.eps
set xlabel "Failed Node"
set ylabel "L_r"
set datafile separator ','
plot "%s" using 1:2 pt 7 ps 0.5 title columnhead, 0. w l lc 0 title "", %f w l lc 0 lt 5 title ""  

set output "/tmp/relative_failures.eps
set xlabel "Failed Node"
set ylabel "L_r"
set datafile separator ','
plot "%s" using 1:3 w lp title columnhead, 0. w l lc 0 title ""  """ % (data_file_name, avg, data_file_name)

data_file.close()
gnuplot_file.close()





