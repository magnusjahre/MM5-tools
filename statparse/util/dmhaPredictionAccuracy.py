#!/usr/bin/env python

from optparse import OptionParser
from statparse.util import fatal, computeTraceError, getNpExperimentDirs
from statparse.tracefile.errorStatistics import plotBoxFromDict, printParamErrorStatDict, checkStatName, getStatnameMessage, printErrorStatDict

commands = ["requests", "latency", "ipc"]


def parseArgs():
    parser = OptionParser(usage="dmhaPredictionAccuracy.py [options] np command statistic")

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
    return directory+"/missBandwidthPolicyPredictionTrace.txt"

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
        print "DMHA Prediction Accuracy"
        print
    
    dirs, sortedparams = getNpExperimentDirs(np)        
        
    if command == "requests":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Measured Num Requests", "Estimated Num Requests", True, False)
    elif command == "latency":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Measured Avg Shared Latency", "Measured Avg Shared Latency", True, False)
    elif command == "ipc":
        results, aggRes = computeTraceError(dirs, np, getTracename, opts.relativeErrors, opts.quiet, "Measured IPC", "Estimated IPC", True, False)
    else:
        assert False, "unknown command"
        
    if opts.printAll:
        printParamErrorStatDict(results, sortedparams, statistic, opts.relativeErrors, opts.decimals)
    else:
        printErrorStatDict(aggRes, opts.relativeErrors, opts.decimals, sortedparams)

    if opts.plotBox:
        plotBoxFromDict(results, opts.hideOutliers, command)
        

if __name__ == '__main__':
    main()