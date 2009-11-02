#!/usr/bin/env python

from optparse import OptionParser

import statparse.experimentConfiguration as expconfig
import statparse.experimentConfiguration as experimentConfiguration
import statparse.printResults as printResults

from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
from statparse import processResults, plotResults

import os
import sys

indexmodulename = "index-all"

numBanks = 4

basenames = {"requests": "membus0.total_requests",
             "busQueueLat": "membus0.total_queue_cycles",
             "busServiceLat": "membus0.total_service_cycles",
             "ticks": "sim_ticks"}


def parseArgs():
    parser = OptionParser(usage="analyzeBusLatency.py [options] np")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--parameters", action="store", dest="parameters", type="string", default="", help="Only print configs matching key and value. Format: key1,val1:key2,val2:...")
    parser.add_option("--bus-channels", action="store", dest="channels", type="int", default=-1, help="The number of memory bus channels")
    parser.add_option("--plot", action="store_true", dest="plot", default=False, help="Show scatter-plot of resulting data")
    parser.add_option("--benchmark", action="store", dest="benchmark", type="string", default="", help="Only show results for this benchmark")

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
    for b in basenames:
        patterns.append(basenames[b])
    
    searchRes = results.searchForPatterns(patterns) 
    return processResults.invertSearchResults(searchRes)

def analyzeBusLatency(results, np, opts):
    
    data = {}
    
    titles = {}
    titles[0] = "Request Intensity (reqs / tick)"
    titles[1] = "Avg Queue Delay (requests)"
    
    for config in results:
        
        totalReqs = float(results[config][basenames["requests"]])
        totalQueueLat = float(results[config][basenames["busQueueLat"]])
        totalServiceLat = float(results[config][basenames["busServiceLat"]])
        ticks = float(results[config][basenames["ticks"]])        
    
        actualUtilization = totalServiceLat / ticks
        
        assert config not in data
        data[config] = {}
        data[config][0] = totalReqs / ticks
        data[config][1] = totalQueueLat / totalServiceLat
#        data[config][1] = actualUtilization

    plotFunc = None
    if opts.plot:
        plotFunc = plotResults.plotScatter
    
    printResults.printResultDictionary(data, opts.decimals, sys.stdout, titles, plotFunc)

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
    results = StatResults(index, searchConfig, False, opts.quiet)
    searchRes = doSearch(results, np, opts)
    analyzeBusLatency(searchRes, np, opts)
    

if __name__ == '__main__':
    main()