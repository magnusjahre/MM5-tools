#!/usr/bin/env python

from optparse import OptionParser

from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults

import statparse.experimentConfiguration as expconfig
import statparse.processResults as processResults
import statparse.printResults as printResults

import os
import sys

indexmodulename = "index-all"

models = ["mlp", "opacu"]
availMemsys = ["RingBased", "CrossbarBased"]

def parseArgs():
    parser = OptionParser(usage="performanceModelAccuracy.py [options] NP")

    parser.add_option("--model", action="store", dest="model", default="opacu", help="The model to use for estimations ("+str(models)+")")
    parser.add_option("--memsys", action="store", dest="memsys", default="RingBased", help="The memory system to use for estimations ("+str(availMemsys)+")")
    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")

    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Command line error..."
        print "Usage : "+parser.usage
        sys.exit(-1)
    
    if opts.model not in models:
        print "Unknown estimation model"
        print "Alternatives: "+str(models)
        sys.exit(-1)
    
    return opts,args

def fatal(message):
    print >> sys.stderr, "Fatal: "+message
    sys.exit(-1)

def retrievePatterns(results, opts, np):
    patterns = ["COM:count", 
                "sim_ticks", 
                "COM:IPC"]
    
    cachenames = ["Private", "L1dcaches"]
    for cachename in cachenames:
        patterns.append(cachename+".*average_mlp") 
        patterns.append(cachename+".*avg_roundtrip_latency")
        patterns.append(cachename+".*num_roundtrip_responses") 
        patterns.append(cachename+".*serial_misses")
        patterns.append(cachename+".*serial_percentage")
    searchRes = results.searchForPatterns(patterns)
    searchRes = processResults.addAllUnitNames(searchRes, opts.quiet, np)
    matchedRes = processResults.matchSPBsToMPB(searchRes, opts.quiet, np)
    return matchedRes

def l2MLPAloneIPC(committed, ticks, mlp, sharedRoundtrip, aloneRoundtrip, responses, configname, tracefile):
    
    interference = sharedRoundtrip - aloneRoundtrip
    sharedIntTicks = interference * responses
    sharedExposedIntTicks = sharedIntTicks * mlp
    aloneEstimateTicks = ticks - sharedExposedIntTicks
    aloneEstimatedIPC = float(committed) / float(aloneEstimateTicks)
    
    sharedMemTicks = sharedRoundtrip * responses
    sharedExposedLatTicks = sharedMemTicks * mlp
    print >> tracefile, configname
    print >> tracefile, "Interference: ", sharedRoundtrip, aloneRoundtrip, interference
    print >> tracefile, "Ticks:       ", ticks
    print >> tracefile, "Committed    ", committed
    print >> tracefile, "MLP:         ", mlp
    print >> tracefile, "Resps:       ", responses
    print >> tracefile, "Memticks :   ", sharedMemTicks, sharedIntTicks
    print >> tracefile, "Exposed:     ", sharedExposedLatTicks, sharedExposedIntTicks
    print >> tracefile, ""
    
    return aloneEstimatedIPC

def commitCounterAloneIPC(committed, ticks, serialMisses, sharedRoundtrip, aloneRoundtrip, responses, configname, tracefile):
    interference = sharedRoundtrip - aloneRoundtrip
    interferencePenalty = interference * serialMisses
    
    aloneTickEstimate = ticks - interferencePenalty
    aloneIPCEstimate = float(committed) / float(aloneTickEstimate)
    sharedIPC = float(committed) / float(ticks)
    
    print >> tracefile, configname
    print >> tracefile, "Interference: ", sharedRoundtrip, aloneRoundtrip, interference
    print >> tracefile, "Ticks:        ", ticks
    print >> tracefile, "Committed     ", committed
    print >> tracefile, "Serial misses ", serialMisses
    print >> tracefile, "Total resps   ", responses
    print >> tracefile, "Int penalty   ", interferencePenalty
    print >> tracefile, "Alone est IPC ", aloneIPCEstimate
    print >> tracefile, "Shared IPC    ", sharedIPC
    print >> tracefile, ""
    
    return aloneIPCEstimate

