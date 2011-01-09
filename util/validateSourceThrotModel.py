#!/usr/bin/python

import sys
import os

from optparse import OptionParser
from statparse.util import fatal
from visualizeMSHROccupancy import MSHROccupancy
from statparse.analysis import computePercError
from m5test.M5Command import M5Command
import shutil

MAX_MSHRS = 16

def parseArgs():
    parser = OptionParser(usage="validateSourceThrotModel.py [options] benchmark ticks")

    parser.add_option("--plot", action="store_true", dest="plot", default=False, help="Print the results as a heat map")
    parser.add_option("--reduced-mshrs", action="store", dest="redmshrs", default=16, type="int", help="The number of MSHRs used to generate the reduce file")
    parser.add_option("--min-request-interval", action="store", dest="interval", default=0, type="int", help="The minimum request interval used to generate the reduce file")

    opts, args = parser.parse_args()
    
    if len(args) != 2:
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
    occupiedTo = [0 for i in range(opts.redmshrs)]
    
    requestsExecuted = 0
    
    lastRequestExecAt = 0
    while not maxdata.isEmpty():
        allocAt, duration = maxdata.getOldestEntry()
        mshrID = findApplicableMSHR(occupiedTo, allocAt)
        
        if allocAt < (lastRequestExecAt + opts.interval):
            allocAt = lastRequestExecAt + opts.interval
        lastRequestExecAt = allocAt
        
        if occupiedTo[mshrID] < allocAt:
            occupiedTo[mshrID] = allocAt + duration
        else:
            occupiedTo[mshrID] = occupiedTo[mshrID] + duration 
        
        requestsExecuted += 1
        if occupiedTo[mshrID] >= maxdata.oldestCycle:
            return requestsExecuted
        
    fatal("More requests in reduced files, this must be wrong!")

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
    
    cmd.run(0, "", False)
    
    os.chdir("..")

def generateTraces(benchmark, ticks, opts):
    
    defaultdirname = "red-exp-default"
    reducedirname = "red-exp-reduced"  
    
    runM5(defaultdirname, benchmark, ticks, MAX_MSHRS, 0)
    runM5(reducedirname, benchmark, ticks, opts.redmshrs, opts.interval)
    
    return defaultdirname+"/PrivateL2Cache0MSHRAllocatedTrace.txt", reducedirname+"/PrivateL2Cache0MSHRAllocatedTrace.txt" 

def main():
    opts, args = parseArgs()
    
    maxfile, redfile = generateTraces(args[0], args[1], opts)
    
    maxdata = MSHROccupancy(maxfile, MAX_MSHRS)
    reddata = MSHROccupancy(redfile, opts.redmshrs)
    
    requestEstimate = estimateReduction(maxdata, opts)
    
    print "Full requests:              "+str(maxdata.requests)
    print "Measured reduced requests:  "+str(reddata.requests)
    print "Estimated reduced requests: "+str(requestEstimate)
    print "Error:                      "+str(computePercError(requestEstimate, reddata.requests))+" %"

if __name__ == '__main__':
    main()