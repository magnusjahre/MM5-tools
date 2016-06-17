#!/usr/bin/env python

import sys
from optparse import OptionParser
from statparse.util import fatal
from statparse.tracefile.tracefileData import TracefileData, computeErrors
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
    
    estimateMap["table-CPL"] = ValueMap("Table CPL", "Table CPL")
    estimateMap["graph-CPL"] = ValueMap("Graph CPL", "Graph CPL")
    estimateMap["S-priv-memsys"] = ValueMap("Private Stall Cycles","Private Stall Cycles")
    estimateMap["L-avg-shared"] = ValueMap("Estimated Private Latency","Alone Memory Latency")
    estimateMap["L-avg-priv"] = ValueMap("Average Shared Private Memsys Latency","Average Alone Private Memsys Latency")
    estimateMap["CWP"] = ValueMap("CWP","CWP")
    
    return estimateMap

def parseArgs():
    parser = OptionParser("privModePerfEstBreakdown.py [options] shared-mode-trace private-mode-trace")

    parser.add_option("--absolute", action="store_false", dest="relative", default=True, help="Use absolute error (relative error is default)")
    parser.add_option("--graphCPL", action="store_true", dest="graphCPL", default=False, help="Use graph CPL (table CPL is default)")
    parser.add_option("--useCWP", action="store_true", dest="useCWP", default=False, help="Use cycles while pending in estimate")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--insts", action="store", dest="insts", type="int", default=-1, help="Print detailed error breakdown for sample identified by this instruction count")
    parser.add_option("--component", action="store", dest="component", default="IPC", help="The component to print the error breakdown for")
    parser.add_option("--colIdent", action="store", dest="colIdent", default="Error", help="Identifier for the error column (useful to highlight the differences between files)")
    parser.add_option("--outfile", action="store", dest="outfile", default="", help="Name of the outputfile (default is standard out)")
    
    opts, args = parser.parse_args()
    
    if len(args) != 2:
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
        
    valueMap["CPI"] = 1.0 / valueMap["IPC"]
    return valueMap

def printErrorTable(smValues, pmValues, opts, components, doCPIAnalysis):
    
    header = ["Component", "Shared Mode", "Private Mode"]
    if opts.relative:
        header.append("Error (%)")
    else:
        header.append("Error")
    if doCPIAnalysis:
        header.append("Est. CPI Stack Val.")
        header.append("Est. CPI Stack Share (%)")
        header.append("Act. CPI Stack Val.")
        header.append("Act. CPI Stack Share (%)")
        
        # The instruction value is cancelled in the relative error computation. Therefore, the relative 
        # error value is exactly the same as the stall cycle relative error. The absolute error is different
        # and a good measure of the absolute importance of each stall component.
        if not opts.relative:
            header.append("CPI Stack Error")
    
    justify = [True, False, False, False]
    if doCPIAnalysis:
        justify = justify + [False, False, False, False]
        if not opts.relative:
            justify.append(False)
    data = [header]
    for c in components:
        line = [c]
        line.append(numberToString(smValues[c], opts.decimals))
        line.append(numberToString(pmValues[c], opts.decimals))
        line.append(numberToString(computeError(smValues[c], pmValues[c], opts.relative, -1), opts.decimals))
        if doCPIAnalysis:
            if c == "I" or c == "IPC" or c == "CPI":
                pass
            else:
                estCpiComp = smValues[c] / smValues["I"]
                line.append(numberToString(estCpiComp, opts.decimals))
                line.append(numberToString(100*estCpiComp / smValues["CPI"], opts.decimals))
                
                actCpiComp = pmValues[c] / pmValues["I"]
                line.append(numberToString(actCpiComp, opts.decimals))
                line.append(numberToString(100*actCpiComp / pmValues["CPI"], opts.decimals))
                
                if not opts.relative:
                    line.append(numberToString(computeError(estCpiComp, actCpiComp, opts.relative, -1), opts.decimals))
                
        data.append(line)
    
    printData(data, justify, sys.stdout, opts.decimals)

