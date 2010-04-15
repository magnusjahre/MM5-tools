#!/usr/bin/env python

from optparse import OptionParser
from statparse.util import fatal
from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
from statparse.plotResults import plotImage

import statparse.experimentConfiguration as expconfig
import statparse.processResults as procres
import statparse.printResults as printres

import os
import sys

ERRVAL = -1.0

def parseArgs():
    parser = OptionParser(usage="findResourceProfile.py [options] benchmark")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--simpoint", action="store", dest="simpoint", type="int", default=-1, help="Only provide results for this simpoint value")
    parser.add_option("--plot", action="store_true", dest="plot", default=False, help="Plot results in heatmap")

    opts, args = parser.parse_args()

    if len(args) != 1:
        print
        print "Commandline error:"
        print parser.usage
        print 
        sys.exit(0)
    
    return opts,args

def gatherPerformanceProfile(results):
    
    results.plainSearch("COM:IPC")
    
    allParams = procres.findAllParams(results.matchingConfigs)
    
    allWays = []
    allUtils = []
    for p in allParams:
        if p["MEMORY-BUS-MAX-UTIL"] not in allUtils:
            allUtils.append(p["MEMORY-BUS-MAX-UTIL"])
        if p["MAX-CACHE-WAYS"] not in allWays:
            allWays.append(p["MAX-CACHE-WAYS"]) 
    allWays.sort()
    allUtils.sort()
    
    profile = [[ERRVAL for j in range(len(allUtils))] for i in range(len(allWays))]
    
    searchConfig = expconfig.buildMatchAllConfig()
    
    for i in range(len(allWays)):
        for j in range(len(allUtils)):
            searchConfig.parameters["MAX-CACHE-WAYS"] = allWays[i]
            searchConfig.parameters["MEMORY-BUS-MAX-UTIL"] = allUtils[j]
            
            configRes = procres.filterConfigurations(results.matchingConfigs, searchConfig)
            
            if(len(configRes) > 1):
                fatal("Multiple results for benchmark, should you specify the simpoint parameter?")
            elif len(configRes) == 0:
                continue
            
            profile[i][j] = results.noPatResults[configRes[0]]
    
    return allWays, allUtils, profile

def printTable(allWays, allUtils, profile, opts):
    
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
        
    printres.printData(textarray, just, sys.stdout, opts.decimals)
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
    
    searchConfig = expconfig.buildMatchAllConfig()
    searchConfig.benchmark = args[0]
    if opts.simpoint != -1:
        searchConfig.simpoint = opts.simpoint
    results = StatResults(index,
                          searchConfig,
                          False,
                          opts.quiet)
    
    allWays, allUtils, profile = gatherPerformanceProfile(results)
    
    if not opts.quiet:
        print
        print "Performance Profile for "+args[0]
        print
    
    printTable(allWays, allUtils, profile, opts)
    
    
    
    if opts.plot:
        
        yrangestr = "0,"+str(len(allWays))
        xrangestr = "0,"+str(len(allUtils))
        
        plotImage(profile,
                  xlabel="Maximum Memory Bus Utilization",
                  ylabel="Available Cache Ways",
                  title=args[0],
                  xticklabels=allUtils,
                  yticklabels=allWays,
                  yrange=yrangestr,
                  xrange=xrangestr)

if __name__ == '__main__':
    main()