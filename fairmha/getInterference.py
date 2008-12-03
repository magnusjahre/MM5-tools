
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
    
    avgInterference = []
    for i in range(np):
        tmp = "NaN"
        try:
            tmp = float(totalInterference[i])/mshrMisses[i]
        except:
            pass
        avgInterference.append(tmp)


    avgLat = []
    for i in range(np):
        tmp = "NaN"
        try:
            tmp = mshrMissTotLat[i]/mshrMisses[i] 
        except:
            pass
        avgLat.append(tmp)
    
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
                    


    return (avgInterference, avgLat, mshrMisses)
    
def printError(sharedfile, alonefiles, np):
    
    shared = getInterference(sharedfile, np, False)
    errs = []
    cpuID = 0
    for a in alonefiles:
        alone = float(getInterference(a, 1, False)[1][0])
        
        estimate = float(shared[1][cpuID])-shared[0][cpuID]
        error = (estimate / alone)-1

        errs.append( (error, estimate, alone) )
        cpuID += 1
    
    i=0
    w = 15
    print "".ljust(w),
    print "Error".rjust(w),
    print "Requests".rjust(w),
    print "Estimate".rjust(w),
    print "Alone".rjust(w)
    
    for e,s,a in errs:
        print ("CPU"+str(i)).ljust(w),
        print (str(round(e*100, 2))+" %").rjust(w),
        print str(shared[2][i]).rjust(w),
        print str(int(s)).rjust(w),
        print str(int(a)).rjust(w)
        i+=1

def printCommitOnceErrors(sharedFile, alonefiles):
    
    latPattern = re.compile("L1.caches..avg_roundtrip_latency.*")
    intPattern = re.compile("L1.caches..avg_roundtrip_interference.*")
    reqPattern = re.compile("L1.caches..num_roundtrip_responses.*")

    sfile = open(sharedFile)
    sharedtext = sfile.read()
    sfile.close()
    slatstrs = latPattern.findall(sharedtext)
    sintstrs = intPattern.findall(sharedtext)
    sreqstrs = reqPattern.findall(sharedtext)

    blackCnt = 25

    blacklist = {}
    for r in sreqstrs:
        keystr,reqstr = r.split()[0:2]
        key = keystr.split('.')[0]
        blacklist[key] =  int(reqstr) < blackCnt

    slats = {}
    for sl in slatstrs:
        keystr,latstr = sl.split()[0:2]
        try:
            slats[keystr.split('.')[0]] = float(latstr)
        except:
            slats[keystr.split('.')[0]] = "N/A"

    sints = {}
    for sl in sintstrs:
        keystr,latstr = sl.split()[0:2]
        try:
            sints[keystr.split('.')[0]] = float(latstr)
        except:
            sints[keystr.split('.')[0]] = "N/A"

    estimates = {}
    for cache in slats:
        assert cache in sints
        try:
            estimates[cache] = slats[cache] - sints[cache]
        except:
            estimates[cache] = "N/A"

    
    alats = {}
    for i in range(len(alonefiles)):
        afile = open(alonefiles[i])
        alatstr = latPattern.findall(afile.read())
        afile.close()
        
        for d in alatstr:
            keystr,latstr = d.split()[0:2]
            key = keystr.split('.')[0] 
            try:
                alats[key[:len(key)-1]+str(i)] = float(latstr)
            except:
                alats[key[:len(key)-1]+str(i)] = "N/A"
        
    errors = {}
    for c in estimates:
        assert c in alats
        try:
            errors[c] = str(int(((estimates[c] - alats[c]) / alats[c]) * 100))+" %"
        except:
            errors[c] = "N/A"

    print
    print "Errors when interference and latency are added simultaneously:"
    print

    w = 20
    print "Cache".ljust(w),
    print "Estimate".rjust(w),
    print "Alone".rjust(w),
    print "Error".rjust(w)

    keys = estimates.keys()
    keys.sort()

    for c in keys:
        print c.ljust(w),
        print str(estimates[c]).rjust(w),
        print str(alats[c]).rjust(w),
        if blacklist[c]:
            print str("TFR").rjust(w)
        else:
            print str(errors[c]).rjust(w)

    print
        
        


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
    sharedPatterns.append(re.compile("per_cpu_entry_avg_delay_"+str(sharedCPUID)+".*"))
    sharedPatterns.append(re.compile("toMemBus.blocking_interference_cycles_"+str(sharedCPUID)+".*"))

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
    alonePatterns.append(re.compile("per_cpu_entry_avg_delay.*"))

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
        queueError = int(((sharedVals[0] - aloneVals[0]) / aloneVals[0]) * 100)
    except:
        pass

    serviceError = "NaN"
    try:
        serviceError = int(((sharedVals[1] - aloneVals[1]) / aloneVals[1]) * 100)
    except:
        pass

    blockingError = "NaN"
    sharedBlockingInterference = sharedVals[4] / sharedVals[2]
    estimatedAloneBlocking = sharedVals[3] - sharedBlockingInterference

    try:
        blockingError = int(((estimatedAloneBlocking - aloneVals[3]) / aloneVals[3]) * 100)
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

    print "Bus blocking:".ljust(w),
    print str(estimatedAloneBlocking).rjust(w),
    print str(aloneVals[3]).rjust(w),
    print str(blockingError).rjust(w)

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

