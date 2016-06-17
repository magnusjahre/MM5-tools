#!/usr/bin/env python

import sys
from optparse import OptionParser
from statparse.util import fatal
from statparse.tracefile.tracefileData import TracefileData
from statparse.printResults import printData, numberToString
from statparse.tracefile.errorStatistics import computeError

class ValueMap:
    
    PRIVATE_MODE = "private"
    SHARED_MODE = "shared"
    
    def __init__(self, smColumnName, pmColumnName):
        self.smColumnName = smColumnName
        self.pmColumnName = pmColumnName
        
    def getValue(self, mode):
        if mode == ValueMap.PRIVATE_MODE:
            return self.pmColumnName
        elif mode == ValueMap.SHARED_MODE:
            return self.smColumnName
        fatal("Unknown mode")

def getEstimateMap():
    estimateMap = {}
    estimateMap["I"] = ValueMap("Cummulative Committed Instructions", "Cummulative Committed Instructions")
    estimateMap["C"] = ValueMap("Compute Cycles", "Compute Cycles")
    estimateMap["S-ind"] = ValueMap("Memory Independent Stalls", "Memory Independent Stalls")
    estimateMap["S-store"] = ValueMap("Alone Write Stall Estimate", "Write Stall Cycles")
    estimateMap["S-blocked"] = ValueMap("Alone Private Blocked Stall Estimate", "Private Blocked Stall Cycles")
    estimateMap["S-emptyROB"] = ValueMap("Alone Empty ROB Stall Estimate", "Empty ROB Stall Cycles")
    estimateMap["S-loads"] = ValueMap("Stall Estimate", "Stall Cycles")
    estimateMap["IPC"] = ValueMap("Estimated Alone IPC", "Measured Alone IPC")
    
    #TODO: Add support for validating the S-loads component
    #estimateMap["CPL"] = ValueMap()
    #estimateMap["S-priv-memsys"] = ValueMap()
    #estimateMap["L-avg-shared"] = ValueMap()
    #estimateMap["L-avg-priv"] = ValueMap()
    #estimateMap["CWP"] = ValueMap()
    
    return estimateMap

def parseArgs():
    parser = OptionParser("privModePerfEstBreakdown.py [options] sample-inst-committed shared-mode-trace private-mode-trace")

    parser.add_option("--absolute", action="store_false", dest="relative", default=True, help="Use absolute error (relative error is default)")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    
    opts, args = parser.parse_args()
    
    if len(args) != 3:
        fatal("command line error\nUsage: "+parser.usage)
    
    return opts,args

def readTraceFile(filename):
    
    tracefile = TracefileData(filename)
    
    try:
        tracefile.readTracefile()
    except IOError:
        fatal("File "+filename+" cannot be opened...")
    return tracefile

def findRowID(trace, instSample):
    colID = trace.findColumnID("Cummulative Committed Instructions", -1)
    rowID = trace.getRowIDByValue(colID, instSample)
    if rowID == -1:
        fatal("Instruction value not found in file "+trace.filename)
    return rowID

def getDataValue(trace, columnTitle, rowID):
    colID = trace.findColumnID(columnTitle, -1)
    return trace.getValue(colID, rowID)

def retrieveValues(trace, instSample, mode):
    valueMap = {}
    
    rowID = findRowID(trace, instSample)

    estimateMap = getEstimateMap()
    for k in estimateMap:
        assert k not in valueMap
        colTitle = estimateMap[k].getValue(mode)
        valueMap[k] = getDataValue(trace, colTitle, rowID)

    if rowID > 0:
        prevComInsts = getDataValue(trace, "Cummulative Committed Instructions", rowID-1)
        valueMap["I"] = valueMap["I"] - prevComInsts
    return valueMap

def computeIPCEstimate(smValues):
    cyclesOther = smValues["S-store"] + smValues["S-blocked"] + smValues["S-emptyROB"]
    cyclesAll = smValues["C"] + smValues["S-ind"] + smValues["S-loads"] + cyclesOther
    return smValues["I"] / cyclesAll

def printErrorTable(smValues, pmValues, opts, components):
    
    header = ["Component", "Shared Mode", "Private Mode"]
    if opts.relative:
        header.append("Error (%)")
    else:
        header.append("Error")
    
    justify = [True, False, False, False]
    data = [header]
    for c in components:
        line = [c]
        line.append(numberToString(smValues[c], opts.decimals))
        line.append(numberToString(pmValues[c], opts.decimals))
        line.append(numberToString(computeError(smValues[c], pmValues[c], opts.relative, -1), opts.decimals))
        data.append(line)
    
    printData(data, justify, sys.stdout, opts.decimals)

def printCoreErrors(smValues, pmValues, opts):
    
    aloneIPCEst = computeIPCEstimate(smValues)
    assert "%.6f" % aloneIPCEst == "%.6f" % smValues["IPC"], "Value mismatch for alone IPC estimate"
    
    components = ["I", "C", "S-ind", "S-loads", "S-store", "S-blocked", "S-emptyROB", "IPC"]
    printErrorTable(smValues, pmValues, opts, components)

def main():
    opts, args = parseArgs()
    
    instSample = args[0]
    sharedTrace = readTraceFile(args[1])
    privateTrace = readTraceFile(args[2])
    
    smValues = retrieveValues(sharedTrace, instSample, ValueMap.SHARED_MODE)
    pmValues = retrieveValues(privateTrace, instSample, ValueMap.PRIVATE_MODE)
    
    printCoreErrors(smValues, pmValues, opts)

if __name__ == '__main__':
    main()
