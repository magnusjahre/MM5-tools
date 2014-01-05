#!/usr/bin/python

from optparse import OptionParser
from workloadfiles.workloads import parseTypeString
from workloadfiles.workloads import Workloads
from workloadfiles.workloads import UnknownWorkloadException
from workloadfiles.workloads import getAllBenchmarks
import optcomplete
import sys

def parseArgs():
    parser = OptionParser(usage="getWorkload.py [options] np [workload-name]")

    parser.add_option("--type", action="store", dest="type", default="all", help="Only print workloads of the specified type")
    parser.add_option("--bm-classification", action="store_true", dest="bmClassification", default=False, help="Print lists of benchmarks given their classification")
    
    optcomplete.autocomplete(parser)
    opts, args = parser.parse_args()
    
    if len(args) > 2 or len(args) < 1:
        print "Command line error."
        print "Usage: "+parser.usage
        sys.exit(-1)
    
    return opts, args

def printBenchmarkClassification(np, workloads):
    print "Benchmark classification:"
    print 
    
    bms = {}
    for type in ["a", "c", "b"]:
        bms[type] = []
        wls = workloads.getWorkloadsByType(np, type)
        for wl in wls:
            for bm in workloads.getTypedBms(np, wl):        
                if bm not in bms[type]:
                    bms[type].append(bm)                
    
    bms["n"] = []
    for noneWl in workloads.getWorkloadsByType(np, "n"):
        for noneBm in workloads.getTypedBms(np, noneWl):
            found = False
            for type in ["a", "c", "b", "n"]:
                if noneBm in bms[type]:
                    found = True
            if not found:
                bms["n"].append(noneBm)

    allBms = getAllBenchmarks()
    
    print "Number of benchmarks: "+str(len(allBms))
    print
    
    for type in bms:
        for bm in bms[type]:
            assert bm in allBms
            allBms.remove(bm)
            
    
    for t in bms:
        print t+":",
        for b in bms[t]:
            print b+", ",
        print
    
    print "Unknown: ",
    for b in allBms:
        print b+", ",
    print

def main():
    opts, args = parseArgs()
    
    np = int(args[0])
    workloads = Workloads()
    
    if opts.bmClassification:
        printBenchmarkClassification(np, workloads)
        return
    
    if len(args) == 2:
        try:
            workloads.printBms(args[1], np)
        except UnknownWorkloadException as e:
            print e.message
            sys.exit(-1)
    else:
        try:
            type = parseTypeString(opts.type)
        except Exception as e:
            print e.args[0]
            sys.exit(-1)
            
        workloads.printWorkloads(np, type)

if __name__ == '__main__':
    main()