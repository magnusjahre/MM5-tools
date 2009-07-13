#!/usr/bin/python

import sys

try:
    tracefilename = sys.argv[1]
    valsInAvg = int(sys.argv[2])
    separator = sys.argv[3]
except:
    print "Usage: compressTrace.py [tracefile] [values in average] [separator]" 
    sys.exit(-1)

trace = open(tracefilename)

first = True
avgcnt = 0
sumstorage = []
for line in trace:
    
    if first:
        print line,
        first = False
        continue
    
    splitted = line.split(separator)
    
    if avgcnt == 0:
        sumstorage = [0.0 for i in range(len(splitted))]
        
    for i in range(len(splitted)):
        sumstorage[i] += float(splitted[i])
    
    if avgcnt == valsInAvg:
        
        assert len(sumstorage) > 0
        sys.stdout.write("%.2f" % (sumstorage[0] / float(valsInAvg)))
        for v in sumstorage[1:]:
            sys.stdout.write(separator+"%.2f" % (v / float(valsInAvg)))
        print
            
        avgcnt = 0
    else:
        avgcnt += 1 
    
trace.close()
