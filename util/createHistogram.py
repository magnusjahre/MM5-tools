#!/usr/bin/env python

from optparse import OptionParser
from statparse.plotResults import plotHistogram

import sys

def parseArgs():
    parser = OptionParser(usage="createHistogram.py [options] DATAFILE")

    parser.add_option("--numbins", action="store", dest="numbins", default=10, type="int", help="The number of bins to divide the data into")
    parser.add_option("--plotfile", action="store", dest="plotfile", default="", type="string", help="Write the histogram plot to this file")
    parser.add_option("--title", action="store", dest="title", default="", type="string", help="Title of the plot")
    parser.add_option("--xlabel", action="store", dest="xlabel", default="Time (seconds)", type="string", help="X-axis label")
    parser.add_option("--use-col-id", action="store", dest="usecol", default=1, type="int", help="The column in the datafile to use")
    
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
    
    datavals = []
    file.readline() # skip header 
    
    for l in file:
        line = l.split()
        if opts.usecol > len(line)-1:
            print "ERROR: Line has "+str(len(line))+" columns, you asked for column "+str(opts.usecol)
            sys.exit()    
        
        try:
            datavals.append(float(line[opts.usecol]))
        except ValueError:
            print "ERROR: Data content \""+str(line[opts.usecol])+"\" cannot be converted to a float"
            sys.exit()   
    
    return datavals

def main():
    
    opts, datafilename = parseArgs()

    times = readFile(datafilename, opts)
    
    print "Maximum value is "+str(max(times))
    
    plotHistogram(times,
                  bins=opts.numbins,
                  filename=opts.plotfile,
                  xlabel=opts.xlabel,
                  title=opts.title)
    

if __name__ == '__main__':
    main()