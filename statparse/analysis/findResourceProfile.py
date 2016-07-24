#!/usr/bin/env python

from optparse import OptionParser
from statparse.util import fatal
from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
from statparse.plotResults import plotImage, plotLines
from fairmha.experimentconfig import specnames
from fairmha.experimentconfig import spec2006names
from deterministic_fw_wls import getBms, workloads, getWorkloads
from statparse.tracefile import isFloat
from resourcePartition import ResourcePartition

import statparse.experimentConfiguration as expconfig
import statparse.processResults as procres
import statparse.printResults as printres
from statparse.printResults import printData, numberToString
from statparse.analysis import computePercError
import optcomplete
import statparse.metrics as metrics

from workloadfiles.workloads import Workload

import pickle
import random

import os
import sys
from math import log

ERRVAL = 0.0
USE_CACHE_WAYS = 16
NO_BW_KEY = "max"

class BMClass:
    BM_RES_LOW = 0
    BM_STREAMING = 1
    BM_RES_MEDIUM = 2
    BM_RES_HIGH = 3
    
    def __init__(self, wlType, avgBWSpeedup, avgLLCSpeedup, normalizedLLCPerfCurve):
        self.type = wlType
        self.avgBWSpeedup = avgBWSpeedup
        self.avgLLCSpeedup = avgLLCSpeedup
        self.normalizedLlcPerfCurve = normalizedLLCPerfCurve
        
    def __str__(self):
        if self.type == self.BM_STREAMING:
            return "s"
        if self.type == self.BM_RES_HIGH:
            return "h"
        if self.type == self.BM_RES_MEDIUM:
            return "m"
        
        return "l"

class PerformanceModel:
    
    FUNC_LIN = 0
    FUNC_POW = 1
    
    def __init__(self, debugPrint, functype):
        self.alpha = 0
        self.missRate = 0.0
        self.beta = 0.0
        
        self.mlp = 0.0
        self.computeCycles = 0.0
        self.committedInstructions = 0.0
        self.sharedMemSysReqs = 0.0
        
        self.printDebug = debugPrint
 
        if functype ==  "lin":
            self.functype = self.FUNC_LIN
        elif functype == "pow":
            self.functype = self.FUNC_POW
        else:
            raise Exception("Function type "+str(functype)+" not supported")
        
        self.linArrivalA = 0
        self.linArrivalB = 0
        
        self.powArrivalA = 0
        self.powArrivalB = 0

    def estimateIPC(self, bandwidthAlloc):
        
        if self.printDebug:
            print "Estimating IPC for allocation "+str(bandwidthAlloc)
        
        avgMemLat = self.estimateMemoryLatency(bandwidthAlloc)
        expectedStallTime = avgMemLat * self.mlp * self.sharedMemSysReqs
        
        if self.printDebug:
            print "-- Avg memory latency "+str(avgMemLat)+", mlp "+str(self.mlp)+" and "+str(self.sharedMemSysReqs)+" requests gives stall time "+str(expectedStallTime)
        
        ipc = self.committedInstructions / (self.computeCycles + expectedStallTime)
        
        if self.printDebug:
            print "-- "+str(self.committedInstructions)+" committed instructions and "+str(self.computeCycles)+" compute cycles gives IPC "+str(ipc)
            
        return ipc

    def estimateMemoryLatency(self, bandwidthAlloc):        
        queueLatEst = self.computeBusQueueLat(bandwidthAlloc)
        
        if self.printDebug:
            print "-- Got bus queue latency estimate "+str(queueLatEst)

        busLatency = self.beta + queueLatEst

        if self.printDebug:
            print "-- Estimating average bus latency to "+str(busLatency)
        
        avgMemLat = self.alpha + self.missRate * busLatency 
        
        if self.printDebug:
            print "-- Alpha "+str(self.alpha)+" and miss rate "+str(self.missRate)+" gives average memory latency estimate "+str(avgMemLat)
        
        return avgMemLat
    
    def computeBusQueueLat(self, bandwidthAlloc):
        if self.functype == self.FUNC_LIN:
            return self.linArrivalA * bandwidthAlloc + self.linArrivalB
        assert self.functype == self.FUNC_POW
        return self.powArrivalA * (bandwidthAlloc ** self.powArrivalB) 
    
    def computeBusQueueFunction(self, midpoint, maxpoint):
        
        if self.printDebug:
            print "Created arrival function with points "+str(midpoint)+", "+str(maxpoint)
    
        midbusq, midbw = midpoint
        maxbusq, maxbw = maxpoint
    
        if self.functype == self.FUNC_LIN:
            self.computeLinBusQueueFunction(maxbusq, maxbw, midbusq, midbw)
        elif self.functype == self.FUNC_POW:
            self.computePowBusQueueFunction(maxbusq, maxbw, midbusq, midbw)
        else:
            raise Exception("Unsupported function type")
    
    def computePowBusQueueFunction(self, maxy, maxbw, midy, midbw):
        self.powArrivalB = ((log(float(maxy)) - log(float(midy))) / (log(float(maxbw)) - log(float(midbw))))
        self.powArrivalA = float(maxy) / (float(maxbw)**self.powArrivalB)
        
        if self.printDebug:
            print "Created power estimation function y = "+str(self.powArrivalA)+"x^"+str(self.powArrivalB)
        
    
    def computeLinBusQueueFunction(self, maxy, maxbw, midy, midbw):
        self.linArrivalA = (maxy - midy) / (maxbw - midbw)
        self.linArrivalB = midy - (self.linArrivalA * midbw)
        
        if self.printDebug:
            print "Created linear estimation function y = "+str(self.linArrivalA)+"x + "+str(self.linArrivalB)
        
    def setBusLatencies(self, busTransfer, busEntry):
        self.beta = busTransfer + busEntry
    
    def setCycleVals(self, stallCycles, totalCycles, totalMemLat):
        self.computeCycles = totalCycles - stallCycles
        self.mlp = float(stallCycles) / float(totalMemLat)
        
