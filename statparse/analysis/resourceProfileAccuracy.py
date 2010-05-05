#!/usr/bin/env python

from optparse import OptionParser
from statparse.util import fatal
from statparse.statfileParser import StatfileIndex
from statparse import experimentConfiguration, metrics
from statparse.statResults import StatResults
from statparse.printResults import numberToString, printData
from statparse.processResults import filterResultsWithConfig
import deterministic_fw_wls

import pickle
import os
import sys
import optcomplete

def parseArgs():
    parser = OptionParser(usage="resourceProfileAccuracy.py [options] metric-name")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--partition-file", action="store", dest="partitionFile", type="string", default="optimalPartitions.pkl", help="File to read partitions from")
    parser.add_option("--np", action="store", dest="np", type="int", default=4, help="Number of cores")
    parser.add_option("--workload", action="store", dest="workload", type="string", default="", help="Print extended information about this workload")

    optcomplete.autocomplete(parser, optcomplete.ListCompleter(metrics.mpMetricNames))
    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Usage: "+parser.usage
        fatal("Command line error")
    
    return opts,args

def computeAccuracy(partitions, index, opts, metric):
    useParts = partitions[metric]
    useParams = {'OPTIMAL-PARTITION-METRIC': metric}
    
    metricObj = metrics.createMetric(metric)
    searchConf = experimentConfiguration.buildMatchAllConfig()
    searchConf.parameters = useParams
    
    if opts.workload != "":
        printSingleWorkload(opts.workload, useParts, opts, useParams, metricObj, searchConf, index)
    else:
        printAllWorkloads(useParts, useParts, opts, useParams, metricObj, searchConf, index)

def computePercError(prediction, actual):
    return ((prediction - actual) / actual) * 100

def printSingleWorkload(wl, useParts, opts, useParams, metricObj, searchConf, index):
    
    results = StatResults(index,
                          searchConf,
                          False,
                          opts.quiet)
    
    
    results.aggregateSimpoints = False
    results.wlMetric = metricObj
    results.plainSearch("COM:IPC")
    
    expMetval = results._aggregateWorkloadResults(opts.np, useParams, wl)[0]
    offlineMetval = useParts[wl].metricValue
    
    print
    print "Extended results for workload "+wl
    print 
    print "Actual performance:     "+numberToString(expMetval, opts.decimals)
    print "Predicted performance:  "+numberToString(offlineMetval, opts.decimals)
    print "Error:                  "+numberToString(computePercError(offlineMetval, expMetval), opts.decimals)+" %"
    print
    
    benchmarks = deterministic_fw_wls.getBms(wl, opts.np, True)
    
    searchConf.workload = wl
    measuredBmRes = {}
    for bm in benchmarks:
        searchConf.benchmark = bm
        tmpres = filterResultsWithConfig(results.noPatResults, searchConf)
        assert len(tmpres.keys()) == 1
        measuredBmRes[bm] = tmpres[tmpres.keys()[0]]
    
    if -1 not in useParts[wl].predictedIPCs:
        fatal("Simpoints are not supported")
    
    predictedBMRes = useParts[wl].predictedIPCs[-1]
    
    header = ["Benchmark", "Actual", "Predicted", "Error %"]
    lines = []
    lines.append(header)
    
    for b in benchmarks:
        error = computePercError(predictedBMRes[b], measuredBmRes[b])
        line = [b,
                numberToString(measuredBmRes[b], opts.decimals),
                numberToString(predictedBMRes[b], opts.decimals),
                numberToString(error, opts.decimals)]
        lines.append(line)
        
    printData(lines, [True, False, False, False], sys.stdout, opts.decimals)
    

def printAllWorkloads(results, useParts, opts, useParams, metricObj, searchConf, index):
    
    results = StatResults(index,
                          searchConf,
                          False,
                          opts.quiet)
    
    
    results.aggregateSimpoints = False
    results.wlMetric = metricObj
    results.plainSearch("COM:IPC")
    
    wls = useParts.keys()
    wls.sort()
    
    header = ["Workload", "Actual", "Prediction", "Error (%)"]
    lines = []
    lines.append(header)
    
    for wl in wls:
        expMetval = results._aggregateWorkloadResults(opts.np, useParams, wl)[0]
        offlineMetval = useParts[wl].metricValue
        
        percerror = computePercError(offlineMetval, expMetval)
        
        line = [wl,
                numberToString(expMetval, opts.decimals),
                numberToString(offlineMetval, opts.decimals),
                numberToString(percerror, opts.decimals)]
        
        lines.append(line)
        
    printData(lines, [True, False, False, False], sys.stdout, opts.decimals)

def main():

    opts,args = parseArgs()
    
    if not os.path.exists("index-all.pkl"):
        print
        fatal("Index file does not exist")
        
    if not os.path.exists("pbsconfig.py"):
        print
        fatal("pbsconfig.py not found")
        
    pbsconfigmodule = __import__("pbsconfig")
    pbsconfigobj = pbsconfigmodule.config
    
    if not os.path.exists(opts.partitionFile):
        fatal("Cannot find partition file "+opts.partitionFile)
    
    partitions = pickle.load(open(opts.partitionFile))
    
    if not opts.quiet:
        print
        print "Cache Capacity and Memory Bandwidth Resource Profile Validation"
        print
        print "Loading index... ",
        sys.stdout.flush()
    index = StatfileIndex("index-all")
    if not opts.quiet:
        print "done!"

    computeAccuracy(partitions, index, opts, args[0])

if __name__ == '__main__':
    main()