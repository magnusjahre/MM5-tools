#!/usr/bin/env python

from optparse import OptionParser
from statparse.plotResults import plotHistogram

import sys

def parseArgs():
    parser = OptionParser(usage="createHistogram.py [options] DATAFILE")

    parser.add_option("--numbins", action="store", dest="numbins", default=10, type="int", help="The number of bins to divide the data into")
    parser.add_option("--plotfile", action="store", dest="plotfile", default="", type="string", help="Write the histogram plot to this file")
    parser.add_option("--title", action="store", dest="title", default="", type="string", help="Title of the plot")
    
    opts, args = parser.parse_args()

    if len(args) != 1:
        print "FATAL: The datafile must be supplied"
        print parser.usage
        sys.exit()
    
    return opts, args[0]

def readFile(filename, opts):
    
    try:
        file = open(filename)
    except:
        print "Cannot open file "+str(filename)
        sys.exit()
    
    times = []
    
    for l in file:
        i, time = l.split()
        times.append(float(time))
    
    return times

def main():
    
    opts, datafilename = parseArgs()

    times = readFile(datafilename, opts)
    
    plotHistogram(times,
                  bins=opts.numbins,
                  filename=opts.plotfile,
                  xlabel='Time (seconds)',
                  title=opts.title)
    

if __name__ == '__main__':
    main()