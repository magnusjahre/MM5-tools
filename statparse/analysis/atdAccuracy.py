#!/usr/bin/env python

from optparse import OptionParser
from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
import statparse.experimentConfiguration as expconfig 
import statparse.processResults as processResults
import statparse.printResults as printResults
from statparse import plotResults
from optcomplete import ListCompleter

import sys
import os
import optcomplete

indexmodulename = "index-all"
numBanks = 4

def parseArgs():
    parser = OptionParser(usage="atdAccuracy.py [options] NP")
    
    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--full-map", action="store_true", dest="fullMap", default=False, help="Use full-map implementation results in parsing")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--absolute-error", action="store_true", dest="abserror", default=False, help="Print absolute number of misses (default is relative to the number of shared cache misses)")
    parser.add_option("--print-banks", action="store_true", dest="printbanks", default=False, help="Print results per bank")
    parser.add_option("--plot-box", action="store_true", dest="plotBox", default=False, help="Create box and whiskers plot")
    parser.add_option("--miss-filter", action="store", type="int", dest="missFilter", default=0, help="Filter results that do not have this number of misses")
    
    optcomplete.autocomplete(parser, ListCompleter(["4", "8", "16"]))
    
    opts, args = parser.parse_args()
    if len(args) != 1:
        print "Command line error..."
        print "Usage "+parser.usage
        sys.exit(-1)
    
    return opts, args

def evaluateATDAccuracy(results, opts, np):
    patterns = ["Shared.*misses_per_cpu_", "Shared.*misses_per_cpu$", "Shared.*cpu_extra_misses_", "Shared.*estimated_shadow_misses_"]
    
    searchRes = results.searchForPatterns(patterns)
    matchedRes = processResults.matchSPBsToMPB(searchRes, opts.quiet, np)
    
    # 3. Compute metric
    missErrorResults = {}
    for config in matchedRes:
        sharedMisses = []
        sharedEstimates = []
        aloneMisses = []
        
        for b in range(numBanks):
            cpuID = expconfig.findCPUID(config.workload, config.benchmark, config.np)
            
            sharedMissName = "SharedCache"+str(b)+".misses_per_cpu_"+str(cpuID)
            aloneMissName = "SharedCache"+str(b)+".misses_per_cpu"
            
            sharedExtraMissName = "SharedCache"+str(b)+".cacheinterference.cpu_extra_misses_"+str(cpuID)
            sharedEstMissName = "SharedCache"+str(b)+".cacheinterference.estimated_shadow_misses_"+str(cpuID)
            
            if opts.fullMap:    
                est = matchedRes[config][sharedMissName]["MPB"] - matchedRes[config][sharedExtraMissName]["MPB"]
            else:
                est = matchedRes[config][sharedEstMissName]["MPB"] 
            
            sharedMisses.append(matchedRes[config][sharedMissName]["MPB"])
            sharedEstimates.append(est)
            aloneMisses.append(matchedRes[config][aloneMissName]["SPB"])
        
        if opts.printbanks:
            assert False, "Printing per bank results not implemented"
        
        if sum(sharedMisses) > opts.missFilter:
        
            err = sum(sharedEstimates) - sum(aloneMisses)
            if not opts.abserror:
                err = float(err)/float(sum(sharedMisses))
            
            assert config not in missErrorResults
            missErrorResults[config] = err
            
        else:
            missErrorResults[config] = "RM"

    if opts.plotBox:
        plotFunc = plotResults.plotBoxPlot
    else:
        plotFunc = None
            
    printResults.printWorkloadResultTable(missErrorResults, opts.decimals, sys.stdout, np, plotFunc)
    
def main():
    
    opts, args = parseArgs()
    
    if not os.path.exists("pbsconfig.py"):
        print "ERROR: pbsconfig.py not found"
        return -1
    
    if not os.path.exists(indexmodulename+".pkl"):
        print "ERROR: cannot find index "+indexmodulename+".pkl, run searchStats.py to generate index"
        return -1 
    
    np = int(args[0])

    if not opts.quiet:
        print >> sys.stdout, "Reading index file "+indexmodulename+".pkl... ",
        sys.stdout.flush()
    index = StatfileIndex(indexmodulename)
    if not opts.quiet:
        print >> sys.stdout, "done!"
    
    searchConfig = expconfig.buildMatchAllConfig()
    results = StatResults(index, searchConfig, False, opts.quiet)
    
    evaluateATDAccuracy(results, opts, np)
         
if __name__ == '__main__':
    main()