def computeModelAccuracy(data, opts, np, compTrace):
    
    accuracy = {}
    
    titles = {}
    titles[0] = "Shared IPC"
    titles[1] = "Alone IPC"
    titles[2] = "Estimated Alone IPC"
    titles[3] = "Abs Error (IPC)"
    titles[4] = "Relative Error (%)"
    titles[5] = "Shared MLP"
    titles[6] = "Shared Serial Percentage"
    
    for mpbconfig in data:
        
        cpuID = expconfig.findCPUID(mpbconfig.workload, mpbconfig.benchmark, np)
        
        if opts.memsys == "RingBased":
            cachename = "PrivateL2Cache"+str(cpuID)
        elif opts.memsys == "CrossbarBased":
            cachename = "L1dcaches"+str(cpuID)
        else:
            fatal("Unknown memory system")
        
        mlpname = cachename+".average_mlp"
        roundtripname = cachename+".avg_roundtrip_latency"
        responsesname = cachename+".num_roundtrip_responses"
        committedname = "detailedCPU"+str(cpuID)+".COM:count"
        serialmissname = cachename+".serial_misses"
        
        ipcname = "detailedCPU"+str(cpuID)+".COM:IPC"
        ticksname = "sim_ticks"
        
        if mlpname not in data[mpbconfig]:
            fatal("Pattern missing from results. Have you specified the correct memory system?")
        
        mpbmlp = data[mpbconfig][mlpname]["MPB"]
        mpbRoundtrip = data[mpbconfig][roundtripname]["MPB"]
        spbRoundtrip = data[mpbconfig][roundtripname]["SPB"]
        responses = data[mpbconfig][responsesname]["MPB"]
        committed = data[mpbconfig][committedname]["MPB"]
        spmIPC = data[mpbconfig][ipcname]["SPB"]
        mpbIPC = data[mpbconfig][ipcname]["MPB"]
        ticks = data[mpbconfig][ticksname]["MPB"]
        serialMisses = data[mpbconfig][serialmissname]["MPB"]
        
        if opts.model == "mlp":
            estAloneIPC = l2MLPAloneIPC(committed, ticks, mpbmlp, mpbRoundtrip, spbRoundtrip, responses, str(mpbconfig), compTrace)
        elif opts.model == "opacu":
            estAloneIPC = commitCounterAloneIPC(committed, ticks, serialMisses, mpbRoundtrip, spbRoundtrip, responses, str(mpbconfig), compTrace)
        else:
            fatal("unknown model")
    
        assert mpbconfig not in accuracy
        accuracy[mpbconfig] = {}
        accuracy[mpbconfig][0] = mpbIPC
        accuracy[mpbconfig][1] = spmIPC
        accuracy[mpbconfig][2] = estAloneIPC
        accuracy[mpbconfig][3] = estAloneIPC - spmIPC
        accuracy[mpbconfig][4] = ((estAloneIPC - spmIPC) / spmIPC) * 100
        accuracy[mpbconfig][5] = mpbmlp
        accuracy[mpbconfig][6] = data[mpbconfig][cachename+".serial_percentage"]["MPB"]
    
    printResults.printResultDictionary(accuracy, opts.decimals, sys.stdout, titles)

def main():
    opts,args = parseArgs()
    
    if not os.path.exists(indexmodulename+".pkl"):
        fatal("index "+indexmodulename+" does not exist, create with searchStats.py")

    np = int(args[0])

    if not opts.quiet:
        print >> sys.stdout, "Reading index file "+indexmodulename+".pkl... ",
    sys.stdout.flush()
    index = StatfileIndex(indexmodulename)
    if not opts.quiet:
        print >> sys.stdout, "done!"
    
    searchConfig = expconfig.buildMatchAllConfig()
    results = StatResults(index, searchConfig, False, opts.quiet)
    
    data = retrievePatterns(results, opts, np)
    
    compTrace = open("estimate-comp-trace.txt", "w")
    
    computeModelAccuracy(data, opts, np, compTrace)
    
    compTrace.flush()
    compTrace.close()

if __name__ == '__main__':
    main()