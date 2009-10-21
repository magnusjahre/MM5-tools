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

def parseArgs():
    parser = OptionParser(usage="performanceModelAccuracy.py [options] NP")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")

    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Command line error..."
        print "Usage : "+parser.usage
        sys.exit(-1)
    
    return opts,args

def fatal(message):
    print >> sys.stderr, "Fatal: "+message
    sys.exit(-1)

def retrievePatterns(results, opts, np):
    patterns = ["Private.*average_mlp", "Private.*avg_roundtrip_latency", "COM:count", "sim_ticks", "COM:IPC", "Private.*num_roundtrip_responses"]
    searchRes = results.searchForPatterns(patterns)
    searchRes = processResults.addAllUnitNames(searchRes, opts.quiet, np)
    matchedRes = processResults.matchSPBsToMPB(searchRes, opts.quiet, np)
    return matchedRes

def estimateIntFreeIPC(committed, ticks, mlp, sharedRoundtrip, aloneRoundtrip, responses, configname, tracefile):
    
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

def computeModelAccuracy(data, opts, np, compTrace):
    
    accuracy = {}
    
    titles = {}
    titles[0] = "Shared IPC"
    titles[1] = "Alone IPC"
    titles[2] = "Estimated Alone IPC"
    titles[3] = "Abs Error (IPC)"
    titles[4] = "Relative Error (%)"
    titles[5] = "MPM MLP"
    titles[6] = "SPM MLP"
    titles[7] = "Rel error (%)"
    
    for mpbconfig in data:
        
        cpuID = expconfig.findCPUID(mpbconfig.workload, mpbconfig.benchmark, np)
        
        mlpname = "PrivateL2Cache"+str(cpuID)+".average_mlp"
        roundtripname = "PrivateL2Cache"+str(cpuID)+".avg_roundtrip_latency"
        responsesname = "PrivateL2Cache"+str(cpuID)+".num_roundtrip_responses"
        committedname = "detailedCPU"+str(cpuID)+".COM:count"
        ipcname = "detailedCPU"+str(cpuID)+".COM:IPC"
        ticksname = "sim_ticks"
        
        mpbmlp = data[mpbconfig][mlpname]["MPB"]
        spbmlp = data[mpbconfig][mlpname]["SPB"]
        mpbRoundtrip = data[mpbconfig][roundtripname]["MPB"]
        spbRoundtrip = data[mpbconfig][roundtripname]["SPB"]
        responses = data[mpbconfig][responsesname]["MPB"]
        committed = data[mpbconfig][committedname]["MPB"]
        spmIPC = data[mpbconfig][ipcname]["SPB"]
        mpbIPC = data[mpbconfig][ipcname]["MPB"]
        ticks = data[mpbconfig][ticksname]["MPB"]
        
        estAloneIPC = estimateIntFreeIPC(committed, ticks, mpbmlp, mpbRoundtrip, spbRoundtrip, responses, str(mpbconfig), compTrace)
    
        assert mpbconfig not in accuracy
        accuracy[mpbconfig] = {}
        accuracy[mpbconfig][0] = mpbIPC
        accuracy[mpbconfig][1] = spmIPC
        accuracy[mpbconfig][2] = estAloneIPC
        accuracy[mpbconfig][3] = estAloneIPC - spmIPC
        accuracy[mpbconfig][4] = ((estAloneIPC - spmIPC) / spmIPC) * 100
        accuracy[mpbconfig][5] = mpbmlp
        accuracy[mpbconfig][6] = spbmlp
        accuracy[mpbconfig][7] = ((mpbmlp - spbmlp) / mpbmlp) * 100
    
    printResults.printResultDictionary(accuracy, opts.decimals, sys.stdout, titles)

def main():
    opts,args = parseArgs()
    
    if not os.path.exists(indexmodulename+".pkl"):
        fatal("index "+indexmodulename+" does not exist, create with searchStats.py")
        
    if not os.path.exists("pbsconfig.py"):
        fatal("pbsconfig.py not found")

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