def getAllSPECNames():
    allSPECNames = specnames[:]
    for n in spec2006names:
        allSPECNames.append(n)
    return allSPECNames

def parseArgs():
    parser = OptionParser(usage="findResourceProfile.py [options] [benchmark]")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--simpoint", action="store", dest="simpoint", type="int", default=-1, help="Only provide results for this simpoint value")
    parser.add_option("--plot", action="store_true", dest="plot", default=False, help="Plot results in heatmap")
    parser.add_option("--list-benchmarks", action="store_true", dest="listBenchmarks", default=False, help="Print a list of the benchmark names")
    parser.add_option("--find-optimal-part", action="store_true", dest="findOptPart", default=False, help="Find optimal partitions")
    parser.add_option("--optimal-part-np", action="store", type="int", dest="optPartNP", default=4, help="Find optimal partitions for this core count")
    parser.add_option("--max-ways", action="store", type="int", dest="maxWays", default=16, help="Total number of ways available")
    parser.add_option("--max-bandwidth", action="store", type="float", dest="maxBW", default=1.0, help="Total bandwidth available")
    parser.add_option("--plot-file", action="store", type="string", dest="plotFile", default="", help="Plot to this file")
    parser.add_option("--metric", action="store", type="string", dest="metric", default="", help="Performance metric to use when finding optimal partitions")
    parser.add_option("--optimal-module-name", action="store", type="string", dest="optModuleName", default="optimalPartitions", help="The name of the python module to store the optimal partitions")
    parser.add_option("--optimal-human-file-name", action="store", type="string", dest="humanPartFile", default="optimalPartitions.txt", help="The name of the file to store to store the human readable partitions")
    parser.add_option("--validate-model", action="store_true", dest="validateModel", default=False, help="Validate the bandwidth model")
    parser.add_option("--debug-model", action="store_true", dest="debugModel", default=False, help="Print debug info for performance model")
    parser.add_option("--queue-lat-function", action="store", dest="queueLatFunction", default="pow", help="Bus queue latency estimation function type (pow or lin)")
    parser.add_option("--greyscale", action="store_true", dest="greyscale", default=False, help="Create grayscale heatmaps")
    
    defStreamingThres = 1.2
    defHighThres = 2.0
    defMediumThres = 1.25
    defWlDistStr = "h:15,m:15,s:5,l:5"
    
    parser.add_option("--generate-workloads", action="store_true", dest="genwl", default=False, help="Generate a workloads in file reswl.py")
    parser.add_option("--streaming-threshold", action="store", dest="streamingThreshold", type="float", default=defStreamingThres, help="Speedup threshold used to classify a benchmark as streaming (Default: "+str(defStreamingThres)+")")
    parser.add_option("--medium-threshold", action="store", dest="mediumThreshold", type="float", default=defMediumThres, help="Speedup threshold used to classify a benchmark as having medium resouce sensitivity (Default: "+str(defMediumThres)+")")    
    parser.add_option("--high-threshold", action="store", dest="highThreshold", type="float", default=defHighThres, help="Speedup threshold used to classify a benchmark highly resource sensitive (Default: "+str(defHighThres)+")")
    parser.add_option("--wl-dist", action="store", dest="wlDistStr", type="string", default=defWlDistStr, help="Comma-divided string containing the number of workloads to generate of each type (Default: "+defWlDistStr+")")
    parser.add_option("--workloadfile", action="store", dest="wlfile", type="string", default="typewls.pkl", help="The file to write the workload dictionary (Defalut: typewls.pcl)")
    parser.add_option("--allow-reuse", action="store_true", dest="allowReuse", default=False, help="Allow a benchmark to used more than once in a workload")

    allSPECNames = getAllSPECNames()

    optcomplete.autocomplete(parser, optcomplete.ListCompleter(allSPECNames))
    opts, args = parser.parse_args()

    if len(args) > 1:
        print
        print "Commandline error:"
        print parser.usage
        print 
        sys.exit(0)
    
    if len(args) == 1:
        if args[0] not in allSPECNames:
            print
            print fatal("Unknown SPEC benchmark "+args[0])
            print
    
    if opts.listBenchmarks:
        names = allSPECNames[:]
        names.sort()
        print
        print "SPEC Benchmark Names"
        print
        for b in names:
            print "- "+b
        print
        sys.exit(0)
        
    
    return opts,args

