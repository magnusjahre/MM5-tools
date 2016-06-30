#!/usr/bin/python

import sys
import os
from optparse import OptionParser
from util import fatal

def parseArgs():
    
    parser = OptionParser(usage="experimentStatus.py [options]")
    #$parser.add_option("--threads", '-t', action="store", dest="threads", default=4, type="int", help="Number of worker threads")
    opts, args = parser.parse_args()
    
    if len(args) != 0:
        print "Usage:"
        print parser.usage
        sys.exit()
    
    
    if not os.path.exists("pbsconfig.py"):
        fatal("Cannot find file pbsconfig.py in current directory")
    
    pbsconfig = __import__("pbsconfig")
    
    return opts, args, pbsconfig

def processExperiment(params, pbsconfig, expectedCores, privmode):
    expid = pbsconfig.get_unique_id(params)
    if privmode:
        cores = 1
    else:
        cores = pbsconfig.get_np(params)
    expectedCores += cores
    if cores == 1 and not privmode:
        wl = pbsconfig.get_benchmark(params)
    else:
        wl = pbsconfig.get_workload(params)
        
    lines = 0
    try:
        dumpOrderFile = open(expid+"/statsDumpOrder.txt")
        lines = len(dumpOrderFile.readlines())
        dumpOrderFile.close()
    except:
        pass
    
    print wl.ljust(15)+expid.ljust(55)+str(lines)+" / "+str(cores)+(str((float(lines)*100)/float(cores))+"%").rjust(10)
    return expectedCores, lines

def main():
    commands, opts, pbsconfig = parseArgs()

    expectedCores = 0
    completedCores = 0
    
    print "Experiment status:"
    for cmd, params in pbsconfig.commandlines:
        expectedCores, lines = processExperiment(params, pbsconfig, expectedCores, False)
        completedCores += lines
        
    if os.path.exists("pbsfiles-priv-mode"):
        for cmd, params in pbsconfig.privModeCommandlines:
            expectedCores, lines = processExperiment(params, pbsconfig, expectedCores, True)
            completedCores += lines
    
    print "Summmary:", completedCores,"out of",expectedCores,"complete",
    print "("+("%.2f" % ((float(completedCores)*100)/float(expectedCores)))+"%)"
    
if __name__ == '__main__':
    main()