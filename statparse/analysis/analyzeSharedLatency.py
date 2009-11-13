#!/usr/bin/env python

from optparse import OptionParser

import statparse.experimentConfiguration as expconfig
import statparse.experimentConfiguration as experimentConfiguration

from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
from statparse import processResults
from statparse.analysis import computeMean, computeRMS, computeStddev
import deterministic_fw_wls

import os
import sys

import copy

indexmodulename = "index-all"

numBanks = 4

class ResultPattern:
    
    def __init__(self, name, basepattern, **kwargs):
        self.name = name
        self.basepattern = basepattern
        
        if "vector" in kwargs:
            self.vectorRange = kwargs["vector"]
        else:
            self.vectorRange = -1

    def retrievePatterns(self, results, cpuID):
        
        searchPatterns = [self.basepattern]
        if self.basepattern.startswith("PrivateL2Cache."):
            searchPatterns = [self.basepattern.replace("PrivateL2Cache.", "PrivateL2Cache"+str(cpuID))]
        
        aggregateSize = -1
        if self.basepattern.startswith("SharedCache."):
            searchPatterns = []
            aggregateSize = numBanks
            for i in range(numBanks):
                searchPatterns.append( self.basepattern.replace("SharedCache.", "SharedCache"+str(i)) )
        
        retvals = []
        for searchPattern in searchPatterns:
            values = []
            if self.vectorRange != -1:
                for i in range(self.vectorRange):
                    values.append(float(results[searchPattern+"_"+str(i)]))
            else:
                values.append(float(results[searchPattern]))
            retvals.append(values)
        
        if len(retvals) == 1:
            return retvals[0]
        
        aggregateRetval = [0 for i in range(aggregateSize)]
        for l in retvals:
            for i in range(aggregateSize):
                aggregateRetval[i] += l[i]
        
        return aggregateRetval
                
        

allPatterns = [ResultPattern("intManRequests", "interferenceManager.requests", vector=4),
               ResultPattern("avgMLP","PrivateL2Cache..mq.avg_mlp_estimation", vector=17),
               ResultPattern("avgBusService", "membus0.avg_service_cycles"),
               ResultPattern("busTotalReqs", "membus0.total_requests"),
               ResultPattern("ticks", "sim_ticks"),
               ResultPattern("avgBusQueueInt", "interferenceManager.avg_interference_bus_queue", vector=4),
               ResultPattern("avgBusQueueLat", "interferenceManager.avg_latency_bus_queue", vector=4),
               ResultPattern("avgBusServiceLat", "interferenceManager.avg_latency_bus_service", vector=4),
               ResultPattern("sharedCacheMisses", "SharedCache..misses_per_cpu", vector=4),
               ResultPattern("sharedCacheAccesses", "SharedCache..accesses_per_cpu", vector=4)]



printstats = ["bus-queue", "request-intensity", "request-dist"]

def parseArgs():
    parser = OptionParser(usage="analyzeBusLatency.py [options] np")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--parameters", action="store", dest="parameters", type="string", default="", help="Only print configs matching key and value. Format: key1,val1:key2,val2:...")
    parser.add_option("--benchmark", action="store", dest="benchmark", type="string", default="", help="Only show results for this benchmark")
    parser.add_option("--workload", action="store", dest="workload", type="string", default="", help="Only show results for this workload")
    parser.add_option("--print-values", action="store_true", dest="printValues", default=False, help="Print values in addition to error")
    parser.add_option("--queue-model-cutoff", action="store", dest="queueModelCutoff", type="float", default=0.001, help="Assume that benchmarks with a lower request intensity than this cutoff cannot increase their request intensity")
    parser.add_option("--error-filter", action="store", dest="errorFilter", type="float", default=0.0, help="Only show results with an absolute error larger than this parameter (in percent)")

    opts, args = parser.parse_args()

    if len(args) != 1:
        print "Command line error..."
        print "Usage : "+parser.usage
        sys.exit(-1)

    params = {}
    if opts.parameters != "":
        try:
            params, spec = experimentConfiguration.parseParameterString(opts.parameters)
        except Exception as e:
            print "Parameter parse error: "+str(e.args[0])
            sys.exit(-1)

    return opts,args,params

def fatal(message):
    print >> sys.stderr, "Fatal: "+message
    sys.exit(-1)

