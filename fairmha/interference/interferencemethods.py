
import sys
import re
import deterministic_fw_wls as fair_wls
import subprocess

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
    bms = getBmNames(fair_wls.workloads[np][wlNum], np)

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

    if printDiff:
        print
        print "Validating DRAM access estimation"
        print

    sharedFile = open(sharedTrace)
    sharedLines = sharedFile.readlines()
    sharedFile.close()

    sstats = {}
    for i in range(1,len(sharedLines)):
        sdata = sharedLines[i].split(";")
        posres = "-1"
        qr = "-1"
        qw = "-1"

        if len(sdata) > 8:
            posres = sdata[6].strip()
            qr = sdata[7].strip()
            qw = sdata[8].strip()
        
        if sdata[1] not in sstats:
            sstats[sdata[1]] = [(sdata[3], posres,qr,qw)]
        else:
            sstats[sdata[1]].append( (sdata[3], posres,qr,qw) )

    aloneFile = open(aloneTrace)
    aloneLines = aloneFile.readlines()
    aloneFile.close()

    astats = {}
    for i in range(1,len(aloneLines)):
        adata = aloneLines[i].split(";")
        if adata[1] not in astats:
            astats[adata[1]] = [adata[3]]
        else:
            astats[adata[1]].append(adata[3])
    
    saddrs = sstats.keys()
    saddrs.sort()

    correct = 0
    wrong = 0

    w = 20

    if printDiff:
        print "Result".ljust(w),
        print "Shared".ljust(w),
        print "Private".ljust(w),
        print "Address".ljust(w),
        print "Shared Hit Position".ljust(w),
        print "Priv Queued Reads".ljust(w),
        print "Priv Queued Writes".ljust(w)


    errorcounts = {
        "hit-conflict": 0,
        "hit-miss": 0,
        "miss-conflict": 0,
        "miss-hit": 0,
        "conflict-miss": 0,
        "conflict-hit": 0
        }

    corPosHist = {}
    errPosHist = {}

    for sa in saddrs:
        
        if sa in astats:

            sacc = sstats[sa]
            aacc = astats[sa]
        
            if len(sacc) != len(aacc):
                if printDiff:
                    print "Warning: Dropping accesses to addr "+str(sa)
                continue

            for i in range(len(sacc)):
                
                sRes,sHitPos,sQr,sQw = sacc[i]

                if sRes == aacc[i]:
                    if printDiff:
                        print "Correct".ljust(w),
                        print sRes.ljust(w),
                        print aacc[i].ljust(w),
                        print str(sa).ljust(w),
                        print sHitPos.ljust(w),
                        print sQr.ljust(w),
                        print sQw.ljust(w)
                    correct += 1

                    if sHitPos not in corPosHist:
                        corPosHist[sHitPos] = 0
                    corPosHist[sHitPos] += 1
                else:
                    if printDiff:

                        print "Error".ljust(w),
                        print sRes.ljust(w),
                        print aacc[i].ljust(w),
                        print str(sa).ljust(w),
                        print sHitPos.ljust(w),
                        print sQr.ljust(w),
                        print sQw.ljust(w)
                    wrong += 1

                    typeid = sRes+"-"+aacc[i]
                    errorcounts[typeid] += 1

                    if sHitPos not in errPosHist:
                        errPosHist[sHitPos] = 0
                    errPosHist[sHitPos] += 1
        else:
            if printDiff:
                print "Warning: no alone access to addr "+str(sa)+", dropping..."

    corStr = "%.2f"%(float(correct)/float(correct+wrong)*100)
    wrongStr = "%.2f"%(float(wrong)/float(correct+wrong)*100)


    if printDiff:
        print
        print "Bus estimation test results"
        print
        print "Correct: "+str(correct)+" "+corStr+"%"
        print "Wrong:   "+str(wrong)+" "+wrongStr+"%"
        print
        print "Error types"
        print
        for t in errorcounts:
            print t.ljust(15)+str(errorcounts[t]).rjust(5)


        file = open("posHist.txt", "w")

        file.write("Position".ljust(15))
        file.write("Correct".rjust(15))
        file.write("Wrong".rjust(15))
        file.write("\n")

        for i in range(max(len(corPosHist),len(errPosHist))):
            file.write(str(i).ljust(15))
            if str(i) in corPosHist:
                file.write(str(corPosHist[str(i)]).rjust(15))
            else:
                file.write("".rjust(15))

            if str(i) in errPosHist:
                file.write(str(errPosHist[str(i)]).rjust(15))
            else:
                file.write("".rjust(15))
            file.write("\n")

        file.flush()
        file.close()

    return corStr,wrongStr,errorcounts

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
        print "Bus Queue".rjust(w),
        print "Bus Service".rjust(w)

    alonesums = [0.0 for i in range(6)]
    estimatesums = [0.0 for i in range(6)]
    entries = [0.0 for i in range(6)]

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
        print "Bus Queue".rjust(w),
        print "Bus Service".rjust(w)
        
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
        for s in data[3:]:
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
                   "Bus Queue":    re.compile("L1.*sum_bus_queue_interference.*"),
                   "Bus Service":  re.compile("L1.*sum_bus_service_interference.*"),
                   "Total":        re.compile("L1.*sum_roundtrip_interference.*"),
                   "Requests":     re.compile("L1.*num_roundtrip_responses.*")}


    latpatterns = {"IC Entry":     re.compile("L1.*sum_ic_entry_latency.*"),
                   "IC Transfer":  re.compile("L1.*sum_ic_transfer_latency.*"),
                   "IC Delivery":  re.compile("L1.*sum_ic_delivery_latency.*"),
                   "Bus Entry":    re.compile("L1.*sum_bus_entry_latency.*"),
                   "Bus Queue":    re.compile("L1.*sum_bus_queue_latency.*"),
                   "Bus Service":  re.compile("L1.*sum_bus_service_latency.*"),
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
        return "%.2f"%( ((float(estimate) - float(correct)) / float(correct))*100 )
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

def getInterferenceErrors(sharedName, aloneNames, absError):
    
    slat,sint,alat = getInterferenceBreakdownError(sharedName, aloneNames, False)

    errors = {}

    keys = slat.keys()
    keys.sort()

    caches = slat[keys[0]].keys()
    caches.sort()

    areqs = [0 for i in range(len(aloneNames))]
    sreqs = [0 for i in range(len(aloneNames))]
    
    cpuidPattern = re.compile("[0-9]+$")
    for c in caches:
        cpuid = int(cpuidPattern.findall(c)[0])
        areqs[cpuid] += alat["Requests"][c]
        sreqs[cpuid] += slat["Requests"][c]

    tslats = {}
    tints = {}
    talats ={}

    for k in keys:
        if k != "Requests":
            tmpslats = [0 for i in range(len(aloneNames))]
            tmpints = [0 for i in range(len(aloneNames))]
            tmpalats = [0 for i in range(len(aloneNames))]

            # create latency sums
            for c in caches:
                cpuid = int(cpuidPattern.findall(c)[0])
                tmpslats[cpuid] += slat[k][c]
                tmpints[cpuid] += sint[k][c]
                tmpalats[cpuid] += alat[k][c]

            # create latency avereges
            for i in range(len(aloneNames)):
                tmpslats[i] = computeAverage(tmpslats[i], sreqs[i])
                tmpints[i] = computeAverage(tmpints[i], sreqs[i])
                tmpalats[i] = computeAverage(tmpalats[i], areqs[i])


            tslats[k] = tmpslats
            tints[k] = tmpints
            talats[k] = tmpalats
    
    errors = {}
    for k in keys:
        if k != "Requests":
            errors[k] = [0 for i in range(len(aloneNames))]
            for cpuid in range(len(aloneNames)):
                estimate = computeEstimate(tslats[k][cpuid], tints[k][cpuid])
                if absError:
                    errors[k][cpuid] = computeEstimate(estimate, talats[k][cpuid])
                else:
                    errors[k][cpuid] = computeError(estimate, talats[k][cpuid])
    
    return errors

def search(filename, pattern):
    file = open(filename)
    text = file.read()
    file.close()
    return pattern.findall(text)

def getPerCoreData(res,shared):
    key = -1
    keystr,valstr = res.split()[0:2]
    if shared:
        try:
            key = int(keystr.split(".")[1].split("_")[3])
        except:
            valstr = "-1"
    return key,int(valstr)


def getReadWriteCount(sFilename, aFilenames):
    
    # FIXME: this statistic is not in use, always returns 0
    # TODO: actually measure private read and writes
    accessPattern = re.compile("membus0.accesses_per_cpu.*")

    sdata = [0 for i in range(len(aFilenames))]
    sres = search(sFilename, accessPattern)
    for r in sres:
        key, val = getPerCoreData(r,True)
        if key != -1:
            sdata[key] = val
        
    adata = [0 for i in range(len(aFilenames))]
    i=0
    for i in range(len(aFilenames)):
        r = search(aFilenames[i],accessPattern)[0]
        key,val = getPerCoreData(r,False)
        adata[i] = val
        
    error = [computeError(sdata[i],adata[i]) for i in range(len(aFilenames))]
    return error
        
    
def computeInterferenceFromTrace(sharedfn, alonefn, printStats):
    
    sharedData = parseTraceFile(sharedfn)
    aloneData = parseTraceFile(alonefn)

    aNotSeen = 0
    sNotSeen = 0

    stats = {}

    if printStats:
        print
        print "Comparing files "+sharedfn+" and "+alonefn
        print
        print str(len(sharedData))+" shared keys"
        print str(len(aloneData))+" alone keys"
        print

    stats["orig-shared-keys"] = len(sharedData)
    stats["orig-alone-keys"] = len(aloneData)

    akeys = aloneData.keys()
    skeys = sharedData.keys()
    for ak in akeys:
        if ak not in sharedData:
            aNotSeen += 1
            del aloneData[ak]

    for sk in skeys:
        if sk not in aloneData:
            sNotSeen += 1
            del sharedData[sk]

    if printStats:
        print str(aNotSeen)+" alone requests not in shared"
        print str(sNotSeen)+" shared requests not in alone"
        print str(len(sharedData))+" shared reqs and "+str(len(aloneData))+" alone reqs left"
        print

    assert len(sharedData) == len(aloneData)

    stats["only-shared-keys"] = sNotSeen
    stats["only-alone-keys"] = aNotSeen
    stats["both-keys"] = len(sharedData)

    interference = {}

    sharedEntriesRemoved = 0
    aloneEntriesRemoved = 0
    entriesLeft = 0

    skeys = sharedData.keys()    
    for skey in skeys:
        assert skey in aloneData

        sStats = sharedData[skey]
        aStats = aloneData[skey]

        if len(sStats) != len(aStats):
            if len(aStats) > len(sStats):
                aloneEntriesRemoved += len(aStats) - len(sStats)
                del aStats[len(sStats):]
            else:
                sharedEntriesRemoved += len(sStats) - len(aStats)
                del sStats[len(aStats):]
            assert len(aStats) == len(sStats)
        entriesLeft += len(sStats)

        interference[skey] = []
        
        for i in range(len(sStats)):
            interference[skey].append(computeTraceInterference(sStats[i], aStats[i]))

    if printStats:
        print str(sharedEntriesRemoved)+" entries removed from shared"
        print str(aloneEntriesRemoved)+" entries removed from alone"
        print str(entriesLeft)+" entries in interference computation"
        print

    stats["shared-entries-removed"] = sharedEntriesRemoved
    stats["alone-entries-removed"] = aloneEntriesRemoved
    stats["entries-used"] = entriesLeft

    return (interference, stats)

def getTraceFileKey(addr, pc):
    #return str(addr)+"-"+str(pc)
    return str(addr)

def computeTraceInterference(sharedData, aloneData):
    
    interference = {}

    interference["ic-entry"] = sharedData["ic-entry"] - aloneData["ic-entry"] 
    interference["ic-transfer"] = sharedData["ic-transfer"] - aloneData["ic-transfer"] 
    interference["ic-delivery"] = sharedData["ic-delivery"] - aloneData["ic-delivery"]

    if sharedData["bus-transfer"] != 0 and aloneData["bus-transfer"] == 0:
        # shared cache miss -> cache interference
        interference["cache-capacity"] = sharedData["bus-entry"] + sharedData["bus-transfer"]
        interference["bus-entry"] = 0
        interference["bus-transfer"] = 0

    elif sharedData["bus-transfer"] != 0 and aloneData["bus-transfer"] != 0:
        # cache miss in both configurations -> bus interference
        interference["cache-capacity"] = 0
        interference["bus-entry"] = sharedData["bus-entry"] - aloneData["bus-entry"]
        interference["bus-transfer"] = sharedData["bus-transfer"] - aloneData["bus-transfer"]
        pass

    elif sharedData["bus-transfer"] == 0 and aloneData["bus-transfer"] != 0:
        print "Shared cache hit and alone miss is impossible (crap!), quitting"
        assert False

    else:
        # cache hit in both configs
        interference["cache-capacity"] = 0
        interference["bus-entry"] = 0
        interference["bus-transfer"] = 0

    return interference

def parseTraceFile(fname):

    data = {}

    print "Parsing file "+fname
    linecnt = 0

    f = open(fname)

    first = True
    for l in f:
        if first:
            first = False
            continue

        splitted = l.split(";")
        assert len(splitted) == 8
        addr = int(splitted[1])
        pc = int(splitted[2])
        key = getTraceFileKey(addr,pc)
        
        lats = {}
        lats["ic-entry"] = int(splitted[3]) 
        lats["ic-transfer"] = int(splitted[4]) 
        lats["ic-delivery"] = int(splitted[5]) 
        lats["bus-entry"] = int(splitted[6]) 
        lats["bus-transfer"] = int(splitted[7]) 
        lats["at-tick"] = int(splitted[0])

        if key not in data:
            data[key] = []

        data[key].append(lats)

        linecnt += 1
        if linecnt % 100000 == 0:
            print "Reading line "+str(linecnt)+" key count "+str(len(data))
    
    print "Finished parsing.."
    print

    f.close()

    return data

def createReqVsLatData(interference):
    
    data = {}
    keys = interference.keys()
    intTypes = interference[keys[0]][0].keys()

    for t in intTypes:
        data[t] = {}

    for key in interference:
        for entry in interference[key]:
            for itype in entry:
                intTicks = entry[itype]
                if intTicks not in data[itype]:
                    data[itype][intTicks] = 1
                else:
                    data[itype][intTicks] += 1

    return data

def parseInterferenceTraceExternal(sharedfn, privatefn, outputfn, statsfn, key):
    binary = "/home/jahre/m5sim/tools/fairmha/traceParse/traceparse"

    args = [binary]
    args.append(sharedfn) 
    args.append(privatefn)
    args.append(outputfn)
    args.append(statsfn)
    args.append(key)

    subprocess.call(args)

    readdata = {}
    first = True
    resfile = open(outputfn)
    for l in resfile:
        if first:
            first = False
            continue

        tmp = l.split()
        assert(len(tmp) == 7)

        interference = int(tmp[0])
        
        lats = {}
        lats["ic-entry"] = int(tmp[1]) 
        lats["ic-transfer"] = int(tmp[2]) 
        lats["ic-delivery"] = int(tmp[3]) 
        lats["bus-entry"] = int(tmp[4]) 
        lats["bus-transfer"] = int(tmp[5]) 
        lats["cache-capacity"] = int(tmp[6]) 

        readdata[interference] = lats

    resfile.close()
    
    data = {}
    for interference in readdata:
        for intType in readdata[interference]:
            if intType not in data:
                data[intType] = {}

            data[intType][interference] = readdata[interference][intType]

    return data