def getCrossbarError(sharedFile, aloneFile, sharedID):
    sipattern = re.compile("interconnect.cpu_interference_cycles_"+str(sharedID)+".*")
    sdpattern = re.compile("interconnect.cpu_total_delay_cycles_"+str(sharedID)+".*")
    srpattern = re.compile("interconnect.cpu_total_delay_requests_"+str(sharedID)+".*")

    adpattern = re.compile("interconnect.cpu_total_delay_cycles.*")
    arpattern = re.compile("interconnect.cpu_total_delay_requests.*")
    aepattern = re.compile("interconnect.avg_read_delay_before_entry.*")
    
    siepattern = re.compile("interconnect.cpu_entry_interference_cycles_"+str(sharedID)+".*")
    sitpattern = re.compile("interconnect.cpu_transfer_interference_cycles_"+str(sharedID)+".*")
    sidpattern = re.compile("interconnect.cpu_delivery_interference_cycles_"+str(sharedID)+".*")
    
    sfile = open(sharedFile)
    sdata = sfile.read()
    sfile.close()

    afile = open(aloneFile)
    adata = afile.read()
    afile.close()

    interference = float(sipattern.findall(sdata)[0].split()[1])
    shared_latency = float(sdpattern.findall(sdata)[0].split()[1])
    shared_requests = float(srpattern.findall(sdata)[0].split()[1])

    entry_int = float(siepattern.findall(sdata)[0].split()[1])
    transfer_int = float(sitpattern.findall(sdata)[0].split()[1])
    delivery_int = float(sidpattern.findall(sdata)[0].split()[1])

    alone_latency = float(adpattern.findall(adata)[0].split()[1])
    alone_entry_avg = float(aepattern.findall(adata)[0].split()[1])
    alone_requests = float(arpattern.findall(adata)[0].split()[1])

    alone_avg = (alone_latency / alone_requests) + alone_entry_avg
    estimate = (shared_latency / shared_requests) - (interference / shared_requests) 

    error = ((estimate - alone_avg) / alone_avg) * 100

    w = 20
    print "".ljust(w),
    print "Estimate".rjust(w),
    print "Measure".rjust(w),
    print "Error (%)".rjust(w)

    print "Total:".ljust(w),
    print str(estimate).rjust(w),
    print str(alone_avg).rjust(w),
    print str(error).rjust(w)

    print
    print "Interference breakdown: "+str(entry_int)+" entry, "+str(transfer_int)+" transfer, "+str(delivery_int)+" delivery"

    print
    print "Number of requests: "+str(int(alone_requests))+" alone, "+str(int(shared_requests))+" shared"

def printCrossbarErrors(sharedFile, aloneFiles):

    print
    print "Crossbar Latency Estimation results"
    print
    for i in range(len(aloneFiles)):
        print "CPU "+str(i)+":"
        getCrossbarError(sharedFile, aloneFiles[i], i)
        print
    


