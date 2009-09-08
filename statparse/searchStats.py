#!/usr/bin/python

import sys
import os
import traceback

import metrics

from optparse import OptionParser
from optparse import OptionGroup
from time import time

from statfileParser import ExperimentConfiguration
from statfileParser import StatfileIndex
from statSearch import StatSearch

def parseArgs():
    parser = OptionParser(usage="parseStats.py [options] (STATKEY | NUMERATOR-KEY DENOMINATOR-KEY)")
    
    searchOptions = OptionGroup(parser, "Search options")
    searchOptions.add_option("--np", action="store", dest="np", type="int", default=-1, help="Limit the file to configurations with n processors")
    searchOptions.add_option("--architecture", action="store", dest="architecture", type="string", default="*", help="Limit the file to configurations with this memory system architecture")
    searchOptions.add_option("--benchmark", action="store", dest="benchmark", type="string", default="*", help="Only present the results for this benchmark")
    searchOptions.add_option("--workload", action="store", dest="workload", type="string", default="*", help="Only present the results for this benchmark")
    searchOptions.add_option("--other-limits", action="store", dest="otherLimits", type="string", default="", help="Only print configs matching key and value. Format: key1,val1:key2,val2:...")
    searchOptions.add_option("--search-file", action="store", dest="searchFile", type="string", default="", help="Search after key in this file")
    parser.add_option_group(searchOptions)
    
    aggregationOptions = OptionGroup(parser, "Result Aggregation Options")
    aggregationOptions.add_option("--workload-agg-metric", action="store", dest="wlAggMetric", default="", help="Metric to use when aggregating workloads")
    aggregationOptions.add_option("--experiment-agg-metric", action="store", dest="expAggMetric", default="", help="Metric to use when aggregating workloads")
    aggregationOptions.add_option("--agg-simpoints", action="store_true", dest="aggSimpoints", default=False, help="Aggregate simpoint results into one value representative for the whole execution")
    aggregationOptions.add_option("--relative-to-column", action="store", dest="relToColumn", type="int", default=-1, help="An integer pointing to the data column to use as the baseline (starts with 0, not counting text columns)")
    parser.add_option_group(aggregationOptions)
    
    resultOptions = OptionGroup(parser, "Result Presentation Options")
    resultOptions.add_option("--outfile", action="store", dest="outfile", type="string", default="stdout", help="Write output to file (Default: stdout)")
    resultOptions.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to print for float results")
    resultOptions.add_option("--print-agg-distribution", action="store_true", dest="printAggDistribution", default=False, help="Use distribution mode when printing results")
    resultOptions.add_option("--print-distribution-file", action="store_true", dest="printDistFile", default=False, help="Create one python file with all matching distributions")
    parser.add_option_group(resultOptions)
    
    otherOptions = OptionGroup(parser, "Other options")
    otherOptions.add_option("--orderfile", action="store", dest="orderFile", type="string", default="statsDumpOrder.txt", help="Dump order file to use in single file mode")
    otherOptions.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only print search results")
    otherOptions.add_option("--show-stacktrace", action="store_true", dest="showStackTrace", default=False, help="Show stacktrace on caught exceptions")
    parser.add_option_group(otherOptions)
    
    opts, args = parser.parse_args()
    
    if len(args) > 2 or len(args) < 1:
        print "Error: wrong number of arguments"
        print "Usage: "+parser.usage
        sys.exit(-1)
    
    params = {}
    if opts.architecture == "":
        params["MEMORY-SYSTEM"] = opts.architecture
        
    if opts.otherLimits != "":
        try:
            otherparams = opts.otherLimits.split(":")
            for pstr in otherparams:
                key,value = pstr.split(",")
                params[key] = value
        except:
            print "Could not parse parameter string "+opts.otherLimits
            sys.exit(-1)
    
    searchConfig = ExperimentConfiguration(opts.np, params, opts.benchmark, opts.workload)
    
    outfile = sys.stdout
    if opts.outfile != "stdout":
        outfile = open(opts.outfile, "w")
    
    return opts, args, searchConfig, outfile

