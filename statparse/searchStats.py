#!/usr/bin/env python
import sys
import os
import traceback

import metrics
import experimentConfiguration
from experimentConfiguration import ExperimentConfiguration

from optparse import OptionParser
from optparse import OptionGroup
from time import time

from statfileParser import StatfileIndex
from statResults import StatResults

def parseArgs():
    parser = OptionParser(usage="parseStats.py [options] (STATKEY | NUMERATOR-KEY DENOMINATOR-KEY)")
    
    searchOptions = OptionGroup(parser, "Search options")
    searchOptions.add_option("--np", action="store", dest="np", type="int", default=-1, help="Limit the file to configurations with n processors")
    searchOptions.add_option("--architecture", action="store", dest="architecture", type="string", default="*", help="Limit the file to configurations with this memory system architecture")
    searchOptions.add_option("--benchmark", action="store", dest="benchmark", type="string", default="*", help="Only present the results for this benchmark")
    searchOptions.add_option("--workload", action="store", dest="workload", type="string", default="*", help="Only present the results for this benchmark")
    searchOptions.add_option("--parameters", action="store", dest="parameters", type="string", default="", help="Only print configs matching key and value. Format: key1,val1:key2,val2:...")
    searchOptions.add_option("--search-file", action="store", dest="searchFile", type="string", default="", help="Search after key in this file")
    parser.add_option_group(searchOptions)
    
    aggregationOptions = OptionGroup(parser, "Result Aggregation Options")
    aggregationOptions.add_option("--workload-metric", action="store", dest="wlAggMetric", default="", help="Metric to use when aggregating workloads")
    aggregationOptions.add_option("--experiment-metric", action="store", dest="expAggMetric", default="", help="Metric to use when aggregating workloads")
    aggregationOptions.add_option("--aggregate-simpoints", action="store_true", dest="aggSimpoints", default=False, help="Aggregate simpoint results into one value representative for the whole execution")
    aggregationOptions.add_option("--aggregate-patterns", action="store_true", dest="aggPatterns", default=False, help="Aggregate values for multiple statistics into one result")
    aggregationOptions.add_option("--baseline-parameters", action="store", dest="baselineParams", type="string", default="", help="Use the specified configuration as the baseline. Format: key1,val1:key2,val2:...")
    parser.add_option_group(aggregationOptions)
    
    resultOptions = OptionGroup(parser, "Result Presentation Options")
    resultOptions.add_option("--outfile", action="store", dest="outfile", type="string", default="stdout", help="Write output to file (Default: stdout)")
    resultOptions.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to print for float results")
    resultOptions.add_option("--print-agg-distribution", action="store_true", dest="printAggDistribution", default=False, help="Use distribution mode when printing results")
    resultOptions.add_option("--print-distribution-file", action="store_true", dest="printDistFile", default=False, help="Create one python file with all matching distributions")
    resultOptions.add_option("--print-all-cores", action="store_true", dest="printAllCores", default=False, help="Print separate statistics for each core in table format")
    resultOptions.add_option("--print-speedups", action="store_true", dest="printSpeedups", default=False, help="Divide per core statistics by single program performance")
    resultOptions.add_option("--print-all-patterns", action="store_true", dest="printAllPatterns", default=False, help="Print all matching patterns")
    resultOptions.add_option("--plot", action="store_true", dest="plot", default=False, help="Show the result table as a bar chart")
    resultOptions.add_option("--normalize-to", action="store", dest="normalizeTo", type="int", default=-1, help="Print results relative to column n (where 1 is the leftmost column)")
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
    if opts.architecture != "*":
        params["MEMORY-SYSTEM"] = opts.architecture
        
    if opts.parameters != "":
        try:
            params, spec = experimentConfiguration.parseParameterString(opts.parameters, params)
        except Exception as e:
            print "Parameter parse error: "+str(e.args[0])
            if opts.showStackTrace:
                traceback.print_exc(file=sys.stdout)
            sys.exit(-1)
    
    searchConfig = ExperimentConfiguration(opts.np, params, opts.benchmark, opts.workload)
    
    baseparams = {}
    basespec = ()
    if opts.baselineParams != "":
        try:
            baseparams, basespec = experimentConfiguration.parseParameterString(opts.baselineParams)
        except Exception as e:
            print "Baseline parameter parse error: "+str(e.args[0])
            if opts.showStackTrace:
                traceback.print_exc(file=sys.stdout)
            sys.exit(-1)
    
    baseconfig = None
    if baseparams != {}:
        basenp, basebm, basewl = basespec
        baseconfig = ExperimentConfiguration(basenp, baseparams, basebm, basewl)
        
        if not opts.quiet:
            print "Parsed base config string and got spec "+str(basespec)+" and parameters "+str(baseparams)
            print "Resulting baseline configuration: "+str(baseconfig)
    
    outfile = sys.stdout
    if opts.outfile != "stdout":
        outfile = open(opts.outfile, "w")
    
    return opts, args, searchConfig, outfile, baseconfig


