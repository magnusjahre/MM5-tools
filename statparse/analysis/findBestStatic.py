#!/usr/bin/env python

import sys
import os

from optparse import OptionParser
from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
import statparse.metrics as metrics
import statparse.experimentConfiguration as expconfig
import statparse.processResults as procres
import statparse.printResults as printres

useMetrics = ["hmos", "stp", "fairness", "sum"]

def getFilename(metricname):
    return "best-static-"+metricname+".txt"

def fatal(message):
    print "ERROR: "+message
    sys.exit(-1)
    

def parseArgs():
    parser = OptionParser(usage="findBestStatic.py [options]")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--np", action="store", dest="np", type="int", default=4, help="Number of processors (Default: 4)")

    opts, args = parser.parse_args()
    
    if len(args) != 0:
        print
        fatal("Commandline error\nUsage: "+parser.usage)
    
    return opts,args
    
def findBestMHA(results, opts, metric, outfile):
    
    if not opts.quiet:
        print "Searching for pattern COM:IPC... ",
        sys.stdout.flush()
    
    results.plainSearch("COM:IPC")
    
    if not opts.quiet:
        print "done!"
    
    results.wlMetric = metric
    results.expMetric = None
    results.aggregateSimpoints = False
    allWls = procres.findAllWorkloads(results.matchingConfigs)
    allParams = procres.findAllParams(results.matchingConfigs)

    resultprint = []
    resultprint.append(["Workload", "Best MHA", "Best Metric Value", "Conv. Metric Value", "Speedup %"])
    just = [True, False, False, False, False]

    for wl in allWls:
        
        maxmetval = 0
        bestparams = None
        convMetricValue = -1
        
        if not opts.quiet:
            print "Processing workload "+wl
        
        for params in allParams:
            
            if "STATICASYMMETRICMHA" not in params:
                continue
            
            if params["STATICASYMMETRICMHA"] == "16":
                continue
            
            metval = results._aggregateWorkloadResults(opts.np, params, wl)
            if len(metval) == 1 and metval[0] != "N/A":
                if metval[0] == maxmetval:
                    # prefer larger MHAs if equal metric value
                    bestMHA = bestparams.split(",")
                    thisMHA = params["STATICASYMMETRICMHA"].split(",")
                    assert len(bestMHA) == len(thisMHA)
                    bestMHASum = 0
                    thisMHASum = 0
                    for i in range(len(bestMHA)):
                        bestMHASum += int(bestMHA[i])
                        thisMHASum += int(thisMHA[i])
                    avgBestMHA = float(bestMHASum) / len(bestMHA)
                    avgThisMHA = float(thisMHASum) / len(thisMHA) 
                    
                    # keep best if avg miss para is equal
                    if avgThisMHA > avgBestMHA:
                        maxmetval = metval[0]
                        bestparams = params["STATICASYMMETRICMHA"]
                    
                elif metval[0] > maxmetval: 
                    maxmetval = metval[0]
                    bestparams = params["STATICASYMMETRICMHA"]
                    
                if params["STATICASYMMETRICMHA"] == "16,16,16,16":
                    convMetricValue = metval[0]
            else:
                if not opts.quiet:
                    print "Warning: skipping "+wl+", "+str(params)
            
        line = []
        line.append(wl+"sp0")
        line.append(bestparams)
        line.append(printres.numberToString(maxmetval, opts.decimals))
        line.append(printres.numberToString(convMetricValue, opts.decimals))
        
        try:
            speedup = ((maxmetval/convMetricValue) - 1)*100
        except:
            speedup = "N/A"
        line.append(printres.numberToString(speedup, opts.decimals))
        
        
        resultprint.append(line)
    
    printres.printData(resultprint, just, outfile, opts.decimals)
    
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
        
    if not opts.quiet:
        print
        print "Best Static Miss Handling Architecture"
        print
        print "Loading index... ",
        sys.stdout.flush()
    index = StatfileIndex("index-all")
    if not opts.quiet:
        print "done!"
    
    searchConfig = expconfig.buildMatchAllConfig()
    results = StatResults(index,
                          searchConfig,
                          False,
                          opts.quiet,
                          baselineParameters=pbsconfigobj.baselineParameters)
    
    
    for metricString in useMetrics:
        
        outfile = open(getFilename(metricString), "w")
        
        if not opts.quiet:
            print
            print "Printing results for metric "+metricString+" to file "+getFilename(metricString)
            print
        
        metric = metrics.createMetric(metricString)
        findBestMHA(results, opts, metric, outfile)
        
        outfile.flush()
        outfile.close()
    

if __name__ == '__main__':
    main()