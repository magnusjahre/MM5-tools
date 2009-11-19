#!/usr/bin/env python

import sys
import os

from optparse import OptionParser
from statparse.tracefile.tracefileData import TracefileData

def parseArgs():
    parser = OptionParser(usage="analyzeTrace.py [options] filename")

    parser.add_option("-q", "--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("-x", "--x-column", action="store", dest="xCol", default="", type="string", help="The column IDs to use along the x-axis")
    parser.add_option("-y", "--y-columns", action="store", dest="yCols", default="", type="string", help="The column IDs to use along the y-axis")
    parser.add_option("-p", "--plot-filename", action="store", dest="plotFilename", default="", type="string", help="Write plot to file")
    
    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Command line error"
        print "Usage: "+parser.usage
        sys.exit(-1)
    
    return opts,args

def main():

    opts,args = parseArgs()
    
    if not os.path.exists(args[0]):
        print "Error: File "+str(args[0])+" not found"
        return -1
    
    if not opts.quiet:
        print
        print "Trace file analysis"
        print
    
    tracecontent = TracefileData(args[0])
    tracecontent.readTracefile()
    
    if opts.xCol == "" and opts.yCols == "":
        tracecontent.printColumnMapping()
    else:
        if opts.xCol == "" or opts.yCols == "":
            print "Error: --x-column and --y-columns options must be used together"
            return -1
        
        if not opts.quiet:
            print "Plotting results..."
        
        tracecontent.plot(opts.xCol, opts.yCols, opts.plotFilename)
        
if __name__ == '__main__':
    main()