def compareBusAccessTraces(sharedTrace, aloneTrace, printDiff):

    print
    print "Validating DRAM access estimation"
    print

    sharedFile = open(sharedTrace)
    sharedLines = sharedFile.readlines()
    sharedFile.close()

    aloneFile = open(aloneTrace)
    aloneLines = aloneFile.readlines()
    aloneFile.close()

    errors = 0.0
    correct = 0.0
    not_cnt = 0.0
    for i in range(len(sharedLines)):
        sdata = sharedLines[i].split(";")
        adata = aloneLines[i].split(";")

        if(sdata[1] != adata[1]):
            if printDiff:
                print sdata[0]+": NOTE, saw different addresses, alone "+adata[1]+" ("+adata[4].strip()+"), shared "+sdata[1]+" ("+sdata[4].strip()+")"
            not_cnt += 1.0

        if sdata[3] == adata[3]:
            print sdata[0]+": correctly estimated "+sdata[3]
            correct += 1.0
        else:
            print sdata[0]+": ERROR, estimated "+sdata[3]+", access was "+adata[3]
            errors += 1.0

    print
    print "Validation stats"
    print
    try:
        print str(correct)+" requests correct ("+str(int((correct/(correct+errors)*100)))+" %)"
    except:
        pass
    try:
        print str(errors)+" requests wrong ("+str(int((errors/(correct+errors)*100)))+" %)"
    except:
        pass
    try:
        print str(not_cnt)+" requests not counted ("+str(int((not_cnt/(correct+errors)*100)))+" %)"
    except:
        pass

def evaluateRequestEstimates(sharedlatency, interference, alonelatency, doPrint):
    
    evalData = {}

    if doPrint:
        print
        print "Evaluating request estimates, reading files..."
        print

    readRequestEstimateFile(sharedlatency, evalData, "slat")
    readRequestEstimateFile(interference, evalData, "sint")
    readRequestEstimateFile(alonelatency, evalData, "alat")

    # check integrity of results
    reqMismatch = 0
    for a in evalData:
        prevSharedTick = 0
        prevAloneTick = 0
        for d in evalData[a]:
            
            if "slat" in d:
                assert d["slat"][1] == d["sint"][1]
                assert prevSharedTick < d["slat"][1]
                prevSharedTick = d["slat"][1]
            else:
                reqMismatch += 1
            
            if "alat" in d:
                assert prevAloneTick < d["alat"][1]
                prevAloneTick = d["alat"][1]
            else:
                reqMismatch += 1

    if reqMismatch > 0:
        if doPrint:
            print "WARNINING: the samples was off by "+str(reqMismatch)+" requests:"

        dropAddrs = []
        for a in evalData:
            index = 0
            for d in evalData[a]:
                if not ("slat" in d and "alat" in d):
                    if doPrint:
                        print "Removing entry "+str(a)+", index "+str(index)+": "+str(evalData[a][index])
                    if a not in dropAddrs:
                        dropAddrs.append( (a, index))
                index += 1

        for a,index in dropAddrs:
            evalData[a][index] = {}

        if doPrint:
            print

    w = 20
    if doPrint:
        print "Addr".ljust(w),
        print "IC Entry".rjust(w),
        print "IC Transfer".rjust(w),
        print "IC Delivery".rjust(w),
        print "Bus Entry".rjust(w),
        print "Bus Transfer".rjust(w)

    alonesums = [0.0 for i in range(5)]
    estimatesums = [0.0 for i in range(5)]
    entries = [0.0 for i in range(5)]

    if doPrint:
        print
        print "Measurement errors (in cycles, estimate / actual) for all reqs"
        print

    evalEntries = 0
    for a in evalData:
        for d in evalData[a]:

            if d != {}:
                evalEntries += 1
                numEntries = len(d["slat"][0])
                estimate = [0 for i in range(numEntries)]
             
                for i in range(numEntries):
                    estimate[i] = d["slat"][0][i] - d["sint"][0][i]
                
                errs = [0.0 for i in range(numEntries)]
                output = ["" for i in range(numEntries)]
                for i in range(numEntries):
                    output[i] = str(estimate[i])+" / "+str(d["alat"][0][i])
                    
                    alonesums[i] += d["alat"][0][i]
                    estimatesums[i] += estimate[i]

                    if d["alat"][0][i] != 0:
                        entries[i] += 1.0

                if doPrint:
                    print str(a).ljust(w),
                    for e in output:
                        print str(e).rjust(w),
                    print

    if doPrint:
        print
        print "Average errors:"
        print
        print "".ljust(w),
        print "IC Entry".rjust(w),
        print "IC Transfer".rjust(w),
        print "IC Delivery".rjust(w),
        print "Bus Entry".rjust(w),
        print "Bus Transfer".rjust(w)
        
        print "Per int value".ljust(w),
        for i in range(len(alonesums)):
            if entries[i] != 0.0:
                aavg = str(int(alonesums[i] / entries[i]))
                eavg = str(int(estimatesums[i] / entries[i]))
                
                print (eavg+" / "+aavg).rjust(w),
            else:
                print "NaN".rjust(w),
        
        print
        print "Per request".ljust(w),
        for i in range(len(alonesums)):
            aavg = str(int(alonesums[i] / float(evalEntries)))
            eavg = str(int(estimatesums[i] / float(evalEntries)))
                
            print (eavg+" / "+aavg).rjust(w),
        print
        print
        
             