def gatherPerformanceProfile(results):
    
    results.plainSearch("COM:IPC")
    
    allParams = procres.findAllParams(results.matchingConfigs)
    
    allWays = []
    allUtils = []
    
    for p in allParams:
        
        if p["MAX-CACHE-WAYS"] not in allWays:
            allWays.append(p["MAX-CACHE-WAYS"])
        
        if "MEMORY-BUS-MAX-UTIL" in p:
            useBWKey = "MEMORY-BUS-MAX-UTIL" 
        elif "NFQ-PRIORITIES" in p:
            useBWKey = "NFQ-PRIORITIES"
        else:
            useBWKey = NO_BW_KEY
            continue
        
        if p[useBWKey] not in allUtils:
            allUtils.append(p[useBWKey])
        
    
    if len(allUtils) == 0:
        allUtils.append(useBWKey)
    
    allWays.sort()
    allUtils.sort()
    
    profile = [[ERRVAL for j in range(len(allUtils))] for i in range(len(allWays))]
    
    searchConfig = expconfig.buildMatchAllConfig()
    
    for i in range(len(allWays)):
        for j in range(len(allUtils)):
            searchConfig.parameters["MAX-CACHE-WAYS"] = allWays[i]
            if useBWKey != NO_BW_KEY:
                searchConfig.parameters[useBWKey] = allUtils[j]
            
            configRes = procres.filterConfigurations(results.matchingConfigs, searchConfig)
            
            if(len(configRes) > 1):
                fatal("Multiple results for benchmark, should you specify the simpoint parameter?")
            elif len(configRes) == 0:
                continue
            
            profile[i][j] = results.noPatResults[configRes[0]]
    
    return allWays, allUtils, profile

