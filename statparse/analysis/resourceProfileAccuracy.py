#!/usr/bin/env python

from optparse import OptionParser
from statparse.util import fatal
from statparse.statfileParser import StatfileIndex
from statparse import experimentConfiguration, metrics
from statparse.statResults import StatResults
from statparse.printResults import numberToString, printData

import pickle
import os
import sys

def parseArgs():
    parser = OptionParser(usage="resourceProfileAccuracy.py [options] metric-name")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--partition-file", action="store", dest="partitionFile", type="string", default="optimalPartitions.pkl", help="File to read partitions from")
    parser.add_option("--np", action="store", dest="np", type="int", default=4, help="Number of cores")

    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Usage: "+parser.usage
        fatal("Command line error")
    
    return opts,args

def computeAccuracy(partitions, index, opts, metric):
    useParts = partitions[metric]
    metricObj = metrics.createMetric(metric)
    
    useParams = {'OPTIMAL-PARTITION-METRIC': metric}
    
    searchConf = experimentConfiguration.buildMatchAllConfig()
    searchConf.parameters = useParams
        
    results = StatResults(index,
                          searchConf,
                          False,
                          opts.quiet)
    
    results.plainSearch("COM:IPC")
    results.aggregateSimpoints = False
    results.wlMetric = metricObj
    
    wls = useParts.keys()
    wls.sort()
    
    header = ["Workload", "Actual", "Prediction", "Error (%)"]
    lines = []
    lines.append(header)
    
    for wl in wls:
        expMetval = results._aggregateWorkloadResults(opts.np, useParams, wl)[0]
        offlineMetval = useParts[wl].metricValue[0]
        
        percerror = ((offlineMetval - expMetval) / expMetval) * 100
        
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