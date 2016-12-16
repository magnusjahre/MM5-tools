#!/usr/bin/env python
import sys
import os
import re

from optparse import OptionParser
from statparse.tracefile.tracefileData import TracefileData
from workloadfiles.workloads import Workloads
from statparse.plotResults import plotLines

class CacheTraceFileNames:
    
    MISSES = 0
    PERFORMANCE = 1
    SPEEDUP = 2
    
    titles = ["misses", "perf", "speedup"]
    
    def __init__(self):
        self.filenamePatterns = {self.MISSES: "globalPolicyMissCurveTrace",
                                 self.PERFORMANCE: "globalPolicyPerformanceCurveTrace",
                                 self.SPEEDUP: "globalPolicySpeedupCurveTrace"}
        
        
    def getFilenames(self, traceType, np):
        basename = self.filenamePatterns[traceType]
        filenames = []
        for i in range(np):
            filenames.append(basename+str(i)+".txt")
        return filenames
    
    def parseTypeString(self, typeString):
        if typeString == self.titles[self.PERFORMANCE]:
            return self.PERFORMANCE
        if typeString == self.titles[self.SPEEDUP]:
            return self.SPEEDUP
        if typeString == self.titles[self.MISSES]:
            return self.MISSES
        
        raise Exception("Unknown parse string, should be perf, speedup or misses")

def parseArgs():
    parser = OptionParser(usage="analyzeCacheAllocation.py [options] result-directory million-cc-sample-point")

    parser.add_option("-q", "--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--type", action="store", dest="type", default="speedup", help="Trace type to use, either perf, speedup or misses")
    parser.add_option("--np", action="store", dest="np", default=4, help="Trace type to use, either perf, speedup or misses")
    parser.add_option("--yrange", action="store", dest="yrange", default="", help="Y-axis range")
    parser.add_option("--plotfile", action="store", dest="plotfile", default="", help="Plot to this file (single plot)")
    parser.add_option("--plotdir-prefix", action="store", dest="plotdirprefix", default="cache-analysis", help="Prefix of cache analysis directories (full plot)")
    parser.add_option("--verify", action="store_true", dest="verify", default=False, help="Verify the lookahead allocation algorithm")
    parser.add_option("--gen-curve-code", action="store_true", dest="genCurveCode", default=False, help="Print code for testing the C++ lookahead implementation")
    
    opts, args = parser.parse_args()
    
    if len(args) < 2:
        print "Command line error"
        print "Usage: "+parser.usage
        sys.exit(-1)
    
    if not os.path.exists(args[0]):
        print "Directory "+str(args[0])+" does not exist"
        sys.exit(-1)
    
    try:
        millccpoint = int(args[1])
    except:
        print "Cannot parse clock cycle sample point "+str(args[1])
        sys.exit(-1)
        
    return opts,args[0],millccpoint*(10**6)

def getCurve(directory, tracefilename, numTicks):
    tracecontent = TracefileData(directory+"/"+tracefilename)
    tracecontent.readTracefile()
    colID = tracecontent.findColumnID("Tick", -1)
    rowID = tracecontent.getRowIDByValue(colID, numTicks)
    row = tracecontent.getRow(rowID)
    return row[1:]

def getAllocation(directory, numTicks):
    tracecontent = TracefileData(directory+"/globalPolicyAllocationTrace.txt")
    tracecontent.readTracefile()
    colID = tracecontent.findColumnID("Tick", -1)
    rowID = tracecontent.getRowIDByValue(colID, numTicks)
    row = tracecontent.getRow(rowID)
    return row[1:]

def getSamplePoints(directory, tracefilename):
    print directory+"/"+tracefilename
    tracecontent = TracefileData(directory+"/"+tracefilename)
    tracecontent.readTracefile()
    colID = tracecontent.findColumnID("Tick", -1)
    return tracecontent.getColumn(colID)

def getBenchmarkNames(directory, np):
    wls = Workloads()
    match = re.search("t-[hmls]-[0-9]+", directory)
    wl = match.group(0)
    bms =  wls.getBms(wl, np)
    return wl, bms

def getAllocPoints(usedir, ccpoint, curves, opts, bms):
    allocation = getAllocation(usedir, ccpoint)
    allocPoints = []
    for i in range(len(allocation)):
        xcoord = int(allocation[i])
        ycoord = curves[i][xcoord-1]
        allocPoints.append( (xcoord,ycoord) )
    
    if not opts.quiet:
        print "Allocation in "+usedir+" at "+str(ccpoint/(10**6))+" million clock cycles:"
        for i in range(len(allocation)):
            print ("CPU"+str(i)+" "+bms[i]).ljust(20)+str(int(allocation[i])).rjust(3)
    return allocPoints

def plotCurves(curves, usedir, bms, opts, samplePoint, allocPoints, tracetype, plotfilename):
    xdata = []
    for i in range(len(curves)):
        assoc = len(curves[i])
        wayrange = range(1, len(curves[i])+1)
        xdata.append(wayrange)
    
    pretitle = usedir.replace("res-4-","")
    pretitle = pretitle.replace("/","")
    
    title = tracetype+": "+pretitle+" at "+str(samplePoint/(10**6))+" million clock cycles"
    
    yrange = opts.yrange
    if yrange == "":
        maxvals = []
        for c in curves:
            maxvals.append(max(c))
        yrange = "0,"+str(max(maxvals)*1.25)

    plotLines(xdata, curves, legendTitles=bms, title=title, yrange=yrange, showPoints=allocPoints, filename=plotfilename)

