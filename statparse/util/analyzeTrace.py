#!/usr/bin/env python
import sys
import os

from optparse import OptionParser
from statparse.tracefile.tracefileData import TracefileData
from statparse.util import getNpExperimentDirs
import statparse.tracefile.tracefileData as tracefileModule
import statparse.printResults as printResults
import traceback

CMDS = ["max", "diff"]

def parseArgs():
    parser = OptionParser(usage="formatTrace.py [options] cmd filename")

    parser.add_option("-c", "--column", action="store", dest="column", default=0, type="int", help="The column ID to perform analysis on")
    parser.add_option("--np", action="store", dest="np", default=0, type="int", help="The number of cores")
    parser.add_option("--decimals", action="store", dest="decimals", default=0, type="int", help="Decimals to print")
    parser.add_option("-n", "--names", action="store_true", dest="printNames", default=False, help="Print the names and numbers of each column")
    
    opts, args = parser.parse_args()
    
    if args[0] not in CMDS:
        print "Unknown command, must be one of: "+(" ".join(CMDS))
        print "Usage: "+parser.usage
        sys.exit(-1)
    
    if len(args) != 2:
        print "Command line error"
        print "Usage: "+parser.usage
        sys.exit(-1)
    
    return opts,args

def findMaxDiff(column):
    
    maxdiff = column[0]
    for i in range(len(column))[1:]:
        diff = column[i] - column[i-1]
        if diff > maxdiff:
            maxdiff = diff

    return maxdiff

def getCommandValue(command, column):
    if command == "max":
        return max(column)
    elif command == "diff":
        return findMaxDiff(column)
    else:
        fatal("Unknown command")
    

def handleSingleFile(command, filename, opts):
    
    if not os.path.exists(filename):
        print "Error: File "+str(filename)+" not found"
        return -1

    tracecontent = TracefileData(filename)
    tracecontent.readTracefile()
    
    if opts.printNames:
        print
        print "Column mapping for file "+tracecontent.filename
        tracecontent.printColumnMapping()
    else:
        
        print "Command "+command+" gave value "+str(getCommandValue(command, column))
            
def handleExperiment(command, filebase, opts):
    data = {}
    dirdata, params = getNpExperimentDirs(opts.np)
    for wl, params, sharedID, aloneIDs in dirdata:
        for i in range(opts.np):
            filename =  sharedID+"/"+filebase+str(i)+".txt"
            
            tracecontent = TracefileData(filename)
            tracecontent.readTracefile()
            column = tracecontent.getColumn(opts.column)
            
            data[sharedID] = getCommandValue(command, column)
            
    return data

def printData(data, opts):
    lines = []
    lines.append(["", "Command value"])
    justify = [True, False]
    
    keys = sorted(data.keys())
    for k in keys:
        line = [k, printResults.numberToString(data[k], opts.decimals)]
        lines.append(line)
        
    line = ["Max", printResults.numberToString(max(data.values()), opts.decimals)]
    lines.append(line)
    
    printResults.printData(lines, justify, sys.stdout, opts.decimals)

def main():

    opts,args = parseArgs()
    
    command = args[0]
    
    if opts.np == 0:
        handleSingleFile(command, args[1], opts)
    else:
        data = handleExperiment(command, args[1], opts)
        printData(data, opts)
    
if __name__ == '__main__':
    main()