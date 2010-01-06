#!/usr/bin/env python

from optparse import OptionParser
from statparse.util import fatal, getNpExperimentDirs, computeTraceError
from statparse.tracefile.errorStatistics import checkStatName, getStatnameMessage, printParamErrorStatDict, plotBoxFromDict, printErrorStatDict

commands = ["total", "bus-queue", "bus-service"]

def parseArgs():
    parser = OptionParser(usage="privateLatencyAccuracy.py [options] np command statistic")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--verbose", action="store_true", dest="verbose", default=False, help="Print extra progress output")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--print-all", action="store_true", dest="printAll", default=False, help="Print results for each workload")
    parser.add_option("--relative", action="store_true", dest="relativeErrors", default=False, help="Print relative errors (Default: absolute)")
    parser.add_option("--plot-box", action="store_true", dest="plotBox", default=False, help="Visualize data with box and whiskers plot")
    parser.add_option("--hide-outliers", action="store_true", dest="hideOutliers", default=False, help="Removes outliers from box and whiskers plot")   
    
    opts, args = parser.parse_args()
    
    if len(args) != 3:
        fatal("command line error\nUsage: "+parser.usage)
    
    if args[1] not in commands:
        fatal("Unknown command "+args[1]+", candidates are "+str(commands))
    
    if not checkStatName(args[2]):
        fatal("Unknown statistic name. "+getStatnameMessage()) 
    
    return opts,args

def getTracename(directory, aloneCPUID, sharedMode):
    prefix = "CPU"
    if sharedMode:
        postfix = "InterferenceTrace.txt"
    else:
        postfix = "LatencyTrace.txt"
    
    return directory+"/"+prefix+str(aloneCPUID)+postfix



def main():

    opts,args = parseArgs()
    try:
        np = int(args[0])
    except:
        fatal("Number of CPUs must be an integer")
    
    command = args[1]
    statistic = args[2]
    
    if not opts.quiet:
        print
        print "Number of Requests Synchronized Alone Latency Accuracy"
        print
    
    dirs, sortedparams = getNpExperimentDirs(np)
    
    if opts.relativeErrors:
        
        if command == "total":
            colname = "Total"
        elif command == "bus-service":
            colname = "bus_service"
        elif command == "bus-queue":
            colname = "bus_queue"
        else:
            assert False, "unknown command"
        
        
        def getBaselineName(directory, aloneCPUID):
            return directory+"/CPU"+str(aloneCPUID)+"LatencyTrace.txt", colname 
        
        baselineFunc = getBaselineName
    else:
        baselineFunc = None
    
    if command == "total":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Total", "Total", False, True, baselineFunc)
    elif command == "bus-service":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "bus_service", "bus_service", False, True, baselineFunc)
    elif command == "bus-queue":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "bus_queue", "bus_queue", False, True, baselineFunc)
    else:
        assert False, "unknown command"
        
    if opts.printAll:
        printParamErrorStatDict(results, sortedparams, statistic, opts.relativeErrors, opts.decimals)
    else:
        printErrorStatDict(aggRes, opts.relativeErrors, opts.decimals, sortedparams)
        
    if opts.plotBox:
        plotBoxFromDict(results, opts.hideOutliers, "Latency")

if __name__ == '__main__':
    main()