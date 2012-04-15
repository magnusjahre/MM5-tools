#!/usr/bin/env python

from statparse.util import fatal, getNpExperimentDirs, computeTraceError, parseUtilArgs
from statparse.tracefile.errorStatistics import plotBoxFromDict, dumpAllErrors
import statparse.tracefile.errorStatistics as errorStats

commands = ["IPC", "MWS", "latency", "overlap", "compute", "privlat", "memind", "cpl", "stall", "cwp", "writestall", "erob"]

def getTracename(dir, cpuID, sharedMode):
    prefix = "globalPolicyCommittedInsts"
    postfix = ".txt"
    
    return dir+"/"+prefix+str(cpuID)+postfix

def main():

    opts,args = parseUtilArgs("computeAloneIPCError.py", commands)
    try:
        np = int(args[0])
    except:
        fatal("Number of CPUs must be an integer")
    
    
    command = args[1]
    statname = args[2]
    
    if not opts.quiet:
        print
        print "Committed Instruction Synchronized Estimation Accuracy"
        print
    
    dirs, sortedparams = getNpExperimentDirs(np)
    
    if command == "IPC":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Measured Alone IPC", "Estimated Alone IPC", False, True)
    elif command == "MWS":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Misses while Stalled", "Misses while Stalled", False, True)
    elif command == "latency":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Alone Memory Latency", "Estimated Private Latency", False, True) 
    elif command == "overlap":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Measured Alone Overlap", "Estimated Alone Overlap", False, True)
    elif command == "compute":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Compute Cycles", "Compute Cycles", False, True)
    elif command == "privlat":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Private Stall Cycles", "Private Stall Cycles", False, True)
    elif command == "memind":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Memory Independent Stalls", "Memory Independent Stalls", False, True)
    elif command == "cpl":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "CPL", "CPL", False, True)
    elif command == "stall":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Actual Stall", "Stall Estimate", False, True)
    elif command == "cwp":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "CWP", "CWP", False, True)
    elif command == "writestall":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Write Stall Cycles", "Alone Write Stall Estimate", False, True)
    elif command == "erob":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Empty ROB Stall Cycles", "Alone Empty ROB Stall Estimate", False, True)
    else:
        assert False, "unknown command"
        
    if opts.printAll:
        errorStats.printParamErrorStatDict(results, sortedparams, statname, opts.relativeErrors, opts.decimals)
    else:
        errorStats.printErrorStatDict(aggRes, opts.relativeErrors, opts.decimals, sortedparams)
        
    if opts.plotBox:
        plotBoxFromDict(results, opts.hideOutliers, sortedparams)
        
    if opts.allErrorFile:
        dumpAllErrors(results, opts.allErrorFile)

if __name__ == '__main__':
    main()