def createSingleFileIndex(opts, args):
    indexmodule = "index-"+os.path.basename(opts.searchFile).split(".")[0]
    indexmodulename = indexmodule+".py"
    
    if os.path.exists(indexmodulename):
        
        starttime = 0.0
        if not opts.quiet:
            print "Index exists, loading for file "+indexmodulename
            starttime = time()
        index = StatfileIndex(indexmodule)
        if not opts.quiet:
            totTime = time() - starttime
            print "Index load took %.2f s" % totTime
    else:
        index = StatfileIndex()
        if opts.np == -1 or opts.workload == "*":
            print "Options --np and --workload are required for single experiment parsing"
            sys.exit(-1)
        
        starttime = 0.0
        if not opts.quiet:
            print "Index does not exist, generating it..."
            starttime = time()
        index.addFile(opts.searchFile, opts.orderFile, opts.np, opts.workload)
        
        if not opts.quiet:
            totTime = time() - starttime
            print "Index generation took %.2f s" % totTime
            print "Storing index in file "+indexmodulename+" for future use"
        
        index.dumpIndex(indexmodule)
        
    return index 

def createMultifileIndex(opts, args):
    
    if not opts.quiet:
        print "No filename provided, assuming experiment parse"
    if not os.path.exists("pbsconfig.py"):
        print "File not found: pbsconfig.py"
        print "Use the --search-file option to search a specific file"
        sys.exit(-1)
        
    pbsconfig = __import__("pbsconfig")
    print "Not implemented "+str(pbsconfig)

def writeSearchResults(statSearch, opts, outfile):
    if opts.wlAggMetric != "" or opts.expAggMetric != "" or opts.aggSimpoints:
        
        wlMetric = None
        if opts.wlAggMetric != "":
            try:
                wlMetric = metrics.createMetric(opts.wlAggMetric)
            except Exception, e:
                print e
                metrics.printPossibleMetrics()
                sys.exit(-1)
        
        expMetric = None    
        if opts.expAggMetric != "":
            try:
                expMetric = metrics.createMetric(opts.expAggMetric)
            except Exception, e:
                print e
                metrics.printPossibleMetrics()
                sys.exit(-1)  
        
        if not opts.quiet:
            print "Aggregating results with metric "
            
        try:
            statSearch.printAggregateResults(opts.decimals, outfile, wlMetric, expMetric, opts.aggSimpoints, opts.relToColumn)
        except Exception, e:
            print 
            print "Error:    Result aggregation failed"
            print "Message:  "+str(e)
            print
            if opts.showStackTrace:
                print "Stacktrace:"
                traceback.print_exc(file=sys.stdout)
                print
            sys.exit(-1)
        
    elif opts.printAggDistribution:
        statSearch.printAggregateDistribution(opts.decimals, outfile)
        
    elif opts.printDistFile:
        if not opts.quiet:
            if outfile == sys.stdout:
                print "Printing dictionary results to file distributions.py"
            else:
                print "Printing dictionary results to user specified file"
        
        statSearch.printDistributionsToFile(outfile)
    else:
        statSearch.printAllResults(opts.decimals, outfile)
    
    if outfile != sys.stdout:
        outfile.flush()
        outfile.close()

def doSearch(index, searchConfig, args):
    statSearch = StatSearch(index, searchConfig)
    if len(args) == 1:
        statSearch.plainSearch(args[0])
    else:
        statSearch.plainSearch(args[0], args[1])

    return statSearch

def main():
    
    opts, args, searchConfig, outfile = parseArgs()
    
    if not opts.quiet:
        print
        print "M5 Statistics Search"
        print
    
    index = None
    if opts.searchFile != "":
        index = createSingleFileIndex(opts, args)
    else:
        index = createMultifileIndex(opts, args)
        
    if not opts.quiet:
        if len(args) == 1:
            print "Searching for pattern "+args[0]+"..."
        else:
            print "Searching for nominator pattern "+args[0]+" and denominator pattern "+args[1]
        print
        
    statSearch = doSearch(index, searchConfig, args)
    
    if not opts.quiet:
        print "Printing search results..."
        print
    
    writeSearchResults(statSearch, opts, outfile)

if __name__ == '__main__':
    main()