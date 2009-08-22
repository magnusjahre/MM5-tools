#!/usr/bin/python

import sys
import os
from optparse import OptionParser

SIMFASTPATH = "/home/jahre/m5sim/simpoints/simplescalar/simplesim-3.0/sim-fast" 

def parseArgs():
    parser = OptionParser(usage="generateBBV.py BENCHMARK")
    parser.add_option("--interval-length", action="store", dest="intervalLength", type="int", default=100000000, help="The length of each simulation point in instructions (default: 100 million)")
    parser.add_option("--outdir", action="store", dest="outdir", default="outdir", help="Directory to place BBV (default: outdir)")
    opts, args = parser.parse_args()
    return parser, opts, args

def addArgument(arguments, arg, value):
    arguments.append("-"+arg+" "+str(value))
    return arguments

def main():

    parser,options,args = parseArgs()

    try:
        benchmark = args[0]
    except:
        print
        print "Error in argument parsing, got "+str(args)
        print "Usage: "+parser.usage
        print
        sys.exit(-1)

    
    intervalLength = options.intervalLength
    outdir = options.outdir
    outfile = "outfile.txt"

    try:
        os.mkdir(outdir)
    except:
        print "Output directory "+outdir+" exists, quitting"
        sys.exit(-1)

    print
    print "Generating BBV for benchmark "+benchmark
    print
    print "SimPoint size:    "+str(intervalLength)+" instructions"
    print "Output directory: "+outdir
    print "Output file:      "+outfile
    print

    arguments = addArgument([], "outdir", outdir)
    arguments = addArgument(arguments, "outfile", outfile)
    arguments = addArgument(arguments, "interval", intervalLength)

    command = SIMFASTPATH
    for a in arguments:
        command += " "+a

    command += " /home/jahre/benchmarks/spec2000/fma3d00.peak.ev6"

    print command


if __name__ == "__main__":
    sys.exit(main())


