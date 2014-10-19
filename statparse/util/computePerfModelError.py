#!/usr/bin/env python

import sys
from statparse.util import fatal, getSingleCoreExpDirs, parseUtilArgs, computeSingleCoreTraceError
from statparse.util.computeAloneIPCError import printResults

commands = ["little", "graph-burst", "graph-sat", "histogram-burst", "histogram-sat"]

class ColumnPair:
    def __init__(self, actualcol, modelcol):
        self.actualColumn = actualcol
        self.modelColumn = modelcol

class ColumnMatches:
    def __init__(self):
        self.colstore = {}
        self.populateColstore()
        
    def populateColstore(self):
        self.colstore["little"] = ColumnPair("Actual Bus Latency", "Little's Law Bus Latency")
        self.colstore["graph-burst"] = ColumnPair("Actual Bus Latency", "Graph Model Bus Latency \(burst\)")
        self.colstore["graph-sat"] = ColumnPair("Actual Bus Latency", "Graph Model Bus Latency \(sat\)")
        self.colstore["histogram-burst"] = ColumnPair("Actual Bus Latency", "Histogram Model Bus Latency \(burst\)")
        self.colstore["histogram-sat"] = ColumnPair("Actual Bus Latency", "Histogram Model Bus Latency \(sat\)")

    def hasKey(self, key):
        return key in self.colstore

    def getPair(self, key):
        return self.colstore[key]
    
def getTracename(dir, cpuID, sharedMode):
    prefix = "globalPolicyCommittedInsts"
    postfix = ".txt"
    
    return dir+"/"+prefix+"0"+postfix

def computePerfModelError(command, statname, dirs, sortedparams, opts):
    traceColMatches = ColumnMatches()
    
    if opts.outfile == "":
        outfile = sys.stdout
    else:
        outfile = open(opts.outfile, "w")
        
    pair = traceColMatches.getPair(command)
    
    results, aggRes = computeSingleCoreTraceError(dirs,
                                                  pair.actualColumn,
                                                  pair.modelColumn,
                                                  getTracename,
                                                  opts.relativeErrors,
                                                  sortedparams)
     
    printResults(results, aggRes, sortedparams, statname, opts, outfile)
            
    if opts.outfile != "":
        outfile.close()
    

def main():
    opts,args = parseUtilArgs("computeAloneIPCError.py", commands)
    try:
        np = int(args[0])
    except:
        fatal("Number of CPUs must be an integer")
        
    if not np == 1:
        fatal("Only one core experiments are supported")
    
    statname = args[1]
    command = None
    if len(args) == 3:
        command = args[2]
    
    if not opts.quiet:
        print
        print "Performance Model Instruction Synchronized Estimation Accuracy"
        print
    
    dirs, sortedparams = getSingleCoreExpDirs()
    
    if command == None:
        fatal("Computing all errors is not implemented")
    else:
        computePerfModelError(command, statname, dirs, sortedparams, opts)

if __name__ == '__main__':
    main()