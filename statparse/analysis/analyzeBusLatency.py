#!/usr/bin/env python

from optparse import OptionParser

import statparse.experimentConfiguration as expconfig
import statparse.experimentConfiguration as experimentConfiguration
import statparse.printResults as printResults

from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
from statparse import processResults

import os
import sys

indexmodulename = "index-all"

numBanks = 4

basenames = {"busqueue": "interferenceManager.avg_latency_bus_queue_",
             "busservice": "interferenceManager.avg_latency_bus_service_",
             "cachemisses": "SharedCache..overall_misses",
             "ticks": "sim_ticks"}


def parseArgs():
    parser = OptionParser(usage="analyzeBusLatency.py [options] np")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--parameters", action="store", dest="parameters", type="string", default="", help="Only print configs matching key and value. Format: key1,val1:key2,val2:...")

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
    titles[0] = "Shared Cache Misses"
    titles[1] = "Average Queue Length"
    titles[2] = "Million Clock Cycles"
    
    for config in results:
        cpuID = expconfig.findCPUID(config.workload, config.benchmark, np)
        
        busQueueLatency = results[config][basenames["busqueue"]+str(cpuID)]
        busServiceLatency = results[config][basenames["busservice"]+str(cpuID)]
        
        cacheMisses = 0
        for bankID in range(numBanks):
            pat = basenames["cachemisses"].replace("SharedCache.", "SharedCache"+str(bankID))
            cacheMisses += results[config][pat]
        
        simticks = results[config][basenames["ticks"]]
        
        assert config not in data
        data[config] = {}
        data[config][0] = cacheMisses
        data[config][1] = float(busQueueLatency) / float(busServiceLatency)
        data[config][2] = float(simticks) / 1000000.0
        
    printResults.printResultDictionary(data, opts.decimals, sys.stdout, titles)

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
    results = StatResults(index, searchConfig, False, opts.quiet)
    searchRes = doSearch(results, np, opts)
    analyzeBusLatency(searchRes, np, opts)
    

if __name__ == '__main__':
    main()