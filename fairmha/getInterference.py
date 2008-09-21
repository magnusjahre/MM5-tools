
import sys
import re
import deterministic_fw_wls as fair_wls

def getResult(r, array, add):
    value = int(r.split()[1])
    text = r.split()[0]
    splitted = text.split("_")
    cpuID = int(splitted[len(splitted)-1])
    if add:
        array[cpuID] += value
    else:
        array[cpuID] -= value
    return array

def getInterference(filename, np, doPrint):


    useBusShadow = False

    file = open(filename)
    filetext = file.read()
    file.close()
    
    l2CapPattern = re.compile("L2Bank[0-9].cpu_capacity_interference_0-9].*")
    
    patterns = {
        "ic": [re.compile("interconnect.cpu_interference_cycles_[0-9].*"), True],
        "l2BW": [re.compile("L2Bank[0-9].cpu_interference_cycles_[0-9].*"), True],
        "l2cap": [re.compile("L2Bank[0-9].cpu_extra_latency_[0-9].*"), True],
        "busBlocked": [re.compile("toMemBus.blocking_interference_cycles_[0-9].*"), True]
    }

    if useBusShadow:
        patterns["bus"] = [re.compile("toMemBus.cpu_interference_bus_[0-9].*"), True]
        patterns["shadowBlocked"] = [re.compile("toMemBus.shadow_blocked_cycles_[0-9].*"), False]
    else:
        patterns["bus"] = [re.compile("toMemBus.estimated_interference_[0-9].*"), True]
        #TODO: Add bus private blocking estimate

    
    accessPatterns = {
        "misses": re.compile("L1[di]caches[0-9].overall_mshr_misses.*"),
        "lat": re.compile("L1[di]caches[0-9].overall_mshr_miss_latency.*")
    }
    
    totalInterference = [0 for i in range(np)]
    
    for p in patterns:
        res = patterns[p][0].findall(filetext)
        for r in res:
            totalInterference = getResult(r, totalInterference, patterns[p][1])
    
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
        errs.append(( (float(shared[1][cpuID])+shared[0][cpuID]) / alone)-1)
        cpuID += 1
    
    i=0
    for e in errs:
        print "CPU"+str(i)+str(round(e*100, 2)).rjust(20)+" %"
        i+=1

def getBmNames(wl,np):
    newWl = []
    i = 0
    for i in range(np):
        extra_fw = wl[1][i] - 1000000000
        id = extra_fw / 20000000
        newWl.append(wl[0][i]+str(id))
        id += 1
    return newWl


def getBenchmarks(wl, printRes, np):
    wlNum = int(wl.replace("fair",""))
    bms = getBmNames(fair_wls.workloads[wlNum], np)

    if printRes:
        for b in bms:
            print b+" ",
        print

    return bms
        
        
def getSampleErrors(sharedFilename, aloneFilename, printOutput):

    sf = open(sharedFilename)
    af = open(aloneFilename)
    
    sLines = sf.readlines()
    aLines = af.readlines()
    
    sf.close()
    af.close()

    data = []

    for i in range(len(sLines))[1:]:
        
        sStats = sLines[i].split(";")
        
        avgSharedLat = float(sStats[1])
        avgInterference = float(sStats[2])

        try:
            aloneLat = float(aLines[i].split(";")[1])
        except:
            break

        error = ((avgSharedLat - avgInterference) / aloneLat) - 1

        if printOutput:
            print sStats[0].ljust(10)+(str(error*100)+" %").rjust(15)

        data.append([int(sStats[0]), avgSharedLat - avgInterference, aloneLat])

    return data
        

    