def printTable(allWays, allUtils, profile, opts, outfilename = ""):
    
    header = [""]
    for util in allUtils:
        header.append(printres.numberToString(util, opts.decimals))
    
    textarray = []
    textarray.append(header)
    
    for i in range(len(allWays)):
        line = [printres.numberToString(allWays[i], opts.decimals)]
        for j in range(len(allUtils)):
            if profile[i][j] != ERRVAL:
                line.append(printres.numberToString(profile[i][j], opts.decimals))
            else:
                line.append("N/A")
    
        textarray.append(line)
    
    just = [True]
    for i in range(len(allUtils)):
        just.append(False)
        
    if outfilename != "":
        outfile = open(outfilename, "w")
    else:
        outfile = sys.stdout
        
    printres.printData(textarray, just, outfile, opts.decimals)

    if outfilename != "":
        outfile.close() 

def doSearch(benchmark, index, opts):
    searchConfig = expconfig.buildMatchAllConfig()
    searchConfig.benchmark = benchmark
    if opts.simpoint != -1:
        searchConfig.simpoint = opts.simpoint
    results = StatResults(index,
                          searchConfig,
                          False,
                          opts.quiet)
    return results

def convertUtilList(allUtils):
    assert len(allUtils) > 0
    if isFloat(allUtils[0]):
        return allUtils
    
    if allUtils[0] == NO_BW_KEY:
        return allUtils
    
    newUtilList = []
    for u in allUtils:
        try:
            newUtilList.append(float(u.split(",")[0]))
        except:
            fatal("Unknown NFQ priorities format")
    return newUtilList

def mergeBmDict(bmdict):
    vals = []
    message = "Malformed resource allocation key list for at least one benchmark"
    for k in bmdict:
        if vals == []:
            vals = bmdict[k]
        else:
            for i in range(len(vals)):
                try:
                    if(bmdict[k][i] != vals[i]):
                        fatal(message)
                except:
                    fatal(message)

    # create index dictionary
    retdict = {}
    for i in range(len(vals)):
        assert vals[i] not in retdict
        retdict[vals[i]] = i

    return vals, retdict

def generateAllRAs(level, allocation, resources, maxlevel, maxval, results):
    if level < maxlevel:
        for r in resources:
            newAlloc = allocation[:]
            newAlloc.append(r)
            generateAllRAs(level+1, newAlloc, resources, maxlevel, maxval, results)
    
    
    if level == maxlevel and sum(allocation) == maxval:
        results.append(allocation)
        

def findOptimalPartitions(bmprofiles, bmways, bmutils, opts):
    
    if not opts.quiet:
        print
        print "Searching for optimal partitions"
        print
    
    ways, wayToIndex = mergeBmDict(bmways)
    utils, utilToIndex = mergeBmDict(bmutils)
    
    np = opts.optPartNP
    if np not in workloads:
        fatal("We don't have workloads for CPU count "+str(np))
    
    validCacheAllocs = []
    generateAllRAs(0, [], ways, np, opts.maxWays, validCacheAllocs)
    
    validBWAllocs = []
    generateAllRAs(0, [], utils, np, opts.maxBW, validBWAllocs)
    
    useMetrics = []
    if opts.metric != "":
        useMetrics.append(metrics.createMetric(opts.metric))
    else:
        for metricName in metrics.mpMetricNames:
            useMetrics.append(metrics.createMetric(metricName))
    
    optimalPartitions = {}
    for perfMetric in useMetrics:

        if not opts.quiet:
            print
            print "Processing metric "+str(perfMetric)+"..."

        optimalPartitions[str(perfMetric.key())] = {}
    
    
        for wl in getWorkloads(np):
            
            if not opts.quiet:
                print "Finding optimal partition for workload "+wl+"..."
            
            benchmarks = getBms(wl, np)
            benchmarksWithZeros = getBms(wl, np, True) 
            
            optimalPart = ResourcePartition(np)
                     
            for cacheAlloc in validCacheAllocs:
                for bwAlloc in validBWAllocs:
                    
                    performance = []
                    baseline = []
                    perfMetric.clearValues()
    
                    for i in range(np):
                        wayIndex = wayToIndex[cacheAlloc[i]]
                        utilIndex = utilToIndex[bwAlloc[i]]
    
                        performance.append(bmprofiles[benchmarks[i]][wayIndex][utilIndex])
                        
                        baselineWayIndex = wayToIndex[max(wayToIndex.keys())]
                        baselineUtilIndex = utilToIndex[max(utilToIndex.keys())]
                        
                        baseline.append(bmprofiles[benchmarks[i]][baselineWayIndex][baselineUtilIndex])
    
    
                    sharedPerf = metrics.buildSimpointDict(benchmarksWithZeros, performance)
                    baselinePerf = metrics.buildSimpointDict(benchmarksWithZeros, baseline)
                    
                    if perfMetric.spmNeeded:
                        perfMetric.setValues(sharedPerf, baselinePerf, np, wl)
                    else:
                        perfMetric.setValues(sharedPerf, {}, np, wl)
                                    
                    metricValue = perfMetric.computeMetricValue()[0]
                    
                    if metricValue > optimalPart.metricValue:
                        optimalPart.setPartition(cacheAlloc, bwAlloc, metricValue, sharedPerf)
            
            assert optimalPart.isInitialized()
            assert wl not in optimalPartitions[perfMetric.key()]
            if not opts.quiet:
                print "Optimal partition: Cache "+str(optimalPart.ways)+", bw "+str(optimalPart.utils)
            optimalPartitions[perfMetric.key()][wl] = optimalPart
        
    return optimalPartitions

