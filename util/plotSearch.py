#!/usr/bin/python

import sys
from optparse import OptionParser
from util.inifile import IniFile
from statparse.tracefile.tracefileData import TracefileData

import matplotlib.pyplot as plt 
from matplotlib.pyplot import ylim

def parseArgs():
    parser = OptionParser(usage="plotSearch.py [options] metric datafile searchfile")

    parser.add_option("--verbose", action="store_true", dest="verbose", default=False, help="Verbose output")
    parser.add_option("--period", action="store", type="int", dest="period", default=2**20, help="The period size for the scheme")
    parser.add_option("--stepsize", action="store", type="int", dest="stepsize", default=1024, help="The granularity of the function plotting")
    parser.add_option("--numconts", action="store", type="int", dest="numconts", default=15, help="The number of contour lines to draw")
    
    opts, args = parser.parse_args()
    
    if len(args) != 3:
        print "Command line error"
        print "Usage: "+parser.usage
        sys.exit(-1)
    
    posargs = ["STP", "ANTT"]
    if args[0] not in posargs:
        print "Unknown metric"
        print "Alternatives are :"+str(posargs)
        sys.exit(-1)
    
    return opts,args

def computeFunctionVal(metric, modeldata, x, y):
    
    if metric == "ANTT":
        print "Metric ANTT not implemented"
        sys.exit(-1)
    
    val = modeldata.data["alone-cycles"][0] / (modeldata.data["beta"][0] + (modeldata.data["alpha"][0]/x))
    val += modeldata.data["alone-cycles"][1] / (modeldata.data["beta"][1] + (modeldata.data["alpha"][1]/y))
    
    return val 


class ModelPlotData:
    def __init__(self, opts):
        self.xvals = []
        self.yvals = []
        self.zvals = []
        self.constraintvals = []
        self.xlimit = []
        self.ylimit = []
        self.xsearch = []
        self.ysearch = []
        
        self.opts = opts

    def setSearchPoints(self, searchTrace):
        xid = searchTrace.findColumnID("CPU", 0)
        yid = searchTrace.findColumnID("CPU", 1)
        
        self.xsearch = searchTrace.getColumn(xid)
        self.ysearch = searchTrace.getColumn(yid)
    
    def plot(self):
        plt.figure()
        cs = plt.contour(self.xvals, self.yvals,self.zvals, self.opts.numconts)
        plt.clabel(cs, inline=1, fontsize=10)
        
        plt.plot(self.xvals, self.constraintvals)
        plt.plot(self.xvals, self.xlimit)
        plt.plot(self.ylimit, self.yvals)
        
        plt.plot(self.xsearch, self.ysearch, 'o')
        
        plt.show()

def computeContours(modeldata, metric, opts):
    
    data = ModelPlotData(opts)
    
    data.xvals = range(1,2*opts.period,opts.stepsize)
    data.yvals = range(1,2*opts.period,opts.stepsize)
    data.zvals = []
    
    for x in data.xvals:
        curline = []
        for y in data.yvals:
            curline.append(computeFunctionVal(metric, modeldata, x, y))
        data.zvals.append(curline)
    
    data.constraintvals = []
    for x in data.xvals:
        data.constraintvals.append(2*opts.period - x)
    
    data.xlimit = []
    for y in data.yvals:
        data.xlimit.append(modeldata.data["alone-cycles"][1])

    data.ylimit = []
    for x in data.xvals:
        data.ylimit.append(modeldata.data["alone-cycles"][0])
    
    return data

def main():
    opts,args = parseArgs()
    metric = args[0]
    modeldata = IniFile(args[1])
    searchtrace = TracefileData(args[2])
    searchtrace.readTracefile()
    
    print "Computing contours..."
    cdata = computeContours(modeldata, metric, opts)
    
    print "Retrieving search points..."
    cdata.setSearchPoints(searchtrace)
    
    print "Plotting..."
    cdata.plot()

if __name__ == '__main__':
    main()