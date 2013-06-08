#!/usr/bin/env python

from statparse.util import fatal, getNpExperimentDirs, computeTraceError, parseUtilArgs
from statparse.tracefile.errorStatistics import plotBoxFromDict, dumpAllErrors
import statparse.tracefile.errorStatistics as errorStats

commands = ["IPC", "MWS", "latency", "overlap", "compute", "privlat", "memind", "cpl", "stall", "cwp", "writestall", "erob"]

def getTracename(dir, cpuID, sharedMode):
    prefix = "globalPolicyCommittedInsts"
    postfix = ".txt"
    
    return dir+"/"+prefix+str(cpuID)+postfix

class ColumnPair:
    def __init__(self, privcol, shcol):
        self.privateColumn = privcol
        self.sharedColumn = shcol

class ColumnMatches:
    def __init__(self):
        self.colstore = {}
        self.populateColstore()
        
    def populateColstore(self):
        self.colstore["IPC"] = ColumnPair("Measured Alone IPC", "Estimated Alone IPC")
        self.colstore["MWS"] = ColumnPair("Misses while Stalled", "Misses while Stalled")
        self.colstore["latency"] = ColumnPair("Alone Memory Latency", "Estimated Private Latency")
        self.colstore["overlap"] = ColumnPair("Measured Alone Overlap", "Estimated Alone Overlap")

        self.colstore["compute"] = ColumnPair("Compute Cycles", "Compute Cycles")
        self.colstore["privlat"] = ColumnPair("Private Stall Cycles", "Private Stall Cycles")
        self.colstore["memind"] = ColumnPair("Memory Independent Stalls", "Memory Independent Stalls")
        self.colstore["cpl"] = ColumnPair("CPL", "CPL")

        self.colstore["stall"] = ColumnPair("Actual Stall", "Stall Estimate")
        self.colstore["cwp"] = ColumnPair("CWP", "CWP")
        self.colstore["writestall"] = ColumnPair("Write Stall Cycles", "Alone Write Stall Estimate")
        self.colstore["erob"] = ColumnPair("Empty ROB Stall Cycles", "Alone Empty ROB Stall Estimate")
        
    def hasKey(self, key):
        return key in self.colstore

    def getPair(self, key):
        return self.colstore[key]

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
    traceColMatches = ColumnMatches()
    
    if traceColMatches.hasKey(command):
        pair = traceColMatches.getPair(command)
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, pair.privateColumn, pair.sharedColumn, False, True)
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