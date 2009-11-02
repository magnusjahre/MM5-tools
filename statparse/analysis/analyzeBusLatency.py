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

basenames = {"requests": "interferenceManager.requests_",
             "busQueueLat": "interferenceManager.latency_bus_queue_",
             "busServiceLat": "interferenceManager.latency_bus_service_",
             "ticks": "sim_ticks",
             "mr0": "SharedCache0.overall_miss_rate",
             "mr1": "SharedCache1.overall_miss_rate",
             "mr2": "SharedCache2.overall_miss_rate",
             "mr3": "SharedCache3.overall_miss_rate"}


def parseArgs():
    parser = OptionParser(usage="analyzeBusLatency.py [options] np")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--parameters", action="store", dest="parameters", type="string", default="", help="Only print configs matching key and value. Format: key1,val1:key2,val2:...")
    parser.add_option("--bus-channels", action="store", dest="channels", type="int", default=-1, help="The number of memory bus channels")

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
    titles[0] = "R"
    titles[1] = "Q(R)"
    
    for config in results:
        
#        cpuID = expconfig.findCPUID(config.workload, config.benchmark, np)
        
        totalReqs = 0
        for i in range(np):
            totalReqs += results[config][basenames["requests"]+str(i)]
        
        totalQueueLatency = 0
        for i in range(np):    
            totalQueueLatency += results[config][basenames["busQueueLat"]+str(i)]
        
        
        totalServiceLatency = 0
        for i in range(np):    
            totalServiceLatency += results[config][basenames["busServiceLat"]+str(i)]
#        ticks = results[config][basenames["ticks"]]
        
        missRates = [0 for i in range(4)]
        missRates[0] = results[config][basenames["mr0"]]
        missRates[1] = results[config][basenames["mr1"]]
        missRates[2] = results[config][basenames["mr2"]]
        missRates[3] = results[config][basenames["mr3"]]
        
        avgMissRate = sum(missRates) / 4
        
        QofR = (float(totalQueueLatency) / float(totalServiceLatency)) 
        
        
        assert config not in data
        data[config] = {}
        data[config][0] = totalReqs * avgMissRate
        data[config][1] = QofR * totalReqs
    
    printResults.printResultDictionary(data, opts.decimals, sys.stdout, titles, None)

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