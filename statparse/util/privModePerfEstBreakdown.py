#!/usr/bin/env python

from optparse import OptionParser
from statparse.util import fatal
from statparse.tracefile.tracefileData import TracefileData

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
    
    #TODO: Add support for validating the S-loads component
    #estimateMap["CPL"] = ValueMap()
    #estimateMap["S-priv-memsys"] = ValueMap()
    #estimateMap["L-avg-shared"] = ValueMap()
    #estimateMap["L-avg-priv"] = ValueMap()
    #estimateMap["CWP"] = ValueMap()
    
    return estimateMap

def parseArgs():
    parser = OptionParser("privModePerfEstBreakdown.py [options] sample-inst-committed shared-mode-trace private-mode-trace")

    #parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    
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

def main():
    opts, args = parseArgs()
    
    instSample = args[0]
    sharedTrace = readTraceFile(args[1])
    privateTrace = readTraceFile(args[2])
    
    smValues = retrieveValues(sharedTrace, instSample, ValueMap.SHARED_MODE)
    pmValues = retrieveValues(privateTrace, instSample, ValueMap.PRIVATE_MODE)
    
    # TODO: Print the results as a table with per-component errors
    print smValues
    print pmValues
    

if __name__ == '__main__':
    main()
