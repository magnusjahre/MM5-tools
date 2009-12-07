#!/usr/bin/env python
from statparse.tracefile.errorStatistics import ErrorStatistics
import statparse.tracefile.errorStatistics as errorStats

from statparse.tracefile.tracefileData import TracefileData
import statparse.tracefile.tracefileData as tracefile
import deterministic_fw_wls as workloads

from optparse import OptionParser

from statparse.util import fatal
from statparse.util import warn
from statparse.util import getExperimentDirs

commands = ["IPC", "MWS", "latency"]


def parseArgs():
    parser = OptionParser(usage="computeAloneIPCError.py [options] np command")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--verbose", action="store_true", dest="verbose", default=False, help="Print extra progress output")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--include-params", action="store", dest="includeParams", type="string", default="", help="A standard parameter string that indicates the parameters to include")
    parser.add_option("--print-all", action="store_true", dest="printAll", default=False, help="Print results for each workload")
    parser.add_option("--relative", action="store_true", dest="relativeErrors", default=False, help="Print relative errors (Default: absolute)")
    
    opts, args = parser.parse_args()
    
    if len(args) != 2:
        fatal("command line error\nUsage: "+parser.usage)
    
    if args[1] not in commands:
        fatal("Unknown command "+args[1]+", candidates are "+str(commands))
    
    return opts,args

def getTracename(dir, cpuID):
    prefix = "missBandwidthPolicyCommittedInsts"
    postfix = ".txt"
    
    return dir+"/"+prefix+str(cpuID)+postfix

def getResultKey(wl, aloneCPUID, bmNames):
    return wl+"-"+str(aloneCPUID)+"-"+bmNames[aloneCPUID]

def computeIPCEstimateErrors(dirs, np, opts, command):
    
    results = {}
    
    aggregateErrors = ErrorStatistics(opts.relativeErrors)
    for wl, shDirID, aloneDirIDs in dirs:
        
        if opts.verbose:
            print "Processing workload "+wl
            
        bmNames = workloads.getBms(wl, np, False)
        
        for aloneCPUID in range(len(aloneDirIDs)):
            
            sharedTrace = TracefileData(getTracename(shDirID, aloneCPUID))
        
            try:
                sharedTrace.readTracefile()
            except IOError:
                if not opts.quiet:
                    warn("File "+getTracename(shDirID)+" cannot be opened, skipping...")
                continue
            
            aloneTrace = TracefileData(getTracename(aloneDirIDs[aloneCPUID], 0))
            aloneTrace.readTracefile()
            
            if command == "IPC":
                curStats = tracefile.computeErrors(aloneTrace, "Measured Alone IPC", sharedTrace, "Estimated Alone IPC", opts.relativeErrors)
            elif command == "MWS":
                curStats = tracefile.computeErrors(aloneTrace, "Misses while Stalled", sharedTrace, "Misses while Stalled", opts.relativeErrors)
            elif command == "latency":
                curStats = tracefile.computeErrors(aloneTrace, "Alone Memory Latency", sharedTrace, "Estimated Private Latency", opts.relativeErrors)
            else:
                assert False, "unknown command"
            
            aggregateErrors.aggregate(curStats)
            
            if getResultKey(wl, aloneCPUID, bmNames) in results:
                fatal("This script only handles one variable parameter")
            
            results[getResultKey(wl, aloneCPUID, bmNames)] = curStats
            
        
    return results, aggregateErrors 

def main():

    opts,args = parseArgs()
    try:
        np = int(args[0])
    except:
        fatal("Number of CPUs must be an integer")
    
    
    command = args[1]
    
    if not opts.quiet:
        print
        print "Alone IPC Prediction Accuracy Estimation"
        print
    
    dirs = getExperimentDirs(np, opts.includeParams)
    results, aggRes = computeIPCEstimateErrors(dirs, np, opts, command)
        
    if opts.printAll:
        errorStats.printErrorStatDict(results, opts.relativeErrors, opts.decimals)
    else:
        print "Aggregate Results:"
        print aggRes

if __name__ == '__main__':
    main()