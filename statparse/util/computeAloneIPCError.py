#!/usr/bin/env python

import sys

from statparse.tracefile.tracefileData import TracefileData
import statparse.tracefile.tracefileData as tracefile
import deterministic_fw_wls as workloads

from optparse import OptionParser

from statparse.util import fatal
from statparse.util import warn
from statparse.util import getExperimentDirs

from statparse.analysis import computeStddev
from statparse.analysis import computeMean
from statparse.analysis import computeRMS

from statparse.printResults import printData
from statparse.printResults import numberToString

TRACENAME="missBandwidthPolicyAloneIPCTrace.txt"

def parseArgs():
    parser = OptionParser(usage="computeAloneIPCError.py [options] np")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--verbose", action="store_true", dest="verbose", default=False, help="Print extra progress output")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--include-params", action="store", dest="includeParams", type="string", default="", help="A standard parameter string that indicates the parameters to include")
    parser.add_option("--print-all", action="store_true", dest="printAll", default=False, help="Print results for each workload")
    parser.add_option("--relative", action="store_true", dest="relativeErrors", default=False, help="Print relative errors (Default: absolute)")
    parser.add_option("--use-avg-lat-estimate", action="store_true", dest="useAvgLatEstimate", default=False, help="Use the average latency based estimates (Default: stall time difference measurements)")    

    opts, args = parser.parse_args()
    
    if len(args) != 1:
        fatal("command line error\nUsage: "+parser.usage)
    
    return opts,args

def getTracename(dir):
    return dir+"/"+TRACENAME

def computeIPCEstimateErrors(dirs, np, opts):
    
    sharedRequestStartID = 1
    
    if opts.useAvgLatEstimate:
        sharedAloneIPCStartID = 9
    else:
        sharedAloneIPCStartID = 5
    
    results = {}
    
    aggErrSum = 0
    aggErrSqSum = 0
    aggNumErrs = 0
    
    for wl, shDirID, aloneDirIDs in dirs:
        
        if opts.verbose:
            print
            print "Processing workload "+wl+" with shared trace "+getTracename(shDirID)
        
        sharedTrace = TracefileData(getTracename(shDirID))
        try:
            sharedTrace.readTracefile()
        except IOError:
            if not opts.quiet:
                warn("File "+getTracename(shDirID)+" cannot be opened, skipping...")
            continue
        
        bmNames = workloads.getBms(wl, np, False)
        
        for aloneCPUID in range(len(aloneDirIDs)):
            if opts.verbose:
                print "Processing shared trace with alone trace " + getTracename(aloneDirIDs[aloneCPUID])
            
            aloneTrace = TracefileData(getTracename(aloneDirIDs[aloneCPUID]))
            aloneTrace.readTracefile()
            errsum, errsqsum, numerrs = tracefile.computeInterpolatedErrors(aloneTrace, 
                                                                           1, 
                                                                           2,
                                                                           sharedTrace,
                                                                           sharedRequestStartID+aloneCPUID,
                                                                           sharedAloneIPCStartID+aloneCPUID,
                                                                           opts.relativeErrors,
                                                                           opts.quiet)
            if wl in results:
                fatal("IPC estimation only handles one set of workloads at the time")
            
            aggErrSum += errsum
            aggErrSqSum += errsqsum
            aggNumErrs += numerrs
            
            avgErr = computeMean(numerrs, errsum)
            rmsErr = computeRMS(numerrs, errsqsum)
            stddev = computeStddev(numerrs, errsum, errsqsum)
            
            results[wl+"-"+str(aloneCPUID)+"-"+bmNames[aloneCPUID]] = (avgErr, rmsErr, stddev)
    
    aggAvgErr = computeMean(aggNumErrs, aggErrSum)
    aggRmsErr = computeRMS(aggNumErrs, aggErrSqSum)
    aggStddev = computeStddev(aggNumErrs, aggErrSum, aggErrSqSum)
    
    return results, (aggAvgErr, aggRmsErr, aggStddev)
        

def printResults(results, opts):
    wlbms = results.keys()
    wlbms.sort()
    
    lines = []
    if opts.relativeErrors:
        lines.append(["", "Relative Average Error (%)", "Relative RMS Error (%)", "Relative Standard Deviation (%)"])
    else:
        lines.append(["", "Average Error", "RMS Error", "Standard Deviation"])
    justify = [True, False, False, False]
    
    for key in wlbms:
        avgErr, rmsErr, stddev= results[key]
        line = [key,
                numberToString(avgErr, opts.decimals),
                numberToString(rmsErr, opts.decimals),
                numberToString(stddev, opts.decimals)]
        lines.append(line)
        
    printData(lines, justify, sys.stdout, opts.decimals)

def main():

    opts,args = parseArgs()
    try:
        np = int(args[0])
    except:
        fatal("Number of CPUs must be an integer")
    
    if not opts.quiet:
        print
        print "Alone IPC Prediction Accuracy Estimation"
        print
    
    dirs = getExperimentDirs(np, opts.includeParams)
    results, aggRes = computeIPCEstimateErrors(dirs, np, opts)
    
    if opts.printAll:
        printResults(results, opts)
    else:
        aggavg, aggrms, aggstd = aggRes
        
        print
        if opts.relativeErrors:
            print "Aggregate Relative Errors (in %):"
        else:
            print "Aggregate Absolute Errors:"
        print ("Average error:            %."+str(opts.decimals)+"f") % aggavg
        print ("RMS error:                %."+str(opts.decimals)+"f") % aggrms
        print ("Error standard deviation: %."+str(opts.decimals)+"f") % aggstd
    
    

if __name__ == '__main__':
    main()