def analyzeCCPoint(usedir, ccpoint, opts, traceFileNames, bms, plotfilename):
    curves = []
    for tfn in traceFileNames:
        curves.append(getCurve(usedir, tfn, ccpoint))
    
    if opts.verify:
        verifyAllocation(curves, opts, usedir, ccpoint)
    
    allocPoints = getAllocPoints(usedir, ccpoint, curves, opts, bms) 
    plotCurves(curves, usedir, bms, opts, ccpoint, allocPoints, opts.type, plotfilename)

def padSample(sample):
    sampleStr = str(int(sample))
    while len(sampleStr) <= 10:
        sampleStr = "0"+sampleStr
    return sampleStr

def getCurveIndex(ways):
    return ways-1

def getMarginalUtility(curve, curAlloc, newAlloc):
    numerator = curve[getCurveIndex(newAlloc)] - curve[getCurveIndex(curAlloc)]
    denominator = float(newAlloc - curAlloc)
    mu = numerator/denominator
    return mu

def getMaxMarginalUtility(curve, curAlloc, balance):
    maxMu = -1.0
    maxAdditionalWays = -1
    additionalWays = 1
    while additionalWays <= balance:
        newAlloc = curAlloc+additionalWays
        mu = getMarginalUtility(curve, curAlloc, newAlloc)
        if mu > maxMu:
            maxMu = mu
            maxAdditionalWays = additionalWays
        additionalWays += 1

    return maxAdditionalWays, maxMu

def printCurvesForM5(curves):
    print "C++ curve intialization for simulator test:"
    print
    for i in range(len(curves)):
        print "double arr"+str(i)+"[] = {",
        first = True
        for v in curves[i]:
            if first:
                print str(v),
                first = False
            else:
                print ","+str(v),
        print "};"
    print
    print "vector<vector<double>> utilities = vector<vector<double>>(cpuCount, vector<double>());"
    for i in range(len(curves)):
        print "utilities["+str(i)+"] = vector<double>(arr"+str(i)+", arr"+str(i)+" + sizeof(arr"+str(i)+") / sizeof(arr"+str(i)+"[0]));"
    print


def verifyAllocation(curves, opts, usedir, ccpoint):
    
    if opts.genCurveCode:
        printCurvesForM5(curves)
    
    maxWays = len(curves[0])
    curAlloc = [1 for c in curves]
    balance = maxWays - sum(curAlloc)
    allocRound = 1
    
    while balance > 0:
        print "Allocation round", allocRound
        winner = -1
        maxMUAdditionalWays = -1
        maxMU = -1.0
        for i in range(len(curves)):
            coreMaxAdditionalWays, coreMaxMu = getMaxMarginalUtility(curves[i], curAlloc[i], balance)
            print "Maximum utility for CPU "+str(i)+" is "+str(coreMaxMu)+" with "+str(coreMaxAdditionalWays)+" additional ways"
            if coreMaxMu > maxMU:
                winner = i
                maxMUAdditionalWays = coreMaxAdditionalWays
                maxMU = coreMaxMu
        
        print "CPU "+str(winner)+" wins, increasing allocation by "+str(maxMUAdditionalWays)+" ways"
        assert maxMUAdditionalWays > 0
        curAlloc[winner] += maxMUAdditionalWays 
        balance -= maxMUAdditionalWays
        
        print "Allocation is now "+str(curAlloc)+", "+str(balance)+" ways remaining"
        assert balance == maxWays - sum(curAlloc)
        allocRound += 1
    
    assert sum(curAlloc) == maxWays
    traceAlloc = [int(v) for v in getAllocation(usedir, ccpoint)]
    print "Verification allocation is", curAlloc
    print "Trace allocation is", traceAlloc
    
    tracesEqual = True
    assert(len(curAlloc) == len(traceAlloc))
    for i in range(len(curAlloc)):
        if curAlloc[i] != traceAlloc[i]:
            tracesEqual = False
    
    print "\nVERIFICATION",
    if tracesEqual:
        print "PASSED\n"
    else:
        print "FAILED\n"
    
    return curAlloc

def main():

    opts,usedir,ccpoint = parseArgs()
    
    if not opts.quiet:
        print
        print "Running cache allocation analysis..."
        print
    
    ctfn = CacheTraceFileNames()
    traceFileType = ctfn.parseTypeString(opts.type)
    traceFileNames = ctfn.getFilenames(traceFileType, opts.np)
    
    wl, bms = getBenchmarkNames(usedir, opts.np)
    
    if ccpoint != 0:
        analyzeCCPoint(usedir, ccpoint, opts, traceFileNames, bms, opts.plotfile)
    else:
        plotdirpath = opts.plotdirprefix+"-"+usedir
        if os.path.exists(plotdirpath):
            print "FATAL: plot directory "+plotdirpath+" exists"
            sys.exit(-1)
        
        os.mkdir(plotdirpath)
        print "Plotting to directory "+plotdirpath
        
        sampleTicks = getSamplePoints(usedir, traceFileNames[0])
        for s in sampleTicks:
            plotfile = wl+"-"+padSample(s)+".pdf"
            print "Processing file "+plotfile
            analyzeCCPoint(usedir, s, opts, traceFileNames, bms, plotdirpath+"/"+plotfile)

if __name__ == '__main__':
    main()