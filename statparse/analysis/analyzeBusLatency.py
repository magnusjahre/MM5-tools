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

#TODO: add membus..avg_service_cycles

basenames = {"busqueue": "membus..avg_queue_cycles",
             "busaccesses": "membus..total_requests",
             "busblocked": "membus..blocked_cycles",
             "cacheaccesses": "SharedCache..overall_accesses",
             "ticks": "sim_ticks"}


def parseArgs():
    parser = OptionParser(usage="analyzeBusLatency.py [options] np")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--parameters", action="store", dest="parameters", type="string", default="", help="Only print configs matching key and value. Format: key1,val1:key2,val2:...")
    parser.add_option("--sai-threshold", action="store", dest="saiThreshold", type="float", default=-1, help="Only print results with a lower shared memory system access intensity than the provied threshold")
    parser.add_option("--bus-channels", action="store", dest="channels", type="int", default=-1, help="Th number of memory bus channels")

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

def aggregateValues(results, config, basepattern, np):
    value = 0
    for i in range(np):
        value += results[config][basepattern+str(i)]
    return value

def aggregateValuesWithReplacement(results, config, basepattern, replaceStr, replaceWithStr, numIDs):
    value = 0
    for bankID in range(numIDs):
        pat = basepattern.replace(replaceStr, replaceWithStr+str(bankID))
        value += results[config][pat]
    return value

def analyzeBusLatency(results, np, opts):
    
    data = {}
    
    titles = {}
    titles[0] = "Shared Access Intensity"
    titles[1] = "Bus Accesses Intensity"
    titles[2] = "Bus Queue Intensity"
    titles[3] = "Memory Bus Cost"
    
    for config in results:
        
        cacheAccesses = aggregateValuesWithReplacement(results, config, basenames["cacheaccesses"], "SharedCache.", "SharedCache", numBanks)
        
        channels = -1
        if "MEMORY-BUS-CHANNELS" in config.parameters:
            channels = config.parameters["MEMORY-BUS-CHANNELS"]
        else:
            if opts.channels == -1:
                fatal("The channels parameter must be set when the number of channels cannot be determined from the experiment parameters")
            channels = opts.channels
        
        avgBusQueueLatency = aggregateValuesWithReplacement(results, config, basenames["busqueue"], "membus.", "membus", channels)
        busAccesses = aggregateValuesWithReplacement(results, config, basenames["busaccesses"], "membus.", "membus", channels)
        busBlocked = aggregateValuesWithReplacement(results, config, basenames["busblocked"], "membus.", "membus", channels)
        # TODO: add busservice
        
        
        simticks = results[config][basenames["ticks"]]
        
        sai = float(cacheAccesses) / float(simticks)
        
        if opts.saiThreshold == -1 or sai < opts.saiThreshold:
        
            assert config not in data
            data[config] = {}
            data[config][0] = sai 
            data[config][1] = float(busAccesses) / float(simticks)
            data[config][2] = ((float(busAccesses) * float(avgBusQueueLatency)) + busBlocked) / float(simticks)
            data[config][3] = -1
            
        
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