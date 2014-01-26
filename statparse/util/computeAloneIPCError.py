#!/usr/bin/env python

import sys
from statparse.util import fatal, getNpExperimentDirs, computeTraceError, parseUtilArgs, getPrivateModeDirs, computePrivateTraceError
from statparse.tracefile.errorStatistics import plotBoxFromDict, dumpAllErrors
import statparse.tracefile.errorStatistics as errorStats
from statparse.printResults import numberToString, printData

commands = ["IPC", "latency", "overlap", "compute", "privlat", "memind", "cpl", "stall", "cwp", "writestall", "erob", "model", "privmemstall", "missrate"]
privateCommands = ["pm-cpl", "pm-cpl-cwp"]
modelComponentCmds = ["compute", "memind", "writestall", "erob", "privmemstall", "stall"]
modelComponentNames = ["Compute Cycle Error", "Memory Independent Stall Error", "Write Stall Error", "Empty ROB Stall Error" , "Private Memsys Stall Error", "Shared Memsys Stall Error"]

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
        self.colstore["latency"] = ColumnPair("Alone Memory Latency", "Estimated Private Latency")
        self.colstore["overlap"] = ColumnPair("Measured Alone Overlap", "Estimated Alone Overlap")

        self.colstore["compute"] = ColumnPair("Compute Cycles", "Compute Cycles")
        self.colstore["privlat"] = ColumnPair("Private Stall Cycles", "Private Stall Cycles")
        self.colstore["memind"] = ColumnPair("Memory Independent Stalls", "Memory Independent Stalls")
        self.colstore["cpl"] = ColumnPair("Graph CPL", "Table CPL")

        self.colstore["stall"] = ColumnPair("Actual Stall", "Stall Estimate")
        self.colstore["cwp"] = ColumnPair("CWP", "CWP")
        self.colstore["writestall"] = ColumnPair("Write Stall Cycles", "Alone Write Stall Estimate")
        self.colstore["erob"] = ColumnPair("Empty ROB Stall Cycles", "Alone Empty ROB Stall Estimate")
        
        self.colstore["privmemstall"] = ColumnPair("Private Blocked Stall Cycles", "Alone Private Blocked Stall Estimate")
        self.colstore["missrate"] = ColumnPair("Measured Private Mode Miss Rate", "Private Mode Miss Rate Estimate")
        
        self.colstore["pm-cpl"] = ColumnPair("Actual Stall", "CPL Stall Estimate")
        self.colstore["pm-cpl-cwp"] = ColumnPair("Actual Stall", "CPL-CWP Stall Estimate")
        
    def hasKey(self, key):
        return key in self.colstore

    def getPair(self, key):
        return self.colstore[key]

def printModelRes(modelRes, sortedparams, workloads, statistic, decimals, doPercentage):
    header = [""]
    justify = [True]
    for p in modelComponentNames:
        header.append(p)
        justify.append(False)
    
    lines = [header]
    
    for w in workloads:
        for p in sortedparams:
            line = [w+"-"+p]
            vals = []
            for i in range(len(modelRes)):
                vals.append(modelRes[i][w][p].getStatByName(statistic))
                
            if doPercentage:
                errsum = 0.0
                for i in range(len(vals)):
                    vals[i] = abs(vals[i])
                    errsum += float(vals[i])
                
                for i in range(len(vals)):
                    if errsum != 0.0:
                        vals[i] = (vals[i]/errsum)*100
                    else:
                        vals[i] = 0.0
            
            for v in vals:
                line.append(numberToString(v, decimals))
            lines.append(line)
            
    printData(lines, justify, sys.stdout, decimals)

def printResults(results, aggRes, sortedparams, statname, opts, outfile):
    if opts.printType == "all":
        errorStats.printParamErrorStatDict(results, sortedparams, statname, opts.relativeErrors, opts.decimals, outfile)
    elif opts.printType == "distribution":
        errorStats.printParamErrorStatDistribution(results, sortedparams, statname, opts.relativeErrors, opts.decimals, outfile)
    else:
        assert opts.printType == "statistics"
        errorStats.printErrorStatDict(aggRes, opts.relativeErrors, opts.decimals, sortedparams, outfile)            

def main():

    allcommands = commands + privateCommands

    opts,args = parseUtilArgs("computeAloneIPCError.py", allcommands)
    try:
        np = int(args[0])
    except:
        fatal("Number of CPUs must be an integer")
    
    statname = args[1]
    command = None
    if len(args) == 3:
        command = args[2]
    
    if not opts.quiet:
        print
        print "Committed Instruction Synchronized Estimation Accuracy"
        print
    
    dirs, sortedparams = getNpExperimentDirs(np)
    privdirs = getPrivateModeDirs()
    traceColMatches = ColumnMatches()

    if command == "model":
        modelRes = []
        workloads = []
        first = True
        for cmd in modelComponentCmds: 
            if not opts.quiet:
                print "Processing command",cmd
            
            pair = traceColMatches.getPair(cmd)
            res, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, pair.privateColumn, pair.sharedColumn, False, True)
            
            if first:
                workloads = res.keys()
                workloads.sort()
                first = False
            modelRes.append(res)
        
        printModelRes(modelRes, sortedparams, workloads, statname, opts.decimals, opts.relativeErrors)
        return

    elif command != None:
        pair = traceColMatches.getPair(command)
        if command in commands:
            results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, pair.privateColumn, pair.sharedColumn, False, True)
            printResults(results, aggRes, sortedparams, statname, opts, sys.stdout)
        else:
            assert command in privateCommands
            results, aggRes = computePrivateTraceError(privdirs, pair.privateColumn, pair.sharedColumn, getTracename, opts.relativeErrors)
            printResults(results, aggRes, ["Alone"], statname, opts, sys.stdout)
        
        if opts.plotBox:
            plotBoxFromDict(results, opts.hideOutliers, sortedparams)
            
        if opts.allErrorFile:
            dumpAllErrors(results, opts.allErrorFile)
        return
    
    if not opts.quiet:
        print "Printing all error components to files"
    
    relstr = "abs"
    if opts.relativeErrors:
        relstr = "rel"
    
    for cmd in allcommands:
        if cmd == "model":
            continue
        
        outname = "error-"+str(np)+"-"+statname+"-"+opts.printType+"-"+relstr+"-"+cmd+".txt"
        outfile = open(outname, "w") 
        if not opts.quiet:
            print "Processing command "+cmd+": Writing output to file "+outname
        pair = traceColMatches.getPair(cmd)
        
        if cmd in commands:
            res, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, pair.privateColumn, pair.sharedColumn, False, True)
            printResults(res, aggRes, sortedparams, statname, opts, outfile)
        else:
            assert cmd in privateCommands
            results, aggRes = computePrivateTraceError(privdirs, pair.privateColumn, pair.sharedColumn, getTracename, opts.relativeErrors)
            printResults(results, aggRes, ["Alone"], statname, opts, outfile)
        
        outfile.close()


if __name__ == '__main__':
    main()