def classify(profiles, opts):
    cacheConfigs = len(profiles)
    bwConfigs = len(profiles[0])
    
    cacheSpeedupSum = 0.0
    for i in range(bwConfigs):
        speedup = profiles[cacheConfigs-1][i] / profiles[0][i] 
        cacheSpeedupSum += speedup
    cacheAvgSpeedup = cacheSpeedupSum / float(bwConfigs)
    
    bwSpeedupSum = 0.0
    for i in range(cacheConfigs):
        speedup = profiles[i][bwConfigs-1] / profiles[i][0] 
        bwSpeedupSum += speedup
    bwAvgSpeedup = bwSpeedupSum / float(cacheConfigs)
    
    llcPerfCurve = []
    for i in range(cacheConfigs):
        llcPerfCurve.append(profiles[i][bwConfigs-1] / profiles[0][bwConfigs-1])
    
    if bwConfigs == 1:
        # Cannot detect streaming behaviour without measurements of bandwidth use
        if cacheAvgSpeedup >= opts.highThreshold:
            return BMClass(BMClass.BM_RES_HIGH, bwAvgSpeedup, cacheAvgSpeedup, llcPerfCurve)
        if cacheAvgSpeedup >= opts.mediumThreshold:
            return BMClass(BMClass.BM_RES_MEDIUM, bwAvgSpeedup, cacheAvgSpeedup, llcPerfCurve)  
    else:
        assert opts.mediumThreshold > opts.streamingThreshold
        if cacheAvgSpeedup < opts.streamingThreshold and bwAvgSpeedup >= opts.highThreshold:
            return BMClass(BMClass.BM_STREAMING, bwAvgSpeedup, cacheAvgSpeedup, llcPerfCurve)
        if cacheAvgSpeedup >= opts.highThreshold and bwAvgSpeedup >= opts.highThreshold:
            return BMClass(BMClass.BM_RES_HIGH, bwAvgSpeedup, cacheAvgSpeedup, llcPerfCurve)
        if cacheAvgSpeedup >= opts.mediumThreshold and bwAvgSpeedup >= opts.mediumThreshold:
            return BMClass(BMClass.BM_RES_MEDIUM, bwAvgSpeedup, cacheAvgSpeedup, llcPerfCurve)    

    return BMClass(BMClass.BM_RES_LOW, bwAvgSpeedup, cacheAvgSpeedup, llcPerfCurve)

def printClassification(classification):
    print
    print "Benchmark classification"
    print
    
    for c in classification:
        print c+": ",
        for bm in classification[c]:
            print bm,
        print

def findWorkload(bms, np, opts):
    wl = Workload()
    
    if len(bms) < np and (not opts.allowReuse):
        print "WARNING: too few benchmarks to generate workload for "+str(np)+" cores"
        return None 
    
    while wl.getNumBms() < np:
        index = random.randint(0, len(bms)-1)
        if (not opts.allowReuse) and wl.containsBenchmark(bms[index]):
            continue
        wl.addBenchmark(bms[index])
    return wl

