#!/usr/bin/env python

from statparse.util import fatal, getNpExperimentDirs, computeTraceError, parseUtilArgs
from statparse.tracefile.errorStatistics import printParamErrorStatDict, plotBoxFromDict, printErrorStatDict

commands = ["total", "bus-queue", "bus-service"]

def getTracename(directory, aloneCPUID, sharedMode):
    prefix = "CPU"
    if sharedMode:
        postfix = "InterferenceTrace.txt"
    else:
        postfix = "LatencyTrace.txt"
    
    return directory+"/"+prefix+str(aloneCPUID)+postfix

def main():

    opts,args = parseUtilArgs("privateLatencyAccuracy.py", commands)
    try:
        np = int(args[0])
    except:
        fatal("Number of CPUs must be an integer")
    
    command = args[1]
    statistic = args[2]
    
    if not opts.quiet:
        print
        print "Number of Requests Synchronized Alone Latency Accuracy"
        print
    
    dirs, sortedparams = getNpExperimentDirs(np)
    
    if opts.relativeErrors:
        
        if command == "total":
            colname = "Total"
        elif command == "bus-service":
            colname = "bus_service"
        elif command == "bus-queue":
            colname = "bus_queue"
        else:
            assert False, "unknown command"
        
        
        def getBaselineName(directory, aloneCPUID):
            return directory+"/CPU"+str(aloneCPUID)+"LatencyTrace.txt", colname 
        
        baselineFunc = getBaselineName
    else:
        baselineFunc = None
    
    if command == "total":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Total", "Total", False, True, baselineFunc)
    elif command == "bus-service":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "bus_service", "bus_service", False, True, baselineFunc)
    elif command == "bus-queue":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "bus_queue", "bus_queue", False, True, baselineFunc)
    else:
        assert False, "unknown command"
        
    if opts.printAll:
        printParamErrorStatDict(results, sortedparams, statistic, opts.relativeErrors, opts.decimals)
    else:
        printErrorStatDict(aggRes, opts.relativeErrors, opts.decimals, sortedparams)
        
    if opts.plotBox:
        plotBoxFromDict(results, opts.hideOutliers, "Latency")

if __name__ == '__main__':
    main()