#!/usr/bin/env python
import sys
import os

from optparse import OptionParser
from statparse.tracefile.tracefileData import TracefileData
import statparse.tracefile.tracefileData as tracefileModule
import traceback

def parseArgs():
    parser = OptionParser(usage="formatTrace.py [options] filename1 ")

    parser.add_option("-c", "--columns", action="store", dest="columns", default="", type="string", help="The column IDs to print (e.g 0, 1, 3-5)")
    parser.add_option("-n", "--names", action="store_true", dest="printNames", default=False, help="Print the names and numbers of each column")
    
    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Command line error"
        print "Usage: "+parser.usage
        sys.exit(-1)
    
    return opts,args

def main():

    opts,args = parseArgs()
    
    filename = args[0]
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
        try:
            tracefileModule.formattedPrint(tracecontent, opts.columns)
        except Exception as e:
            print "Printing failed!"
            print "Error: "+str(e) 
            traceback.print_exc()
        
if __name__ == '__main__':
    main()