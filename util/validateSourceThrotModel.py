#!/usr/bin/python

import sys
import os
import shutil

from optparse import OptionParser
from visualizeMSHROccupancy import MSHROccupancy
from statparse.analysis import computePercError
from m5test.M5Command import M5Command
from workloadfiles.workloads import getAllBenchmarks

MAX_MSHRS = 16

def parseArgs():
    parser = OptionParser(usage="validateSourceThrotModel.py [options] ticks [benchmark]")

    parser.add_option("--plot", action="store_true", dest="plot", default=False, help="Print the results as a heat map")
    parser.add_option("--reduced-mshrs", action="store", dest="redmshrs", default=16, type="int", help="The number of MSHRs used to generate the reduce file")
    parser.add_option("--min-request-interval", action="store", dest="interval", default=0, type="int", help="The minimum request interval used to generate the reduce file")
    parser.add_option("--width", action="store", dest="width", default=18, type="int", help="The width of each column in print")
    opts, args = parser.parse_args()
    
    if len(args) < 1 and len(args) > 2:
        print "Command line error..."
        print "Usage : "+parser.usage
        sys.exit(-1)
    
    return opts, args

def findApplicableMSHR(mshrlist, at):
    mintick = 100000000000
    minindex = -1
    
    for i in range(len(mshrlist)):
        if mshrlist[i] <= at:
            return i
        
        if mshrlist[i] < mintick:
            mintick = mshrlist[i]
            minindex = i
    
    assert minindex != -1
    return minindex

def estimateReduction(maxdata, opts):
    
    estimate = MSHROccupancy("", opts.redmshrs)
    
    occupiedTo = [0 for i in range(opts.redmshrs)]
    lastRequestExecAt = 0
    
    while not maxdata.isEmpty():
        allocAt, duration = maxdata.getOldestEntry()
        mshrID = findApplicableMSHR(occupiedTo, allocAt)
        
        if opts.interval > 0 and allocAt < (lastRequestExecAt + opts.interval):
            allocAt = lastRequestExecAt + opts.interval
        lastRequestExecAt = allocAt
        
        if occupiedTo[mshrID] < allocAt:
            occupiedTo[mshrID] = allocAt + duration
        else:
            occupiedTo[mshrID] = occupiedTo[mshrID] + duration 
        
        estimate.addEntry(mshrID, occupiedTo[mshrID]-duration, duration)
        
        if occupiedTo[mshrID] >= maxdata.oldestCycle:
            return estimate
        
    return estimate

def runM5(dir, benchmark, ticks, basemshrs, requestInterval):
    if os.path.exists(dir):
        shutil.rmtree(dir)
    os.mkdir(dir)
    
    os.chdir(dir)
    cmd = M5Command()
    cmd.setUpTest(benchmark, 1, "RingBased", 1)
    cmd.setArgument("USE-CHECKPOINT", "/home/jahre/newchk")
    cmd.setArgument("MEMORY-BUS-SCHEDULER", "RDFCFS")
    cmd.setArgument("BASEMSHRS", basemshrs)
    cmd.setArgument("MIN-REQUEST-INTERVAL", requestInterval)
    cmd.setArgument("SIMULATETICKS", ticks)
    cmd.setArgument("DO-MSHR-TRACE", True)
    
    cmd.run(0, "", False, False)
    
    os.chdir("..")

def generateTraces(benchmark, ticks, opts):
    
    defaultdirname = "red-exp-default"
    reducedirname = "red-exp-reduced"  
    
    runM5(defaultdirname, benchmark, ticks, MAX_MSHRS, 0)
    runM5(reducedirname, benchmark, ticks, opts.redmshrs, opts.interval)
    
    return defaultdirname+"/PrivateL2Cache0MSHRAllocatedTrace.txt", reducedirname+"/PrivateL2Cache0MSHRAllocatedTrace.txt" 

def processBenchmark(benchmark, ticks, opts):
    maxfile, redfile = generateTraces(benchmark, ticks, opts)
    
    if os.path.exists(maxfile):
        maxdata = MSHROccupancy(maxfile, MAX_MSHRS)
        reddata = MSHROccupancy(redfile, opts.redmshrs)
        
        estimate = estimateReduction(maxdata, opts)
    
        return maxdata, reddata, estimate
    return None,None,None

def main():
    opts, args = parseArgs()
    
    if len(args) == 1:
        for t in ["Benchmark","Max requests", "Reduced requests", "Estimate", "Error"]:
            print t.ljust(opts.width),
        print 
        for n in getAllBenchmarks():
            maxdata, reddata, estimate = processBenchmark(n, args[0], opts)
            if maxdata != None:
                error = "N/A"
                if reddata.requests != 0:
                    error = str(computePercError(estimate.requests, reddata.requests))+" %"
                
                print str(n).ljust(opts.width),
                print str(maxdata.requests).ljust(opts.width),
                print str(reddata.requests).ljust(opts.width),
                print str(estimate.requests).ljust(opts.width),
                print str(error).ljust(opts.width)
            else:
                print str(n).ljust(opts.width)+"Error..."
            sys.stdout.flush()
    else:
        maxdata, reddata, estimate = processBenchmark(args[1], args[0], opts)
        
        print "Full requests:              "+str(maxdata.requests)
        print "Measured reduced requests:  "+str(reddata.requests)
        print "Estimated reduced requests: "+str(estimate.requests)
        if reddata.requests != 0:
            print "Error:                      "+str(computePercError(estimate.requests, reddata.requests))+" %"
    
        if opts.plot:
            estimate.plot(args[0]+" Estimate", "")

if __name__ == '__main__':
    main()