def doSearch(results, np, opts):
    
    patterns = []
    for p in allPatterns:
        patterns.append(p.basepattern)
    
    searchRes = results.searchForPatterns(patterns) 
    return processResults.invertSearchResults(searchRes)

def retrievePatterns(config, results, np):
    
    patternResults = {}
    
    cpuID = expconfig.findCPUID(config.workload, config.benchmark, np)
    
    for pattern in allPatterns:
        
        assert pattern not in patternResults
        patternResults[pattern.name] = {}
        
        patternResults[pattern.name] = pattern.retrievePatterns(results[config], cpuID)  
    
    return patternResults

def createMHAOrder(): 
    maxMSHRs = 16
    MSHROptions = [1,2,4,8]
    
    mhaConfigs = []
    for i in range(4):
        for MSHROpt in MSHROptions:
            tmpMHA = [0 for k in range(4)]
            for j in range(4):
                if j != i:
                    tmpMHA[j] = maxMSHRs
                else:
                    tmpMHA[j] = MSHROpt
        
            mhaConfigs.append(tmpMHA)
        
    mhaStrings = []
    for c in mhaConfigs:
        tmpStr = str(c[0])
        for v in c[1:]:
            tmpStr += ","+str(v)
        mhaStrings.append(tmpStr)
    
    return mhaStrings


def analyzeBusLatency(results, np, opts):
    
    baselineKey = "16,16,16,16"
    
    filterConfig = expconfig.buildMatchAllConfig()
    filterConfig.parameters = {"STATICASYMMETRICMHA": baselineKey}
    baselineConfigs = processResults.filterConfigurations(results.keys(), filterConfig)
    
    width = 15

    print "Config".ljust(30),
    for i in range(np):
        if opts.printValues:
            print ("CPU"+str(i)+" est").rjust(width),
            print ("CPU"+str(i)+" act").rjust(width),
        print ("CPU"+str(i)+" % e").rjust(width),
    print 
    
    errsum = 0
    errsqsum = 0 
    numerrs = 0
    
    for config in results:
    
        if config.parameters["STATICASYMMETRICMHA"] == baselineKey:
            continue
        
        currentCpuID = expconfig.findCPUID(config.workload, config.benchmark, np)
        currentMHA = int(config.parameters["STATICASYMMETRICMHA"].split(",")[currentCpuID])
        
        if currentMHA == 16:
            continue
        
        expResults = retrievePatterns(config, results, np)
    
        filterConfig = copy.deepcopy(config)
        filterConfig.parameters["STATICASYMMETRICMHA"] = baselineKey
        baselineResults = processResults.filterConfigurations(baselineConfigs, filterConfig)
        if baselineResults == []:
            continue
        assert len(baselineResults) == 1
        
        
        # 1. estimate reduction in request intensity due to MSHR reduction
        baselineExpResults = retrievePatterns(baselineResults[0], results, np)
    
        baselineBusSlots = baselineExpResults["ticks"][0] / baselineExpResults["avgBusService"][0]
        baselineActualUtilization = baselineExpResults["busTotalReqs"][0] / baselineBusSlots
        
        mlpReduction = baselineExpResults["avgMLP"][16] / baselineExpResults["avgMLP"][currentMHA]   
        
        estimatedReducedReqCount = baselineExpResults["intManRequests"][currentCpuID] * mlpReduction
        noCacheFreeSlots = baselineExpResults["intManRequests"][currentCpuID] - estimatedReducedReqCount
        
        sharedCacheMissRate = baselineExpResults["sharedCacheMisses"][currentCpuID] / baselineExpResults["sharedCacheAccesses"][currentCpuID]
        freeRequestSlots = noCacheFreeSlots * sharedCacheMissRate 
        
        # 2. estimate how the CPUs will respond to this reduction:
        maxRequests = [0.0 for i in range(np)]
        maxBusRequests = [0.0 for i in range(np)]
        requestDist = [0.0 for i in range(np)]
        requestTotalWithoutCurrCPU = sum(expResults["intManRequests"]) - expResults["intManRequests"][currentCpuID] 
        for i in range(np):
            
            if i != currentCpuID:
                
                requestDist[i] =  baselineExpResults["intManRequests"][i] / requestTotalWithoutCurrCPU  
                
                avgPrivateModeQLat = baselineExpResults["avgBusQueueLat"][i] - baselineExpResults["avgBusQueueInt"][i]

                privModeAvgWait = avgPrivateModeQLat / baselineExpResults["avgBusServiceLat"][i]
                sharedModeAvgWait = baselineExpResults["avgBusQueueLat"][i] / baselineExpResults["avgBusServiceLat"][i] 

                thisRequestIntensity = baselineExpResults["intManRequests"][i] / baselineExpResults["ticks"][0]
                
                if thisRequestIntensity > opts.queueModelCutoff:
                    maxRequests[i] = (sharedModeAvgWait / privModeAvgWait) * baselineExpResults["intManRequests"][i]
                else:
                    maxRequests[i] = baselineExpResults["intManRequests"][i]
                
                thisMissRate = baselineExpResults["sharedCacheMisses"][i] / baselineExpResults["sharedCacheAccesses"][i]    
                maxBusRequests[i] = maxRequests[i] * thisMissRate
        
        newRequestCount = [baselineExpResults["intManRequests"][i] for i in range(np)]         
        newRequestCount[currentCpuID] = estimatedReducedReqCount
        
        if baselineActualUtilization > 0.95: 
            
            if sum(maxBusRequests) >= freeRequestSlots:
                for i in range(np):
                    if i != currentCpuID:
                        newRequestCount[i] += freeRequestSlots * requestDist[i]
            else:
                for i in range(np):
                    if i != currentCpuID:
                        newRequestCount[i] = maxRequests[i]
                
        else:
            # bus is not full in baseline, assume similar request intensity in reduced case
            pass
        
        values = []
        for i in range(np):
            estimatedIntensity = newRequestCount[i] / baselineExpResults["ticks"][0]
            actualIntensity = expResults["intManRequests"][i] / expResults["ticks"][0]
        
            relError = ((estimatedIntensity - actualIntensity) / actualIntensity) * 100
            
            errsum += relError
            errsqsum += relError**2
            numerrs += 1
            
            values.append( (estimatedIntensity, actualIntensity, relError) )
        
        printIt = False
        for ei, ai, re in values:
            if abs(re) >= opts.errorFilter:
                printIt = True
        
        if printIt:
            print str(config).ljust(30),
            for ei,ai,re in values:
                if opts.printValues:
                    print ("%.4f" % ei).rjust(width),
                    print ("%.4f" % ai).rjust(width),
                print ("%.1f" % re).rjust(width),
            print
    
    print
    print "Result statistics:"
    print "Average error                "+str(computeMean(numerrs, errsum))+" %"
    print "RMS error                    "+str(computeRMS(numerrs, errsqsum))+" %"
    print "Standard deviation of errors "+str(computeStddev(numerrs, errsum, errsqsum))+" %"
    print
    