def getIndexmodule(basename):
    indexmodule = "index-"+basename
    indexmodulename = indexmodule+".pkl"
    return indexmodule, indexmodulename

def createFileIndex(opts, args):
    
    if opts.searchFile != "":
        if opts.np == -1 or opts.workload == "*":
            print "Options --np and --workload are required for single experiment parsing"
            sys.exit(-1) 
    
        pbsconfig = None
        indexmodule, indexmodulename = getIndexmodule(os.path.basename(opts.searchFile).split(".")[0])
    else:
        if not opts.quiet:
            print "No filename provided, assuming experiment parse"
        if not os.path.exists("pbsconfig.py"):
            print "File not found: pbsconfig.py"
            print "Use the --search-file option to search a specific file"
            sys.exit(-1)
        
        pbsconfig = __import__("pbsconfig")
        indexmodule, indexmodulename = getIndexmodule("all")
    
    if os.path.exists(indexmodulename):
        
        starttime = 0.0
        if not opts.quiet:
            print "Index exists, loading file "+indexmodulename
            starttime = time()
        index = StatfileIndex(indexmodule)
        if not opts.quiet:
            totTime = time() - starttime
            print "Index load took %.2f s" % totTime
    else:
        index = StatfileIndex()
        
        starttime = 0.0
        if not opts.quiet:
            print "Index does not exist, generating it..."
            starttime = time()
            
        if opts.searchFile != "":
            index.addFile(opts.searchFile, opts.orderFile, opts.np, opts.workload)
        else:
            assert pbsconfig != None
            totalLines = float(len(pbsconfig.commandlines))
            curConfigNum = 0
            for cmd, params in pbsconfig.commandlines:
                fileID = pbsconfig.get_unique_id(params)
                filepath = fileID+"/"+fileID+".txt"
                orderpath = fileID+"/statsDumpOrder.txt"
                
                np = pbsconfig.get_np(params)
                if np > 1:
                    wlOrBm = pbsconfig.get_workload(params)
                else:
                    wlOrBm = pbsconfig.get_benchmark(params)
                
                if os.path.exists(filepath):
                    if not opts.quiet:
                        percProgress = (float(curConfigNum) / totalLines) * 100
                        print ("Adding file "+filepath).ljust(70),
                        print ("%.2f" % percProgress)+" % complete"
                    
                    varparams = pbsconfig.get_variable_params(params)
                    try:
                        index.addFile(filepath, orderpath, np, wlOrBm, varparams)
                    except Exception as e:
                        print "Parsing failed for experment "+str(np)+", "+wlOrBm
                        print "Message: "+str(e)
                else:
                    if not opts.quiet:
                        print "WARNING: file "+filepath+" does not exist"
                curConfigNum += 1
        
        if not opts.quiet:
            totTime = time() - starttime
            print "Index generation took %.2f s" % totTime
            print "Storing index in file "+indexmodulename+" for future use"
        
        index.dumpIndex(indexmodule)
        
    return index

def writeSearchResults(statSearch, opts, outfile):
    
    if opts.wlAggMetric != "" or opts.expAggMetric != "" or opts.aggSimpoints or opts.printAllCores:
        
        wlMetric = None
        if opts.wlAggMetric != "":
            try:
                wlMetric = metrics.createMetric(opts.wlAggMetric)
            except Exception, e:
                print e
                metrics.printPossibleMetrics()
                sys.exit(-1)
        
        if opts.printAllCores:
            if wlMetric != None:
                print "ERROR: --print-table and --workload-agg-metric are mutually exclusive"
                return -1 
            wlMetric = metrics.NoAggregation(opts.printSpeedups)
        else:
            if opts.printSpeedups:
                print "WARNING: --print-speedups only makes sense with --print-all-cores"
        
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
            statSearch.printAggregateResults(opts.decimals, outfile, wlMetric, expMetric, opts.aggSimpoints)
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

def doSearch(index, searchConfig, args, options, baseconfig):
    statSearch = StatResults(index, searchConfig, options.aggPatterns, options.quiet, baseconfig, not options.printAllPatterns, options.plot, options.normalizeTo)
    if len(args) == 1:
        statSearch.plainSearch(args[0])
    else:
        statSearch.plainSearch(args[0], args[1])

    return statSearch

def main():
    
    opts, args, searchConfig, outfile, baseconfig = parseArgs()
    
    if not opts.quiet:
        print
        print "M5 Statistics Search"
        print
    
    
    index = createFileIndex(opts, args)
        
    if not opts.quiet:
        if len(args) == 1:
            print "Searching for pattern "+args[0]+"..."
        else:
            print "Searching for nominator pattern "+args[0]+" and denominator pattern "+args[1]
        print

    try:
        statSearch = doSearch(index, searchConfig, args, opts, baseconfig)
    except Exception as e:
        print str(e)
        return -1
    
    if not opts.quiet:
        print "Printing search results..."
        print
    
    writeSearchResults(statSearch, opts, outfile)

if __name__ == '__main__':
    main()
