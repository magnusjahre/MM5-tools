#!/usr/bin/python

import sys
import os
import re
from optparse import OptionParser
from util import fatal

def parseArgs():
    
    parser = OptionParser(usage="experimentStatus.py [options]")
    parser.add_option("--verbose", '-v', action="store_true", dest="verbose", default=False, help="Print all lines")
    parser.add_option("--only-shared-mode", '-s', action="store_true", dest="onlySharedMode", default=False, help="Only print shared mode status")
    parser.add_option("--rerun-list", '-r', action="store_true", dest="rerunList", default=False, help="Print command to resubmit non-complete jobs")
    opts, args = parser.parse_args()
    
    if len(args) != 0:
        print "Usage:"
        print parser.usage
        sys.exit()
    
    
    if not os.path.exists("pbsconfig.py"):
        fatal("Cannot find file pbsconfig.py in current directory")
    
    pbsconfig = __import__("pbsconfig")
    
    return opts, args, pbsconfig

def processExperiment(params, pbsconfig, expectedCores, privmode, verbose):
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
    
    if verbose or lines != cores:
        print wl.ljust(15)+expid.ljust(55)+str(lines)+" / "+str(cores)+(str((float(lines)*100)/float(cores))+"%").rjust(10)
    return expectedCores, lines, lines == cores

def processRerunList(failedlist, opts):
    rerunfiles = []
    pairs = []
    os.chdir("pbsfiles")
    for fn in os.listdir("."):
        if fn.startswith("runfile"):
            f = open(fn)
            content = f.read()
            for failedExp in failedlist:
                res = re.search("-ESTATSFILE="+failedExp+".txt", content)
                if res != None:
                    pairs.append((failedExp, fn))
                    if fn not in rerunfiles:
                        rerunfiles.append(fn)
    os.chdir("..")

    if opts.verbose:
        print
        print "Experiment to runfile mapping:"
        for exp, fn in pairs:
            print exp.ljust(40),fn.rjust(15)

    print
    print "Command to submit failed files:"
    print "sbatch "+" ".join(rerunfiles)

def main():
    opts, args, pbsconfig = parseArgs()

    expectedCores = 0
    completedCores = 0
    failedlist = []

    print "Shared mode experiment status:"
    for cmd, params in pbsconfig.commandlines:
        expectedCores, lines, success = processExperiment(params, pbsconfig, expectedCores, False, opts.verbose)
        completedCores += lines
        if not success:
            failedlist.append(pbsconfig.get_unique_id(params))

    if not opts.onlySharedMode:
        print
        print "Private mode experiment status:"
        for cmd, params in pbsconfig.privModeCommandlines:
            expectedCores, lines, success = processExperiment(params, pbsconfig, expectedCores, True, opts.verbose)
            completedCores += lines
            if not success:
                failedlist.append(pbsconfig.get_unique_id(params))
    
    print "Summary:", completedCores,"out of",expectedCores,"complete",
    print "("+("%.2f" % ((float(completedCores)*100)/float(expectedCores)))+"%)"

    if opts.rerunList:
        processRerunList(failedlist, opts)
    
if __name__ == '__main__':
    main()
