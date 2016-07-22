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

def plotCurves(curves, usedir, bms, opts, samplePoint, allocPoints, tracetype):
    xdata = []
    for i in range(len(curves)):
        assoc = len(curves[i])
        wayrange = range(1, len(curves[i])+1)
        xdata.append(wayrange)
    
    pretitle = usedir.replace("res-4-","")
    pretitle = pretitle.replace("/","")
    
    title = tracetype+": "+pretitle+" at "+str(samplePoint/(10**6))+" million clock cycles"
    
    plotLines(xdata, curves, legendTitles=bms, title=title, yrange=opts.yrange, showPoints=allocPoints)

def main():

    opts,usedir,ccpoint = parseArgs()
    
    if not opts.quiet:
        print
        print "Running cache allocation analysis..."
        print
    
    ctfn = CacheTraceFileNames()
    traceFileType = ctfn.parseTypeString(opts.type)
    traceFileNames = ctfn.getFilenames(traceFileType, opts.np)
    
    curves = []
    for tfn in traceFileNames:
        curves.append(getCurve(usedir, tfn, ccpoint))
        
    allocation = getAllocation(usedir, ccpoint)
    allocPoints = []
    for i in range(len(allocation)):
        xcoord = int(allocation[i])
        ycoord = int(curves[i][xcoord])
        allocPoints.append( (xcoord,ycoord) )
    
    wl, bms = getBenchmarkNames(usedir, opts.np)
    allocPoints = getAllocPoints(usedir, ccpoint, curves, opts, bms)
    plotCurves(curves, usedir, bms, opts, ccpoint, allocPoints, opts.type)

if __name__ == '__main__':
    main()