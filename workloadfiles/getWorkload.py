#!/usr/bin/python

from optparse import OptionParser
from workloadfiles.workloads import parseTypeString
from workloadfiles.workloads import Workloads
from workloadfiles.workloads import UnknownWorkloadException
from workloadfiles.workloads import getAllBenchmarks
from workloadfiles.workloads import typedWorkloadIdentifiers
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
    for type in typedWorkloadIdentifiers:
        if type != 'a':
            bms[type] = []
            wls = workloads.getWorkloadsByType(np, type)
            for wl in wls:
                for bm in workloads.getTypedBms(np, wl):        
                    if bm not in bms[type]:
                        bms[type].append(bm)                
    
    allBms = getAllBenchmarks()
    
    print "Number of benchmarks: "+str(len(allBms))
    print
     
    allcnt = 0
    for t in bms:
        print t+":",
        cnt = 0
        for b in bms[t]:
            print b+", ",
            cnt +=1
        allcnt += cnt
        print "("+str(cnt)+")"
    print "Total: "+str(allcnt)
    

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