def printWorkloads(wls, opts):
    
    outfile = open(opts.wlfile, "w")
    pickle.dump(wls, outfile)
    outfile.close()
    
    if not opts.quiet:
        for np in wls:
            print
            print str(np)+" core workloads:"
            print
            for cn in wls[np]:
                for w in wls[np][cn]:
                    print cn, str(w)

def getWorkloadCounts(typeStr):
    
    wlTypeCntStrs = typeStr.split(",")
    
    wlTypeCnt = {}
    for cntStr in wlTypeCntStrs:
        cntArr = cntStr.split(":")
        try:
            wlTypeCnt[cntArr[0]] = int(cntArr[1])
        except:
            fatal("Could not parse workload string element "+cntStr)
    
    return wlTypeCnt

def generateWorkloads(allprofiles, opts):
    
    classification = {}
    
    for bm in allprofiles:
        cl = classify(allprofiles[bm], opts)
        if not opts.quiet:
            print "Classified "+bm+" in category "+str(cl)+", avg bandwidth speedup "+str(cl.avgBWSpeedup)+", avg LLC speedup "+str(cl.avgLLCSpeedup)
            #print "LLC performance curve", cl.normalizedLlcPerfCurve
        
        if str(cl) not in classification:
            classification[str(cl)] = []
        classification[str(cl)].append(bm)
    
    if not opts.quiet:
        printClassification(classification)
    
    workloads = {}
    random.seed(56)
     
    wlTypeCnts = getWorkloadCounts(opts.wlDistStr)
    
    for np in [2,4,8]:
        workloads[np] = {}
        for classname in classification:
            workloads[np][classname] = []
            if classname not in wlTypeCnts:
                fatal("Unknown workload class name "+classname+" provided")
            for i in range(wlTypeCnts[classname]):
                newwl = findWorkload(classification[classname], np, opts)
                if newwl == None:
                    break
                workloads[np][classname].append(newwl) 
    
    printWorkloads(workloads, opts)
    

def handleMultibenchmark(index, opts):
    
    if not opts.quiet:
        print
        print "Creating profiles for all benchmarks..."
        print
    
    allprofiles = {}
    allBmWays = {}
    allBmUtils = {}
    allModels = {}
    lastutil = []
    
    for benchmark in getAllSPECNames():
        
        print "Processing "+benchmark 
        
        results = doSearch(benchmark, index, opts)
        allWays, allUtils, profile = gatherPerformanceProfile(results)
        
        if allUtils == []:
            print "No results found, skipping"
            continue
        
        allUtils = convertUtilList(allUtils)
        lastutil = allUtils
        
        printTable(allWays, allUtils, profile, opts, "profile-data-"+benchmark+".txt")
        if opts.plot:
            doPlot(benchmark, allWays, allUtils, profile, opts.greyscale, "profile-plot-"+benchmark+".pdf")

        assert benchmark not in allprofiles
        allprofiles[benchmark] = profile
        allBmWays[benchmark] = allWays
        allBmUtils[benchmark] = allUtils
        
        if opts.validateModel:
            actual, model = buildModel(benchmark, results, opts, allUtils, allWays, profile, "profile-error-plot-"+benchmark+".pdf")
            allModels[benchmark] = (actual, model)
     
    if opts.findOptPart:
        optimalPartitions = findOptimalPartitions(allprofiles, allBmWays, allBmUtils, opts)
        printPartitions(optimalPartitions, opts)
    
    if opts.validateModel:
        printModelAccuracy(lastutil, allModels, opts)
        
    if opts.genwl:
        generateWorkloads(allprofiles, opts)

def printModelAccuracy(utils, allModels, opts):
    lines = []

    header = [""]
    just = [True]
    for u in utils:
        header.append(numberToString(u, opts.decimals))
        just.append(False)
    lines.append(header)
    
    bms = allModels.keys()
    bms.sort()
    
    for bm in bms:
        line = [bm]
        actual, model = allModels[bm]
        assert len(actual) == len(utils)
        assert len(model) == len(utils)
        for i in range(len(utils)):
            line.append(numberToString(computePercError(model[i], actual[i]), opts.decimals))
        lines.append(line)
    
    print
    print "Performance model percentage error"
    print
    printData(lines, just, sys.stdout, opts.decimals)
    

