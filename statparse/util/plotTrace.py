#!/usr/bin/env python
import sys
import os

from optparse import OptionParser
from statparse.tracefile.tracefileData import TracefileData
import statparse.tracefile.tracefileData as tracefileModule
import traceback

def parseArgs():
    parser = OptionParser(usage="analyzeTrace.py [options] filename1 [filename2 ...]")

    parser.add_option("-q", "--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("-x", "--x-column", action="store", dest="xCol", default="", type="string", help="The file and column IDs to use along the x-axis (e.g 0:0,1:1)")
    parser.add_option("-y", "--y-columns", action="store", dest="yCols", default="", type="string", help="The file and column IDs to use along the y-axis (e.g 0:0,1:1)")
    parser.add_option("-p", "--plot-filename", action="store", dest="plotFilename", default="", type="string", help="Write plot to file")
    parser.add_option("--xrange", action="store", dest="xRange", default="", type="string", help="The x values to include in the plot (Syntax: min,max)")
    parser.add_option("--yrange", action="store", dest="yRange", default="", type="string", help="The y values to include in the plot (Syntax: min,max)")
    parser.add_option("--xlabel", action="store", dest="xlabel", default="none", type="string", help="The x axis label")
    parser.add_option("--ylabel", action="store", dest="ylabel", default="none", type="string", help="The y axis label")
    parser.add_option("--type", action="store", dest="plotType", default="line", type="string", help="The plot type to use")
    parser.add_option("--title", action="store", dest="title", default="none", type="string", help="The chart title")
    
    opts, args = parser.parse_args()
    
    if len(args) < 1:
        print "Command line error"
        print "Usage: "+parser.usage
        sys.exit(-1)
    
    return opts,args

def main():

    opts,args = parseArgs()
    
    if not opts.quiet:
        print
        print "Running trace file analysis..."
    
    traces = []
    for filename in args:
        if not os.path.exists(filename):
            print "Error: File "+str(filename)+" not found"
            return -1
        
        tracecontent = TracefileData(filename)
        tracecontent.readTracefile()
        traces.append(tracecontent)
    
    if opts.xCol == "" and opts.yCols == "":
        fileID = 0
        for trace in traces:
            print
            print "Column mapping for file ID "+str(fileID)+": "+trace.filename
            trace.printColumnMapping()
            fileID += 1
    else:
        if opts.xCol == "" or opts.yCols == "":
            print "Error: --x-column and --y-columns options must be used together"
            return -1
        
        if not opts.quiet:
            print "Plotting results..."
        
        try:
            tracefileModule.plot(traces, opts.xCol, opts.yCols, filename=opts.plotFilename, xrange=opts.xRange, yrange=opts.yRange, plotType=opts.plotType, xlabel=opts.xlabel, ylabel=opts.ylabel, title=opts.title)
        except Exception as e:
            print "Plotting failed!"
            print "Error: "+str(e) 
            traceback.print_exc()
        
if __name__ == '__main__':
    main()