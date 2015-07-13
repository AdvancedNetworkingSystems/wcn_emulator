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
for failure_id in sorted(pop_failures.keys()):
    print >> data_file, failure_id, ",",\
     1-pop_failures[failure_id]/nonpop_failures[failure_id]

print >> gnuplot_file,\
"""
set term eps enhanced
set output "/tmp/plot.eps
set xlabel "Failed Node"
set ylabel "R"
set datafile separator ','
plot "%s" using 1:2 w lp title columnhead """ % data_file_name

data_file.close()
gnuplot_file.close()





