#!/usr/bin/python

import sys
import os

from optparse import OptionParser
from statparse.util import fatal
from visualizeMSHROccupancy import MSHROccupancy
from statparse.analysis import computePercError

MAX_MSHRS = 16

def parseArgs():
    parser = OptionParser(usage="validateSourceThrotModel.py [options] max-file reduced-file")

    parser.add_option("--plot", action="store_true", dest="plot", default=False, help="Print the results as a heat map")
    parser.add_option("--reduced-mshrs", action="store", dest="redmshrs", default=4, type="int", help="The number of MSHRs used to generate the reduce file")
    parser.add_option("--min-request-interval", action="store", dest="interval", default=0, type="int", help="The minimum request interval used to generate the reduce file")

    opts, args = parser.parse_args()
    
    if len(args) != 2:
        print "Command line error..."
        print "Usage : "+parser.usage
        sys.exit(-1)
    
    if not os.path.exists(args[0]):
        fatal("File "+args[0]+" does not exist")
    
    if not os.path.exists(args[1]):
        fatal("File "+args[1]+" does not exist")
    
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
    
    while not maxdata.isEmpty():
        allocAt, duration = maxdata.getOldestEntry()
        mshrID = findApplicableMSHR(occupiedTo, allocAt)
        if occupiedTo[mshrID] < allocAt:
            occupiedTo[mshrID] = allocAt + duration
        else:
            occupiedTo[mshrID] = occupiedTo[mshrID] + duration 
            
        requestsExecuted += 1
        if occupiedTo[mshrID] > maxdata.oldestCycle:
            return requestsExecuted
        
    fatal("More requests in reduced files, this must be wrong!")

def main():
    opts, args = parseArgs()
    
    maxdata = MSHROccupancy(args[0], MAX_MSHRS)
    reddata = MSHROccupancy(args[1], opts.redmshrs)
    
    requestEstimate = estimateReduction(maxdata, opts)
    
    print "Full requests:              "+str(maxdata.requests)
    print "Measured reduced requests:  "+str(reddata.requests)
    print "Estimated reduced requests: "+str(requestEstimate)
    print "Error:                      "+str(computePercError(requestEstimate, reddata.requests))+" %"

if __name__ == '__main__':
    main()