def computeIPCEstimate(smValues):
    cyclesOther = smValues["S-store"] + smValues["S-blocked"] + smValues["S-emptyROB"]
    cyclesAll = smValues["C"] + smValues["S-ind"] + smValues["S-loads"] + cyclesOther
    return smValues["I"] / cyclesAll

def printCoreErrors(smValues, pmValues, opts):
    
    aloneIPCEst = computeIPCEstimate(smValues)
    assert "%.3f" % aloneIPCEst == "%.3f" % smValues["IPC"], "Value mismatch for alone IPC estimate"
    
    components = ["I", "C", "S-ind", "S-loads", "S-store", "S-blocked", "S-emptyROB", "IPC", "CPI"]
    printErrorTable(smValues, pmValues, opts, components, True)
 
def computeStallEstimate(smValues, opts):
    avgLat = smValues["L-avg-shared"] + smValues["L-avg-priv"]
    if opts.useCWP:
        avgLat = avgLat - smValues["CWP"]
    
    cpl = smValues["table-CPL"]
    if opts.graphCPL:
        cpl = smValues["graph-CPL"]
    
    return smValues["S-priv-memsys"] + cpl*avgLat
    
def printStallEstimateErrors(smValues, pmValues, opts):
    
    aloneStallEstimate = computeStallEstimate(smValues, opts)
    if "%.2f" % aloneStallEstimate != "%.2f" % smValues["S-loads"]:
        fatal("Value mismatch for alone stall estimate. Are you using the correct policy?")
    
    components = ["S-priv-memsys", "L-avg-shared", "L-avg-priv"]
    if opts.graphCPL:
        components.append("graph-CPL")
    else:
        components.append("table-CPL")
        
    if opts.useCWP:
        components.append("CWP")
    components.append("S-loads")
    
    printErrorTable(smValues, pmValues, opts, components, False)

def printDetailedErrorReport(sharedTrace, privateTrace, opts):
    smValues = retrieveValues(sharedTrace, opts.insts, ValueMap.SHARED_MODE)
    pmValues = retrieveValues(privateTrace, opts.insts, ValueMap.PRIVATE_MODE)
    
    print
    print "Core Alone IPC Estimate Errors:"
    print
    printCoreErrors(smValues, pmValues, opts)
    print
    print "Alone Stall Estimate Errors:"
    print
    printStallEstimateErrors(smValues, pmValues, opts)
    print
    
def printErrorDistribution(sharedTrace, privateTrace, opts):
    estMap = getEstimateMap()
    if opts.component not in estMap:
        fatal("Unknown estimate component "+opts.component)
    errors = computeErrors(privateTrace, estMap[opts.component].pmColumnName, sharedTrace, estMap[opts.component].smColumnName, opts.relative)
    allErrors = errors.getAllErrors()
    
    instColID = sharedTrace.findColumnID(estMap["I"].smColumnName, -1)
    allInsts = sharedTrace.getColumn(instColID)


    header = ["", opts.colIdent+"-"+opts.component]
    justify = [True, False]
    
    outfile = sys.stdout
    if opts.outfile != "":
        outfile = open(opts.outfile, "w")
    
    data = [header]
    for i in range(len(allErrors)):
        line = []
        line.append(numberToString(allInsts[i], 0))
        line.append(numberToString(allErrors[i], opts.decimals))
        data.append(line)
    printData(data, justify, outfile, opts.decimals)

def main():
    opts, args = parseArgs()
    
    sharedTrace = readTraceFile(args[0])
    privateTrace = readTraceFile(args[1])
    
    if opts.insts != -1:
        printDetailedErrorReport(sharedTrace, privateTrace, opts)
    else:
        printErrorDistribution(sharedTrace, privateTrace, opts)

if __name__ == '__main__':
    main()