def readRequestEstimateFile(filename, resultstorage, key):

    rfile = open(filename)
    filedata = rfile.readlines()
    rfile.close

    for l in filedata[1:]:
        data = l.split(";")
        tick = int(data[0])
        addr = int(data[1])

        values = []
        for s in data[2:]:
            values.append(int(s))

        if addr not in resultstorage:
            resultstorage[addr] = [{}]


        added = False
        for entry in resultstorage[addr]:
            if key not in entry:
                added = True
                entry[key] = (values, tick)
                break

        if not added:
            resultstorage[addr].append({key: (values, tick)})


def getInterferenceBreakdownError(sharedfilen, alonefilens, doPrint):
    
    intpatterns = {"IC Entry":     re.compile("L1.*sum_ic_entry_interference.*"),
                   "IC Transfer":  re.compile("L1.*sum_ic_transfer_interference.*"),
                   "IC Delivery":  re.compile("L1.*sum_ic_delivery_interference.*"),
                   "Bus Entry":    re.compile("L1.*sum_bus_entry_interference.*"),
                   "Bus Transfer": re.compile("L1.*sum_bus_transfer_interference.*"),
                   "Total":        re.compile("L1.*sum_roundtrip_interference.*"),
                   "Requests":     re.compile("L1.*num_roundtrip_responses.*")}


    latpatterns = {"IC Entry":     re.compile("L1.*sum_ic_entry_latency.*"),
                   "IC Transfer":  re.compile("L1.*sum_ic_transfer_latency.*"),
                   "IC Delivery":  re.compile("L1.*sum_ic_delivery_latency.*"),
                   "Bus Entry":    re.compile("L1.*sum_bus_entry_latency.*"),
                   "Bus Transfer": re.compile("L1.*sum_bus_transfer_latency.*"),
                   "Total":        re.compile("L1.*sum_roundtrip_latency.*"),
                   "Requests":     re.compile("L1.*num_roundtrip_responses.*")}

    sfile = open(sharedfilen)
    stext = sfile.read()
    sfile.close()

    sint = addBreakdownPatterns({}, intpatterns, stext, -1)
    slat = addBreakdownPatterns({}, latpatterns, stext, -1)

    alat = {}
    cpu_num = 0
    for afn in alonefilens:
        afile = open(afn)
        atext = afile.read()
        afile.close()
        
        alat = addBreakdownPatterns(alat, latpatterns, atext, cpu_num)
        
        cpu_num += 1

    results = [slat, sint, alat]

    if doPrint:
        printBreakdownError(results, len(alonefilens))

    return results

def addBreakdownPatterns(data, patterns, text, cpu_num):
    
    for p in patterns:
        res = patterns[p].findall(text)
        
        if p not in data:
            data[p] = {}
        
        for r in res:
            rsplit = r.split()
            rkey = rsplit[0].split(".")[0]
            if cpu_num != -1:
                rkey = rkey.replace("0", str(cpu_num))
            rdata = int(rsplit[1])
            data[p][rkey] = rdata

    return data