def printResultData(resultData, np, decimals):
    
    width = 15
    
    workloads = resultData.keys()
    workloads.sort()
    
    print "".ljust(width),
    print "".ljust(width),
    
    if len(workloads) == 1:
        wlNames = deterministic_fw_wls.getBms(workloads[0], np, False)
        for wl in wlNames:
            print wl.rjust(width),
    else:
        for i in range(np):
            print ("CPU "+str(i)).rjust(width),
    print
    
    for wl in workloads:
        for mha in createMHAOrder():
            print wl.ljust(width),
            print mha.ljust(width),
            for i in range(np):
                try:
                    res = resultData[wl][mha][i]
                    print (("%."+str(decimals)+"f") % res).rjust(width),
                except:
                    print "N/A".rjust(width),
                
            print

def main():

    opts,args,params = parseArgs()
    
    np = int(args[0])
    
    if not os.path.exists(indexmodulename+".pkl"):
        fatal("index "+indexmodulename+" does not exist, create with searchStats.py")

    if not opts.quiet:
        print >> sys.stdout, "Reading index file "+indexmodulename+".pkl... ",
    sys.stdout.flush()
    index = StatfileIndex(indexmodulename)
    if not opts.quiet:
        print >> sys.stdout, "done!"

    searchConfig = expconfig.buildMatchAllConfig()
    searchConfig.parameters = params
    searchConfig.np = np
    if opts.benchmark != "":
        searchConfig.benchmark = str(opts.benchmark)
    if opts.workload != "":
        searchConfig.workload = opts.workload    
    
    results = StatResults(index, searchConfig, False, opts.quiet)
    searchRes = doSearch(results, np, opts)
    analyzeBusLatency(searchRes, np, opts)
    

if __name__ == '__main__':
    main()