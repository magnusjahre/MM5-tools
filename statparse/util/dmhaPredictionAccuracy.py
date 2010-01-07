#!/usr/bin/env python

from statparse.util import fatal, computeTraceError, getNpExperimentDirs, parseUtilArgs
from statparse.tracefile.errorStatistics import plotBoxFromDict, printParamErrorStatDict, printErrorStatDict

commands = ["requests", "latency", "ipc"]

def getTracename(directory, aloneCPUID, sharedMode):
    return directory+"/missBandwidthPolicyPredictionTrace.txt"

def main():

    opts,args = parseUtilArgs("dmhaPredictionAccuracy.py", commands)
    try:
        np = int(args[0])
    except:
        fatal("Number of CPUs must be an integer")
    
    
    command = args[1]
    statistic = args[2]
    
    if not opts.quiet:
        print
        print "DMHA Prediction Accuracy"
        print
    
    dirs, sortedparams = getNpExperimentDirs(np)        
        
    if command == "requests":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Measured Num Requests", "Estimated Num Requests", True, False)
    elif command == "latency":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Measured Avg Shared Latency", "Measured Avg Shared Latency", True, False)
    elif command == "ipc":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Measured IPC", "Estimated IPC", True, False)
    else:
        assert False, "unknown command"
        
    if opts.printAll:
        printParamErrorStatDict(results, sortedparams, statistic, opts.relativeErrors, opts.decimals)
    else:
        printErrorStatDict(aggRes, opts.relativeErrors, opts.decimals, sortedparams)

    if opts.plotBox:
        plotBoxFromDict(results, opts.hideOutliers, command)
        

if __name__ == '__main__':
    main()