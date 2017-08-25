#!/usr/bin/env python

import sys
from optparse import OptionParser
from sag import fatal

def parseArgs():
    parser = OptionParser(usage="evaluateApplication.py [options] period parallel-fraction model-file")

    parser.add_option("--max-cores", action="store", dest="maxCores", default=8, help="Maximum number of cores (Default: 8)")
    parser.add_option("--voltage-points", action="store", dest="voltagePoints", default=10, help="Number of voltage points to consider (Default: 10)")
    
    
    opts, args = parser.parse_args()

    if len(args) != 3:
        print
        print "Commandline error:"
        print parser.usage
        print 
        sys.exit(0)
        
    return args, opts

def readModelFile(modelfilename):
    model = {}
    f = open(modelfilename)
    for l in f:
        try:
            data = l.split("=")
            key = data[0].strip()
            value = float(data[1])
        except:
            fatal("Cannot parse model config line:\n"+str(l))
        
        assert key not in model
        model[key] = value
        
    return model

def main():
    args, opts = parseArgs()
    model = readModelFile(args[2])
    
    vStep = (model["VMAX"] - model["VMIN"]) / float(opts.voltagePoints)
    vRange = [model["VMIN"]+vStep*i for i in range(opts.voltagePoints+1)]
    
    print vRange

if __name__ == '__main__':
    main()