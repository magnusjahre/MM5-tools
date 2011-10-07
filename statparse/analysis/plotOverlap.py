#!/usr/bin/env python

from optparse import OptionParser
from statparse.util import fatal
from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
from statparse.plotResults import plotRawScatter

import statparse.experimentConfiguration as expconfig
import statparse.processResults as procres

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

    def __init__(self, bm, index, ways, bws):
        self.benchmark = bm        
        self.results = doSearch(bm, index)
        
        self.ways = ways
        self.bws = bws
        
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
                data[w][b] = findPattern(pattern, w, b, self.results)
        return data

    def _makeArray(self, usedict):
        data = []
        for b in sorted(self.bws):
            data.append(usedict[b])
        return data

    def plot(self):
        xdata = []
        ydata = []
        for w in ways:
            ydata.append(self._makeArray(self.reqpara[w]))
            xdata.append(self._makeArray(self.avgReqLatency[w]))
        
        plotRawScatter(xdata,
                       ydata,
                       yrange="0,"+str(max(self.reqpara)*1.1))
        
    
        
def parseArgs():
    parser = OptionParser(usage="plotOverlap.py [options] [benchmark]")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    
    opts, args = parser.parse_args()
    return opts,args
    
def handleMultibenchmark(index, opts):
    fatal("not impl")

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
        stats = OverlapStats(args[0], index, ways, bws)
        stats.plot()
    else:
        handleMultibenchmark(index, opts)
        