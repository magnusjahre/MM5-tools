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
        yrange = "0,"+str(max(max(curves))*1.25)

    plotLines(xdata, curves, legendTitles=bms, title=title, yrange=yrange, showPoints=allocPoints, filename=plotfilename)

def analyzeCCPoint(usedir, ccpoint, opts, traceFileNames, bms, plotfilename):
    curves = []
    for tfn in traceFileNames:
        curves.append(getCurve(usedir, tfn, ccpoint))
    
    allocPoints = getAllocPoints(usedir, ccpoint, curves, opts, bms)
    plotCurves(curves, usedir, bms, opts, ccpoint, allocPoints, opts.type, plotfilename)

def padSample(sample):
    sampleStr = str(int(sample))
    while len(sampleStr) <= 10:
        sampleStr = "0"+sampleStr
    return sampleStr

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