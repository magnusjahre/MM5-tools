#!/usr/bin/env python

from optparse import OptionParser
from statparse.util import fatal
from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
from statparse.plotResults import plotRawScatter

import statparse.experimentConfiguration as expconfig
import statparse.processResults as procres
import statparse.printResults as printres

import os
import sys

def findPattern(patstring, ways, bandwidth, results):
    results.plainSearch(patstring)
    
    if results.noPatResults == {}:
        fatal("No results found for pattern "+patstring)

    searchConfig = expconfig.buildMatchAllConfig()    
    searchConfig.parameters["MAX-CACHE-WAYS"]  = ways
    searchConfig.parameters["MODEL-THROTLING-POLICY-STATIC"]  = bandwidth

    configRes = procres.filterConfigurations(results.matchingConfigs, searchConfig)
    assert len(configRes) == 1
    return results.noPatResults[configRes[0]]

def doSearch(benchmark, index):
    searchConfig = expconfig.buildMatchAllConfig()
    searchConfig.benchmark = benchmark
    results = StatResults(index,
                          searchConfig,
                          False,
                          opts.quiet)
    return results

class OverlapStats:

    def __init__(self, bm, index, ways, bws, plotStall):
        self.benchmark = bm        
        self.results = doSearch(bm, index)
        
        self.ways = ways
        self.bws = bws
        
        self.plotStall = plotStall
        
        self.stallCycles = self.readPatternMatrix("interferenceManager.cpu_stall_cycles")
        self.memReqCycles = self.readPatternMatrix("interferenceManager.total_latency")
        self.avgReqLatency = self.readPatternMatrix("interferenceManager.avg_total_latency")
        
        self.reqpara = {}
        
        for w in self.ways:
            self.reqpara[w] = {}
            for b in self.bws:
                self.reqpara[w][b] = self.memReqCycles[w][b] / self.stallCycles[w][b]
                
              
    def readPatternMatrix(self, pattern):
        data = {}
        for w in self.ways:
            data[w] = {}
            for b in self.bws:
                data[w][b] = float(findPattern(pattern, w, b, self.results))
        return data

    def _makeArray(self, usedict):
        data = []
        for b in sorted(self.bws):
            data.append(usedict[b])
        return data

    def plot(self, filename, doFit):
        
        xdata = []
        ydata = []
        maxpara = 0.0
        for w in ways:
            if self.plotStall:
                tmpreqpara = self._makeArray(self.stallCycles[w])
            else:
                tmpreqpara = self._makeArray(self.reqpara[w])
            ydata.append(tmpreqpara)
            xdata.append(self._makeArray(self.memReqCycles[w]))
            if max(tmpreqpara) > maxpara:
                maxpara =  max(tmpreqpara) 
        
        ylabel = "Memory Latency / Stall Cycle"
        if self.plotStall:
            ylabel = "Stall Cycles"
        
        plotRawScatter(xdata,
                       ydata,
                       yrange="0,"+str(maxpara*1.25),
                       legend=ways,
                       title=self.benchmark,
                       xlabel="Total Shared Memory Latency (cycles)",
                       ylabel=ylabel,
                       filename=filename,
                       fitLines=doFit)
    
    def dumpAll(self, decimals):
        print
        print "Stall cycles"
        self.dump(decimals, "stall")
        print
        print "Total Memory Latency"
        print
        self.dump(decimals, "latency")
        print
        print "Reqpara"
        print
        self.dump(decimals, "reqpara")
    
    def dump(self, decimals, datatype):
        header = [""]
        just = [True]
        for b in self.bws:
            header.append(printres.numberToString(b, decimals))
            just.append(False)
        data = [header]
        
        for w in self.ways:
            line = [str(w)]
            for b in self.bws:
                if datatype == "stall":
                    line.append(printres.numberToString(self.stallCycles[w][b], decimals))
                elif datatype == "latency":
                    line.append(printres.numberToString(self.memReqCycles[w][b], decimals))
                else:
                    line.append(printres.numberToString(self.reqpara[w][b], decimals))
            data.append(line)
            
        printres.printData(data, just, sys.stdout, decimals)
        
def parseArgs():
    parser = OptionParser(usage="plotOverlap.py [options] [benchmark]")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Suppress output")
    parser.add_option("--plot-stall", action="store_true", dest="plotStall", default=False, help="Plot stall cycles vs memory latency")
    parser.add_option("--fit-line", action="store_true", dest="fitLine", default=False, help="Add linear regression lines to plot")
    parser.add_option("-f", "--plot-filename", action="store", dest="plotfilename", default="", help="Write plot to this file")
    parser.add_option("--decimals", action="store", dest="decimals", default=3, help="Number of decimal places in output")
    
    opts, args = parser.parse_args()
    return opts,args
    
if __name__ == '__main__':
    opts,args = parseArgs()
    
    if not os.path.exists("index-all.pkl"):
        print
        fatal("Index file does not exist")
        
    if not os.path.exists("pbsconfig.py"):
        print
        fatal("pbsconfig.py not found")
        
    pbsconfigmodule = __import__("pbsconfig")
    pbsconfigobj = pbsconfigmodule.config
    
    if "MAX-CACHE-WAYS" in pbsconfigobj.variableSimulatorArguments:
        ways =  pbsconfigobj.variableSimulatorArguments["MAX-CACHE-WAYS"]
    else:
        fatal("MAX-CACHE-WAYS parameter must exist in simulator configuration")    
    
    if "MODEL-THROTLING-POLICY-STATIC" in pbsconfigobj.variableSimulatorArguments:
        bws =  pbsconfigobj.variableSimulatorArguments["MODEL-THROTLING-POLICY-STATIC"]
    else:
        fatal("MODEL-THROTLING-POLICY-STATIC parameter must exist in simulator configuration")
    
    print 
    
    if not opts.quiet:
        print
        print "Overlap Analysis"
        print
        print "Loading index... ",
        sys.stdout.flush()
    index = StatfileIndex("index-all")
    if not opts.quiet:
        print "done!"

    if len(args) > 0:
        stats = OverlapStats(args[0], index, ways, bws, opts.plotStall)
        
        stats.dumpAll(opts.decimals)
        stats.plot(opts.plotfilename, opts.fitLine)
    else:
        for bm in pbsconfigobj.getAllBenchmarks():
            print "Processing "+bm
            stats = OverlapStats(bm, index, ways, bws, opts.plotStall)
            stats.plot("reqpara-"+bm+".pdf", opts.fitLine)
        
        