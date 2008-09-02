
import sys
import re

def getResult(r, array):
    value = int(r.split()[1])
    text = r.split()[0]
    cpuID = int(text.split("_")[3])
    array[cpuID] += value
    return array

def getInterference(filename, np, doPrint):

    file = open(filename)
    filetext = file.read()
    file.close()
    
    l2CapPattern = re.compile("L2Bank[0-9].cpu_capacity_interference_0-9].*")
    
    patterns = {
        "ic":re.compile("interconnect.cpu_interference_cycles_[0-9].*"),
        "l2BW": re.compile("L2Bank[0-9].cpu_interference_cycles_[0-9].*"),
        "l2cap": re.compile("L2Bank[0-9].cpu_extra_latency_[0-9].*"),
        "bus": re.compile("toMemBus.cpu_interference_bus_[0-9].*"),
        "busConflict": re.compile("toMemBus.cpu_interference_conflict_[0-9].*"),
        "busHtM": re.compile("toMemBus.cpu_interference_htm_[0-9].*"),
        "busBlocked": re.compile("toMemBus.blocking_interference_cycles_[0-9].*")
    }
    
    accessPatterns = {
        "misses": re.compile("L1[di]caches[0-9].overall_mshr_misses.*"),
        "lat": re.compile("L1[di]caches[0-9].overall_mshr_miss_latency.*")
    }
    
    totalInterference = [0 for i in range(np)]
    
    for p in patterns:
        res = patterns[p].findall(filetext)
        for r in res:
            totalInterference = getResult(r, totalInterference)
    
    mshrMissTotLat = [0 for i in range(np)]
    mshrMisses = [0 for i in range(np)]
    numWbs = [0 for i in range(np)]
    numMSHRHits = [0 for i in range(np)]
    for p in accessPatterns:
        res = accessPatterns[p].findall(filetext)
        for r in res:
            value = float(r.split()[1])
            text = r.split()[0]
            cpuID = int(text[9])
            if p == "misses":
                mshrMisses[cpuID] += value
            elif p == "lat":
                mshrMissTotLat[cpuID] += value
            else:
                assert False
    
    avgInterference = [float(totalInterference[i])/mshrMisses[i] for i in range(np)]
    avgLat = [mshrMissTotLat[i]/mshrMisses[i] for i in range(np)]
    
    if doPrint:
        print
        print "Interference summary for file "+filename
        print
        print "Interference:"
        for i in range(np):
            print "CPU "+str(i)+": "+str(totalInterference[i])+", "+str(avgInterference[i])+" per req ("+str(mshrMisses[i])+" reqs)"
        print
        print "Average latencies"
        for i in range(np):
            print "CPU "+str(i)+": "+str(avgLat[i])+", "+str(mshrMisses[i])+" requests"
        print
        
    return (avgInterference, avgLat)
    
def printError(sharedfile, alonefiles, np):
    
    shared = getInterference(sharedfile, np, False)
    errs = []
    cpuID = 0
    for a in alonefiles:
        alone = float(getInterference(a, 1, False)[1][0])
        errs.append(( (alone+shared[0][cpuID]) / float(shared[1][cpuID]) )-1)
        cpuID += 1
    
    i=0
    for e in errs:
        print "CPU"+str(i)+str(round(e*100, 2)).rjust(20)+" %"
        i+=1
