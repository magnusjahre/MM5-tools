#!/usr/bin/env python

from optparse import OptionParser

from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults

import statparse.experimentConfiguration as expconfig
import statparse.processResults as processResults
import statparse.printResults as printResults
import statparse.experimentConfiguration as experimentConfiguration
from statparse.analysis import computeMean,computeRMS,computeStddev

import os
import sys

indexmodulename = "index-all"

models = ["mlp", "opacu", "mshrcnt"]
availMemsys = ["RingBased", "CrossbarBased"]

def parseArgs():
    parser = OptionParser(usage="performanceModelAccuracy.py [options] NP")

    parser.add_option("--model", action="store", dest="model", default="mshrcnt", help="The model to use for estimations ("+str(models)+")")
    parser.add_option("--memsys", action="store", dest="memsys", default="RingBased", help="The memory system to use for estimations ("+str(availMemsys)+")")
    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--use-spm-mlp", action="store_true", dest="useSpmMLP", default=False, help="Use mlp numbers from single program mode")
    parser.add_option("--parameters", action="store", dest="parameters", type="string", default="", help="Only print configs matching key and value. Format: key1,val1:key2,val2:...")
    parser.add_option("--no-stats", action="store_true", dest="noStats", default=False, help="Don't print statistics")

    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Command line error..."
        print "Usage : "+parser.usage
        sys.exit(-1)
    
    if opts.model not in models:
        print "Unknown estimation model"
        print "Alternatives: "+str(models)
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

def retrievePatterns(results, opts, np):
    patterns = ["COM:count", 
                "sim_ticks", 
                "COM:IPC"]
    
    cachenames = ["Private", "L1dcaches"]
    for cachename in cachenames:
        patterns.append(cachename+".*average_mlp") 
        patterns.append(cachename+".*avg_roundtrip_latency")
        patterns.append(cachename+".*num_roundtrip_responses") 
        patterns.append(cachename+".*opacu_serial_misses")
        patterns.append(cachename+".*opacu_serial_percentage")
        patterns.append(cachename+".*mshrcnt_serial_misses")
        patterns.append(cachename+".*mshrcnt_serial_percentage")
        
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
    
    errsum = 0
    errsqsum = 0
    n = 0
    
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
        opacuserialmissname = cachename+".opacu_serial_misses"
        mshrcntserialmissname = cachename+".mshrcnt_serial_misses"
        
        ipcname = "detailedCPU"+str(cpuID)+".COM:IPC"
        ticksname = "sim_ticks"
        
        if mlpname not in data[mpbconfig]:
            fatal("Pattern missing from results. Have you specified the correct memory system?")
        
        
        mpbRoundtrip = data[mpbconfig][roundtripname]["MPB"]
        spbRoundtrip = data[mpbconfig][roundtripname]["SPB"]
        responses = data[mpbconfig][responsesname]["MPB"]
        committed = data[mpbconfig][committedname]["MPB"]
        spmIPC = data[mpbconfig][ipcname]["SPB"]
        mpbIPC = data[mpbconfig][ipcname]["MPB"]
        ticks = data[mpbconfig][ticksname]["MPB"]
        if opts.useSpmMLP:
            mpbmlp = data[mpbconfig][mlpname]["SPB"]
            opacuSerialMisses = data[mpbconfig][opacuserialmissname]["SPB"]
            mshrcntSerialMisses = data[mpbconfig][mshrcntserialmissname]["SPB"]
        else:
            mpbmlp = data[mpbconfig][mlpname]["MPB"]
            opacuSerialMisses = data[mpbconfig][opacuserialmissname]["MPB"]
            mshrcntSerialMisses = data[mpbconfig][mshrcntserialmissname]["MPB"]
        
        if opts.model == "mlp":
            estAloneIPC = l2MLPAloneIPC(committed, ticks, mpbmlp, mpbRoundtrip, spbRoundtrip, responses, str(mpbconfig), compTrace)
        elif opts.model == "opacu":
            estAloneIPC = commitCounterAloneIPC(committed, ticks, opacuSerialMisses, mpbRoundtrip, spbRoundtrip, responses, str(mpbconfig), compTrace)
        elif opts.model == "mshrcnt":
            estAloneIPC = commitCounterAloneIPC(committed, ticks, mshrcntSerialMisses, mpbRoundtrip, spbRoundtrip, responses, str(mpbconfig), compTrace)
        else:
            fatal("unknown model")
    
        relErrPerc = ((estAloneIPC - spmIPC) / spmIPC) * 100
        errsum += relErrPerc
        errsqsum += relErrPerc*relErrPerc
        n += 1
    
        assert mpbconfig not in accuracy
        accuracy[mpbconfig] = {}
        accuracy[mpbconfig][0] = mpbIPC
        accuracy[mpbconfig][1] = spmIPC
        accuracy[mpbconfig][2] = estAloneIPC
        accuracy[mpbconfig][3] = estAloneIPC - spmIPC
        accuracy[mpbconfig][4] = relErrPerc        
    
    printResults.printResultDictionary(accuracy, opts.decimals, sys.stdout, titles)

    if not opts.noStats:
        avg = computeMean(n, errsum)
        rms = computeRMS(n, errsqsum)
        stddev = computeStddev(n, errsum, errsqsum)
        
        print 
        print "Relative Error Statistics:"
        print "Mean:               "+printResults.numberToString(avg, opts.decimals).rjust(10)+" %"
        print "RMS Error:          "+printResults.numberToString(rms, opts.decimals).rjust(10)+" %"
        print "Standard deviation: "+printResults.numberToString(stddev, opts.decimals).rjust(10)+" %"

def main():
    opts,args,params = parseArgs()
    
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
    searchConfig.parameters = params
    results = StatResults(index, searchConfig, False, opts.quiet)
    
    data = retrievePatterns(results, opts, np)
    
    compTrace = open("estimate-comp-trace.txt", "w")
    
    computeModelAccuracy(data, opts, np, compTrace)
    
    compTrace.flush()
    compTrace.close()

if __name__ == '__main__':
    main()