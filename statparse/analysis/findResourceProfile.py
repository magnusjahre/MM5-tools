#!/usr/bin/env python

from optparse import OptionParser
from statparse.util import fatal
from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
from statparse.plotResults import plotImage
from fairmha.experimentconfig import specnames
from workloads import workloads
from statparse.tracefile import isFloat

import statparse.experimentConfiguration as expconfig
import statparse.processResults as procres
import statparse.printResults as printres
import optcomplete

import os
import sys

ERRVAL = 0.0

def parseArgs():
    parser = OptionParser(usage="findResourceProfile.py [options] [benchmark]")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--simpoint", action="store", dest="simpoint", type="int", default=-1, help="Only provide results for this simpoint value")
    parser.add_option("--plot", action="store_true", dest="plot", default=False, help="Plot results in heatmap")
    parser.add_option("--list-benchmarks", action="store_true", dest="listBenchmarks", default=False, help="Print a list of the benchmark names")
    parser.add_option("--optimal-part-np", action="store", type="int", dest="optPartNP", default=4, help="Find optimal partitions for this core count")
    parser.add_option("--max-ways", action="store", type="int", dest="maxWays", default=16, help="Total number of ways available")
    parser.add_option("--max-bandwidth", action="store", type="float", dest="maxBW", default=1.0, help="Total bandwidth available")
    parser.add_option("--plot-file", action="store", type="string", dest="plotFile", default="", help="Plot to this file")

    optcomplete.autocomplete(parser, optcomplete.ListCompleter(specnames))
    opts, args = parser.parse_args()

    if len(args) > 1:
        print
        print "Commandline error:"
        print parser.usage
        print 
        sys.exit(0)
    
    if len(args) == 1:
        if args[0] not in specnames:
            print
            print fatal("Unknown SPEC benchmark "+args[0])
            print
    
    if opts.listBenchmarks:
        names = specnames[:]
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
        
        if "MEMORY-BUS-MAX-UTIL" in p:
            useBWKey = "MEMORY-BUS-MAX-UTIL" 
        else: 
            assert "NFQ-PRIORITIES" in p
            useBWKey = "NFQ-PRIORITIES"
        
        if p[useBWKey] not in allUtils:
            allUtils.append(p[useBWKey])
        if p["MAX-CACHE-WAYS"] not in allWays:
            allWays.append(p["MAX-CACHE-WAYS"])
             
    allWays.sort()
    allUtils.sort()
    
    profile = [[ERRVAL for j in range(len(allUtils))] for i in range(len(allWays))]
    
    searchConfig = expconfig.buildMatchAllConfig()
    
    for i in range(len(allWays)):
        for j in range(len(allUtils)):
            searchConfig.parameters["MAX-CACHE-WAYS"] = allWays[i]
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
                    
    return vals

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
    
    ways = mergeBmDict(bmways)
    utils = mergeBmDict(bmutils)
    
    np = opts.optPartNP
    
    validCacheAllocs = []
    generateAllRAs(0, [], ways, np, opts.maxWays, validCacheAllocs)
    
    validBWAllocs = []
    generateAllRAs(0, [], utils, np, opts.maxBW, validBWAllocs)
    
    for cacheAlloc in validCacheAllocs:
        for bwAlloc in validBWAllocs:
            print cacheAlloc, bwAlloc
            
            # TODO: compute performance

def handleMultibenchmark(index, opts):
    
    if not opts.quiet:
        print
        print "Creating profiles for all benchmarks..."
        print
    
    allprofiles = {}
    allBmWays = {}
    allBmUtils = {}
    
    for benchmark in specnames:
        
        print "Processing "+benchmark 
        
        results = doSearch(benchmark+"0", index, opts)
        allWays, allUtils, profile = gatherPerformanceProfile(results)
        
        allUtils = convertUtilList(allUtils)
        
        printTable(allWays, allUtils, profile, opts, "profile-data-"+benchmark+".txt")
        doPlot(benchmark, allWays, allUtils, profile, "profile-plot-"+benchmark+".pdf")
        
        assert benchmark not in allprofiles
        allprofiles[benchmark] = profile
        allBmWays[benchmark] = allWays
        allBmUtils[benchmark] = allUtils
            
    findOptimalPartitions(allprofiles, allBmWays, allBmUtils, opts)

def handleSingleBenchmark(benchmark, index, opts):

    results = doSearch(benchmark, index, opts)
    
    allWays, allUtils, profile = gatherPerformanceProfile(results)
    
    if not opts.quiet:
        print
        print "Performance Profile for "+benchmark
        print
    
    allUtils = convertUtilList(allUtils)
    
    printTable(allWays, allUtils, profile, opts)

    if opts.plot:
        doPlot(benchmark, allWays, allUtils, profile, filename=opts.plotFile)
        

def doPlot(title, allWays, allUtils, profile, filename = ""):
    
    yrangestr = "0,"+str(len(allWays))
    xrangestr = "0,"+str(len(allUtils))
    zrangestr = "0,"+str(max(max(profile)))
    
    plotImage(profile,
              xlabel="NFQ Prioritiy",
              ylabel="Available Cache Ways",
              zlabel="Instructions Per Cycle (IPC)",
              title=title,
              xticklabels=allUtils,
              yticklabels=allWays,
              yrange=yrangestr,
              xrange=xrangestr,
              zrange=zrangestr,
              filename=filename)

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
        benchmark = args[0]+"0"
        handleSingleBenchmark(benchmark, index, opts)
    else:
        handleMultibenchmark(index, opts)
    

if __name__ == '__main__':
    main()