def printBreakdownError(results, np):
    slat, sint, alat = results

    print
    print "Interference Summary"
    print

    width = 20
    cpuidPattern = re.compile("[0-9]+$")

    types = slat.keys()
    caches = slat[types[0]].keys()
    types.sort()
    caches.sort()

    avgres = [[] for i in range(np)]

    # Print per cache stats with subtotal
    for cache in caches:
            
        print "Interference stats for "+cache
        print
        
        
        print "".ljust(width),
        print "Shared lat".rjust(width),
        print "Shared int".rjust(width),
        print "Alone".rjust(width),
        print "Estimate".rjust(width),
        print "Error (%)".rjust(width)

        sreqs = slat["Requests"][cache]
        areqs = alat["Requests"][cache]

        for t in types:
            if t != "Requests":
                
                avgslat = computeAverage(slat[t][cache], sreqs)
                avgsint = computeAverage(sint[t][cache], sreqs)
                avgalat = computeAverage(alat[t][cache], areqs)
                estimate = computeEstimate(avgslat, avgsint)
                error = computeError(estimate, avgalat)
                
                if t == "Total":
                    cpuid = int(cpuidPattern.findall(cache)[0])
                    avgres[cpuid].append([avgslat, avgsint, avgalat, estimate, error, sreqs, areqs])

                print t.ljust(width),
                print str(avgslat).rjust(width),
                print str(avgsint).rjust(width),
                print str(avgalat).rjust(width),
                print str(estimate).rjust(width),
                print str(error).rjust(width)
                
        print

    print
    print "Requests counts: "
    print
    print "".ljust(width),
    print "Shared".rjust(width),
    print "Alone".rjust(width)
    
    for i in range(np):
        print ("CPU"+str(i)).ljust(width),
        print str(avgres[i][0][5] + avgres[i][1][5]).rjust(width),
        print str(avgres[i][0][6] + avgres[i][1][6]).rjust(width)

        
    # Print total system summary
    print
    print "Total interference summary"
    print
    
    print "".ljust(width),
    print "Shared lat".rjust(width),
    print "Shared int".rjust(width),
    print "Alone".rjust(width),
    print "Estimate".rjust(width),
    print "Error (%)".rjust(width)

    reqCntLimit = 25
    cntToLow = False

    for i in range(np):
        if (avgres[i][0][5]+avgres[i][1][5]) < reqCntLimit:
            print ("CPU"+str(i)+"*").ljust(width),
            cntToLow = True
        else:
            print ("CPU"+str(i)).ljust(width),
        print str(computeWeightedAvg(avgres, i, 0)).rjust(width),
        print str(computeWeightedAvg(avgres, i, 1)).rjust(width),
        print str(computeWeightedAvg(avgres, i, 2)).rjust(width),
        print str(computeWeightedAvg(avgres, i, 3)).rjust(width),
        print str(computeWeightedAvg(avgres, i, 4)).rjust(width)

    if cntToLow:
        print
        print "* - The number of requests is less than the threshold of "+str(reqCntLimit)
    print
    
    

def computeAverage(sum, num):
    if num != 0:
        return int(float(sum) / float(num))
    return "NaN"

def computeError(estimate, correct):
    if correct != 0 and estimate != "NaN":
        return int(((float(estimate) - float(correct)) / float(correct))*100)
    elif correct == 0 and estimate == 0:
        return 0
    return "NaN"

def computeEstimate(lat, int):
    if lat != "NaN" and int != "NaN":
        return lat - int
    return "NaN"

def computeWeightedAvg(avgres, cpuid, testnum):

    data = []
    for d in avgres[cpuid]:
        data.append( (d[5] ,d[testnum]) )

    tw = 0
    for w,num in data:
        tw += w

    avg = 0.0
    for w,num in data:
        if num != "NaN":
            avg += (float(w)/float(tw)) * float(num)
        else:
            assert w == 0
    
    return int(avg)