def printPartitions(optimalPartitions, opts):
    
    outname = opts.optModuleName+".pkl"
    
    if not opts.quiet:
        print
        print "Dumping optimal partitions data into module "+outname
    
    outfile = open(outname, "w")
    
    pickle.dump(optimalPartitions, outfile)
    
    outfile.close()
    
    header = ["Workload", "Optimal Cache Ways", "Optimal Utilization", "Metric Value"]
    just = [True, False, False, False]
    
    if not opts.quiet:
        print "Dumping human readable optimal partitions data into module "+opts.humanPartFile
    
    readableOptFile = open(opts.humanPartFile, "w")
    for metric in optimalPartitions:
        readableOptFile.write("\nOptimal partitons for metric "+metric+"\n\n")
    
        lines = [header]
        
        wls = optimalPartitions[metric].keys()
        wls.sort()
        
        for wl in wls:
            line = [wl,
                    str(optimalPartitions[metric][wl].ways),
                    str(optimalPartitions[metric][wl].utils),
                    numberToString(optimalPartitions[metric][wl].metricValue, opts.decimals)]
            
            lines.append(line)
    
        printData(lines, just, readableOptFile, opts.decimals)
    
    readableOptFile.flush()
    readableOptFile.close()

def findPattern(patstring, results, maxBW = False):
    results.plainSearch(patstring)
    
    if results.noPatResults == {}:
        fatal("No results found for pattern "+patstring)
    
    searchConfig = expconfig.buildMatchAllConfig()    
    searchConfig.parameters["MAX-CACHE-WAYS"] = USE_CACHE_WAYS
    if maxBW:
        searchConfig.parameters["NFQ-PRIORITIES"] = "0.99,0.01"
    else:
        searchConfig.parameters["NFQ-PRIORITIES"] = "0.25,0.75"
    
    configRes = procres.filterConfigurations(results.matchingConfigs, searchConfig)
    assert len(configRes) == 1
    return results.noPatResults[configRes[0]]

def buildModel(benchmark, results, opts, allUtils, allWays, profile, plotfilename=""):
    perfModel = PerformanceModel(opts.debugModel, opts.queueLatFunction)
    
    perfModel.setCycleVals(findPattern("interferenceManager.cpu_stall_cycles", results),
                           findPattern("sim_ticks", results),
                           findPattern("interferenceManager.total_latency", results))
    
    perfModel.committedInstructions = findPattern("detailedCPU0.COM:count", results)
    perfModel.sharedMemSysReqs = findPattern("interferenceManager.requests", results)

    busReads = float(findPattern("membus0.reads_per_cpu", results))
    busEntryLatSum = findPattern("interferenceManager.latency_bus_entry", results)
    busServiceLatSum = findPattern("interferenceManager.latency_bus_service", results)
    busQueueLatSumMid = findPattern("interferenceManager.latency_bus_queue", results)
    busQueueLatSumMax = findPattern("interferenceManager.latency_bus_queue", results, True)

    perfModel.setBusLatencies(float(busServiceLatSum) / busReads,
                              float(busEntryLatSum) / busReads)    

    perfModel.computeBusQueueFunction((float(busQueueLatSumMid) / busReads, 0.25),
                                      (float(busQueueLatSumMax) / busReads, 0.99))

    accesses = 0
    misses = 0
    for b in range(4):
        accesses += findPattern("SharedCache"+str(b)+".read_accesses", results)
        misses += findPattern("SharedCache"+str(b)+".read_misses", results)
    perfModel.missRate = float(misses) / float(accesses)

    avgBusLatency = findPattern("interferenceManager.avg_latency_bus_entry", results) + findPattern("interferenceManager.avg_latency_bus_queue", results) + findPattern("interferenceManager.avg_latency_bus_service", results)
    alpha = findPattern("interferenceManager.avg_round_trip_latency", results) - avgBusLatency 

    if opts.debugModel:
        print "Removing avg bus latency "+str(avgBusLatency)
        print "Measured bus requests "+str(busReads)+", miss rate "+str(perfModel.missRate)
        print "Computed avg bus lat is "+str(perfModel.missRate * (float(busServiceLatSum+busQueueLatSumMid+busEntryLatSum)/busReads))
    
    perfModel.alpha = alpha
    
    cacheIndex = -1
    for i in range(len(allWays)):
        if allWays[i] == USE_CACHE_WAYS:
            assert cacheIndex == -1
            cacheIndex = i
    assert cacheIndex != -1
    
    predictions = []
    for i in range(len(allUtils)):
        predictions.append(perfModel.estimateIPC(allUtils[i]))
    
    if opts.plot:
        plotLines([allUtils, allUtils],
                  [profile[cacheIndex], predictions],
                  legendTitles=["Actual", "Model"],
                  filename=plotfilename)
        
    return (profile[cacheIndex], predictions)
    

