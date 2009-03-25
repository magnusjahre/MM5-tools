
import sys
import pbsconfig
import parsemethods

FAIRNESS = 0
AWS = 1
NO_METRIC = 2


def computeMetric(metric, sharedIPCs, aloneIPCs, np):
    
    speedups = [sharedIPCs[i] / aloneIPCs[i] for i in range(np)]
    
    if metric == NO_METRIC:
        return speedups
    elif metric == FAIRNESS:
        maxval = max(speedups)
        minval = min(speedups)
        return [minval/maxval]
    elif metric == AWS:
        sum = 0.0
        for s in speedups:
            sum += s
        return [sum]
    else:
        assert False



metrics = {"fairness": FAIRNESS,
           "AWS": AWS}

if len(sys.argv) > 4 or len(sys.argv) < 3:
    print 'Usage: python -c "import fairmha.getSpeedup" <np> <key> [<metric>]'
    sys.exit(-1)
    
np = int(sys.argv[1])
outkey = sys.argv[2] 

currentMetric = NO_METRIC
if len(sys.argv) == 4:
    if sys.argv[3] in metrics:
        currentMetric = metrics[sys.argv[3]]
    else:
        print
        print "Error: Invalid metric"
        print
        print "Alternatives are:"
        for m in metrics:
            print m
        print
        sys.exit(-1)

IPCSTR = "detailedCPU.*COM:IPC.*" 
    
files = parsemethods.getAllFilenames(pbsconfig, np)

results = {}

for wl in files:
    for key in files[wl]:
        
        sf, afs = files[wl][key]
        
        sharedIPCs = [0.0 for i in range(np)]
        sharedRes = parsemethods.findValues(IPCSTR, sf)
        for id in sharedRes:
            sharedIPCs[id] = sharedRes[id]
        
        aloneIPCs = [0.0 for i in range(np)]
        for i in range(np):
            aloneIPCs[i] = parsemethods.findValues(IPCSTR, afs[i])[0]
        
        curRes = computeMetric(currentMetric, sharedIPCs, aloneIPCs, np) 
        
        if wl not in results:
            results[wl] = {}
            
        assert key not in results[wl]
        results[wl][key] = curRes


sortedWls = results.keys()
sortedWls.sort()

sortedKeys = results[sortedWls[0]].keys()
sortedKeys.sort()

if outkey not in sortedKeys:
    print
    print "Error: Requested key not found"
    print
    print "The possible keys are:"
    for k in sortedKeys:
        print k
    print
    sys.exit(-1)
    

width = 20

if currentMetric == NO_METRIC:
    print "".ljust(width),
    for i in range(np):
        print ("CPU"+str(i)).rjust(width),
    print
    
    for w in sortedWls:
        print w.ljust(width),
        for i in range(np):
            print ("%.3f" % results[w][outkey][i]).rjust(width),
        print
        
else:
    print "".ljust(width),
    for k in sortedKeys:
        print k.rjust(width),
    print
    
    for w in sortedWls:
        print w.ljust(width),
        for k in sortedKeys:
            assert len(results[w][k]) == 1
            print ("%.3f" % results[w][k][0]).rjust(width),
        print    
        
