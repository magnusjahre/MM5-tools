#!/usr/bin/python

import sys
import os

from optparse import OptionParser

from statparse.util import fatal, warn
from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
from statparse.plotResults import plotImage

import statparse.experimentConfiguration as expconfig
import statparse.processResults as procres
import statparse.printResults as printres

ERRVAL = "N/A"

def parseArgs():
    parser = OptionParser(usage="getProfile.py [options] statistic-pattern")

    parser.add_option("--plot", action="store_true", dest="plot", default=False, help="Print the results as a heat map")
    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Suppress output")
    parser.add_option("--benchmark", action="store", dest="benchmark", default="", help="Only print profile for given benchmark")
    parser.add_option("--decimals", action="store", dest="decimals", default=2, type="int", help="Number of decimals to print")

    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Command line error..."
        print "Usage : "+parser.usage
        sys.exit(-1)
    
    return opts,args[0]

def doSearch(pattern, benchmark, index, opts):
    searchConfig = expconfig.buildMatchAllConfig()
    searchConfig.benchmark = benchmark
    results = StatResults(index,
                          searchConfig,
                          False,
                          opts.quiet)
    
    results.plainSearch(pattern)
    return results

def getProfile(benchmark, opts, pattern, pbsconfigobj, index):
    
    results = doSearch(pattern, benchmark, index, opts)
    
    if results.matchingConfigs == []:
        fatal("No results found, check your pattern and benchmark name")
    
    keys = pbsconfigobj.variableSimulatorArguments.keys()
    if len(keys) != 2:
        fatal("This script handles exactly two variable arguments in the pbsconfig file")
    
    if not opts.quiet:
        print 
        print "Column key is "+keys[0]
        print "Row key is "+keys[1]
        print
    
    searchConfig = expconfig.buildMatchAllConfig()
    xargs = pbsconfigobj.variableSimulatorArguments[keys[0]]
    yargs = pbsconfigobj.variableSimulatorArguments[keys[1]]
    
    profile = [ [ERRVAL for j in range(len(xargs))] for i in range(len(yargs))]
    
    for x in range(len(xargs)):
        for y in range(len(yargs)):
            searchConfig.parameters[keys[0]] = xargs[x]
            searchConfig.parameters[keys[1]] = yargs[y]
            
            configRes = procres.filterConfigurations(results.matchingConfigs, searchConfig)
            
            if(len(configRes) > 1):
                fatal("Multiple results for benchmark "+str(benchmark)+", pattern must be refined")
            elif len(configRes) == 0:
                continue
            
            profile[x][y] = results.noPatResults[configRes[0]]
    
    return keys[0], xargs, keys[1], yargs, profile

def printTable(xargs, yargs, profile, opts, outfilename = ""):
    
    header = [""]
    for x in xargs:
        header.append(printres.numberToString(x, opts.decimals))
    
    textarray = []
    textarray.append(header)
    
    for x in range(len(xargs)):
        line = [printres.numberToString(yargs[x], opts.decimals)]
        for y in range(len(yargs)):
            line.append(printres.numberToString(profile[x][y], opts.decimals))
    
        textarray.append(line)
    
    just = [True]
    for i in range(len(xargs)):
        just.append(False)
        
    if outfilename != "":
        outfile = open(outfilename, "w")
    else:
        outfile = sys.stdout
        
    printres.printData(textarray, just, outfile, opts.decimals)

    if outfilename != "":
        outfile.close() 

def doPlot(benchmark, xname, xargs, yname, yargs, pattern, profile, filename = ""):
    
    yrangestr = "-0.5,"+str(len(xargs)-0.5)
    xrangestr = "-0.5,"+str(len(yargs)-0.5)
    zrangestr = "0,"+str(max(max(profile)))
    
    plotImage(profile,
              xlabel=xname,
              ylabel=yname,
              zlabel=pattern,
              title=benchmark,
              xticklabels=xargs,
              yticklabels=yargs,
              yrange=yrangestr,
              xrange=xrangestr,
              zrange=zrangestr,
              filename=filename)


def main():
    
    opts,pattern = parseArgs()
    
    if not os.path.exists("index-all.pkl"):
        print fatal("Index file does not exist")
        
    if not os.path.exists("pbsconfig.py"):
        print fatal("pbsconfig.py not found")

    pbsconfigmodule = __import__("pbsconfig")
    pbsconfigobj = pbsconfigmodule.config

    if not opts.quiet:
        print
        print "Retrieving profile..."
        print
        print "Loading index... ",
        sys.stdout.flush()
    index = StatfileIndex("index-all")
    if not opts.quiet:
        print "done!"

    if opts.benchmark != "":
        xname, xargs, yname, yargs, profile = getProfile(opts.benchmark, opts, pattern, pbsconfigobj, index)
        printTable(xargs, yargs, profile, opts)
        if opts.plot:
            doPlot(opts.benchmark, xname, xargs, yname, yargs, pattern, profile)
    else:
        fatal("multibenchmark not impl")

if __name__ == '__main__':
    main()