def handleSingleBenchmark(benchmark, index, opts):

    results = doSearch(benchmark, index, opts)
    
    allWays, allUtils, profile = gatherPerformanceProfile(results)
    
    if not opts.quiet:
        print
        print "Performance Profile for "+benchmark
        print
    
    allUtils = convertUtilList(allUtils)
    
    printTable(allWays, allUtils, profile, opts)

    if opts.plot and not opts.validateModel:
        doPlot(benchmark, allWays, allUtils, profile, opts.greyscale, filename=opts.plotFile)
    
    if opts.validateModel:
        actual, model = buildModel(benchmark, results, opts, allUtils, allWays, profile)
        printAccuracy(allUtils, actual, model, opts)
        
def printAccuracy(allUtils, actual, model, opts):
    
    assert len(allUtils) == len(actual)
    assert len(actual) == len(model)
    
    lines =[ ["Util", "Actual", "Model", "% err"]]
    for i in range(len(allUtils)):
        line = []
        line.append(numberToString(allUtils[i], opts.decimals))
        line.append(numberToString(actual[i], opts.decimals))
        line.append(numberToString(model[i], opts.decimals))
        line.append(numberToString(computePercError(model[i],actual[i]), opts.decimals))
                
        lines.append(line)
        
    print
    printData(lines, [True, False, False, False], sys.stdout, opts.decimals)
        

def doPlot(title, allWays, allUtils, profile, doGreyscale, filename = ""):
    
    yrangestr = "-0.5,"+str(len(allWays)-0.5)
    xrangestr = "-0.5,"+str(len(allUtils)-0.5)
    zrangestr = "0,"+str(max(max(profile)))
    
    if len(allUtils) > 1:
        plotImage(profile,
                  xlabel="Max Bandwidth Utilization (%)",
                  ylabel="Available Cache Ways",
                  zlabel="Instructions Per Cycle (IPC)",
                  title=title,
                  xticklabels=allUtils,
                  yticklabels=allWays,
                  yrange=yrangestr,
                  xrange=xrangestr,
                  zrange=zrangestr,
                  filename=filename,
                  greyscale=doGreyscale)
    else:
        cacheprofile = []
        for p in profile:
            cacheprofile.append(p[0])
        plotLines([allWays],
                  [cacheprofile],
                  yrange="0,"+str(max(cacheprofile)*1.1),
                  xlabel="Cache Ways",
                  ylabel="IPC")

def main():
    opts,args = parseArgs()
    
    if not os.path.exists("index-all.pkl"):
        print
        fatal("Index file does not exist")
        
    if not os.path.exists("pbsconfig.py"):
        print
        fatal("pbsconfig.py not found")
        
    pbsconfigmodule = __import__("pbsconfig")
    pbsconfigobj = pbsconfigmodule.config
        
    if not opts.quiet:
        print
        print "Cache Capacity and Memory Bandwidth Resource Profile"
        print
        print "Loading index... ",
        sys.stdout.flush()
    index = StatfileIndex("index-all")
    if not opts.quiet:
        print "done!"

    if len(args) > 0:
        benchmark = args[0]
        handleSingleBenchmark(benchmark, index, opts)
    else:
        handleMultibenchmark(index, opts)

if __name__ == '__main__':
    main()
