
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


    useBusShadow = True
    printInterferenceBreakdown = True

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
        #"misses": re.compile("L1[di]caches[0-9].overall_mshr_misses.*"),
        #"lat": re.compile("L1[di]caches[0-9].overall_mshr_miss_latency.*")
        "misses": re.compile("L1[di]caches[0-9].num_roundtrip_responses.*"),
        "lat": re.compile("L1[di]caches[0-9].sum_roundtrip_latency.*")
    }
    
    totalInterference = [0 for i in range(np)]
    

    allInterference = {}

    for p in patterns:
        res = patterns[p][0].findall(filetext)
        tmpInterference = [0 for i in range(np)]
        for r in res:
            totalInterference = getResult(r, totalInterference, patterns[p][1])
            tmpInterference = getResult(r, tmpInterference, patterns[p][1])
        
        allInterference[p] = tmpInterference
    
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
        
        if printInterferenceBreakdown and np > 1:
            breakdownWidth = 15
            print "Interference breakdown (per request):"
            print "".ljust(breakdownWidth),
            for i in range(np):
                print ("CPU"+str(i)).rjust(breakdownWidth),
            print
            for p in allInterference:
                print p.ljust(breakdownWidth),
                for i in range(np):

                    intPerReq = int(float(allInterference[p][i]) / mshrMisses[i])

                    print str(intPerReq).rjust(breakdownWidth),
                print
            print
                    


    return (avgInterference, avgLat)
    
def printError(sharedfile, alonefiles, np):
    
    shared = getInterference(sharedfile, np, False)
    errs = []
    cpuID = 0
    for a in alonefiles:
        alone = float(getInterference(a, 1, False)[1][0])
        errs.append(( (float(shared[1][cpuID])-shared[0][cpuID]) / alone)-1)
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

        estimatedLatency = avgSharedLat - avgInterference
        error = ((estimatedLatency - aloneLat) / aloneLat)

        if printOutput:
            print sStats[0].ljust(10)+(str(error*100)+" %").rjust(15)

        #data.append([int(sStats[0]), avgSharedLat - avgInterference, aloneLat])
        data.append([int(sStats[0]), error])

    return data

def getAverageSampleError(sharedfile, alonefile):
    data = getSampleErrors(sharedfile, alonefile, False)

    sum = 0.0
    count = 0
    for tick, value in data:
        sum += value
        count += 1

    return sum / float(count)
        

def getBusErrorEstimate(sharedFile, aloneFile, sharedCPUID):

    sharedPatterns = []
    sharedPatterns.append(re.compile("avg_estimated_private_queue_latency_"+str(sharedCPUID)+".*"))
    sharedPatterns.append(re.compile("avg_predicted_service_latency_"+str(sharedCPUID)+".*"))
    sharedPatterns.append(re.compile("service_latency_requests_"+str(sharedCPUID)+".*"))

    file = open(sharedFile)
    sharedText = file.read()
    file.close()

    sharedVals = []
    for sp in sharedPatterns:
        res = sp.findall(sharedText)
        assert len(res) == 1
        sharedVals.append(float(res[0].split()[1]))

    alonePatterns= []
    alonePatterns.append(re.compile("avg_actual_queue_delay.*"))
    alonePatterns.append(re.compile("avg_actual_service_latency.*"))
    alonePatterns.append(re.compile("actual_service_latency_requests.*"))

    file = open(aloneFile)
    aloneText = file.read()
    file.close()

    aloneVals = []
    for sp in alonePatterns:
        res = sp.findall(aloneText)
        assert len(res) == 1
        aloneVals.append(float(res[0].split()[1]))


    queueError = "NaN"
    try:
        queueError = int(((aloneVals[0] - sharedVals[0]) / sharedVals[0]) * 100)
    except:
        pass

    serviceError = "NaN"
    try:
        serviceError = int(((aloneVals[1] - sharedVals[1]) / sharedVals[1]) * 100)
    except:
        pass

    w = 20
    print "".ljust(w),
    print "Estimate".rjust(w),
    print "Measure".rjust(w),
    print "Error (%)".rjust(w)

    print "Queue latency:".ljust(w),
    print str(sharedVals[0]).rjust(w),
    print str(aloneVals[0]).rjust(w),
    print str(queueError).rjust(w)

    print "Service latency:".ljust(w),
    print str(sharedVals[1]).rjust(w),
    print str(aloneVals[1]).rjust(w),
    print str(serviceError).rjust(w)

    print
    print "Number of requests: "+str(int(aloneVals[2]))+" alone, "+str(int(sharedVals[2]))+" shared"
        
    
def printBusErrors(sharedFile, aloneFiles):
    
    print
    print "Bus Latency Estimation results"
    print
    for i in range(len(aloneFiles)):
        print "CPU "+str(i)+":"
        getBusErrorEstimate(sharedFile, aloneFiles[i], i)
        print
    
