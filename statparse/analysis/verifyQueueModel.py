#!/usr/bin/python

import sys
import os

from optparse import OptionParser
from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
import statparse.experimentConfiguration as expconfig 

def parseArgs():
    parser = OptionParser(usage="verifyQueueModel.py [options] benchmark")
    
    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    
    opts, args = parser.parse_args()
    if len(args) != 1:
        print "Command line error..."
        print "Usage "+parser.usage
        sys.exit(-1)
    
    return opts, args

class BandwidthModel:
    
    patterns = ["COM:count", "sim_ticks"]
    invalid  = "N/A"

    def __init__(self, bmname, results):
        self.searchRes = results.searchForPatterns(self.patterns)

        # Set up bw allocation structures
        self.arrivalRates = []
        for r in self.searchRes["detailedCPU0.COM:count"]:
            self.arrivalRates.append(self.getBW(r))
        self.arrivalRates.sort()
        self.indexMap = {}
        for i in range(len(self.arrivalRates)):
            self.indexMap[self.arrivalRates[i]] = i
        
        # Store selected statistics
        self.committedInstructions = self.getStat("detailedCPU0.COM:count")
        self.ticks = self.getStat("sim_ticks")

        print self.committedInstructions
        print self.ticks
    
    def getBW(self, r):
        return float(r.parameters["MODEL-THROTLING-POLICY-STATIC"])
    
    def getStat(self, key):
        tmp = [self.invalid for i in range(len(self.arrivalRates))]
        for r in self.searchRes[key]:
            tmp[self.indexMap[self.getBW(r)]] = float(self.searchRes[key][r])
        return tmp
        

def main():
    opts,args = parseArgs()
    bm = args[0]
    
    if not os.path.exists("pbsconfig.py"):
        print "ERROR: pbsconfig.py not found"
        return -1
    
    if not os.path.exists("index-all.pkl"):
        print "ERROR: cannot find index index-all.pkl, run searchStats.py to generate index"
        return -1
    
    if not opts.quiet:
        print >> sys.stdout, "Reading index file index-all.pkl... ",
        sys.stdout.flush()
    index = StatfileIndex("index-all")
    if not opts.quiet:
        print >> sys.stdout, "done!"
    
    searchConfig = expconfig.buildMatchAllConfig()
    searchConfig.benchmark = bm
    results = StatResults(index, searchConfig, False, opts.quiet)
    
    curModel = BandwidthModel(bm, results)

if __name__ == '__main__':
    main()