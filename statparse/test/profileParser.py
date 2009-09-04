#!/usr/bin/python

from statparse.statfileParser import StatfileIndex
import cProfile
import pstats

print
print "Generating execution profile by parsing mock 8-core statfiles"
print 

np = 8
workloadIDs = range(1,21)
wlBase = "fair"

workloads = []
for w in workloadIDs:
    if w < 10:
        workloads.append(wlBase+"0"+str(w))
    else:
        workloads.append(wlBase+str(w))

params = {}

filepath = "/home/jahre/workspace/m5sim-tools/statparse/test/"
statfile = filepath+"fair19-8-stats.txt"
dumporderfile = filepath+"statsDumpOrder.txt"
      
index = StatfileIndex()

def addFile():
    for wl in workloads:
        index.addFile(statfile, dumporderfile, np, wl, params)

cProfile.run("addFile()", "parseprofile")

stats = pstats.Stats("parseprofile")
stats.sort_stats("time").print_stats()
