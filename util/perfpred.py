#!/usr/bin/env python

from optparse import OptionParser
from time import time

import sys
import subprocess

def parseArgs():
    parser = OptionParser(usage="buildSpec2006.py [options] COMMAND")

    parser.add_option("--iterations", action="store", dest="iterations", default=10, type="int", help="The number of interations to run the supplied commands")
    parser.add_option("--outfile", action="store", dest="outfile", default="timings.txt", type="string", help="The file the timings are written to (default: timings.txt)")
    
    opts, args = parser.parse_args()

    if len(args) != 1:
        print "FATAL: The command to run must be supplied"
        print parser.usage
        sys.exit()
    
    cmd = []
    for a in args[0].split():
        cmd.append(a)
    
    return opts, cmd

def timedExecute(cmd):
    start = time()
    subprocess.call(cmd)
    end = time()
    return end-start

def main():
    
    opts, cmd = parseArgs()
    timings = open(opts.outfile, "w")
    
    print
    print "Command execution timing helper"
    print 
    
    for i in range(opts.iterations):
        time = timedExecute(cmd)
        timings.write(str(i)+ " "+str(time)+"\n")
        print "Iteration "+str(i)+" done, time "+str(time)
        
    timings.close()
    
    print


if __name__ == '__main__':
    main()