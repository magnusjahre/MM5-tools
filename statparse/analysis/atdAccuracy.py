#!/usr/bin/env python

from optparse import OptionParser
from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
import statparse.experimentConfiguration as expconfig 

import sys
import os

indexmodulename = "index-all"
numBanks = 4

def parseArgs():
    parser = OptionParser(usage="atdAccuracy.py [options] NP")
    
    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--full-map", action="store_true", dest="fullMap", default=False, help="Use full-map implementation results in parsing")
    
    opts, args = parser.parse_args()
    if len(args) != 1:
        print "Command line error..."
        print "Usage "+parser.usage
        sys.exit(-1)
    
    return opts, args

def generateSharedMissPatterns(np):
    
    patterns = {}
    
    for p in range(np):
        for b in range(numBanks):
    
            bankName = "SharedCache"+str(b)
            baseMissPatStr = bankName+".misses_per_cpu"
    
            missPattern = baseMissPatStr+"_"+str(p)
            aloneMissPattern = baseMissPatStr+"$"
            shadowMissPattern = bankName+".cpu_extra_misses_"+str(p)
            shadowAloneEstimatePattern = bankName+".estimated_shadow_misses_"+str(p)
            
            if p not in patterns:
                patterns[p] = {}
            patterns[p][b] = {"sMiss": missPattern,
                              "aMiss": aloneMissPattern,
                              "atdMiss": shadowMissPattern,
                              "atdEst": shadowAloneEstimatePattern}
            
    return patterns


def evaluateATDAccuracy(results, opts, np):
    patterns = generateSharedMissPatterns(np)
    for p in range(np):        
        for b in range(numBanks):
            patres = {}
            
            for name in patterns[p][b]:
                results.plainSearch(patterns[p][b][name])
                assert name not in patres
                patres[name] = results.noPatResults
                
#            processPatternRes(patres)
            
            
    
def main():
    
    if not os.path.exists("pbsconfig.py"):
        print "ERROR: pbsconfig.py not found"
        return -1
    
    if not os.path.exists(indexmodulename+".pkl"):
        print "ERROR: cannot find index "+indexmodulename+".pkl, run searchStats.py to generate index"
        return -1 
        
    opts, args = parseArgs()
    np = int(args[0])

    if not opts.quiet:
        print >> sys.stdout, "Reading index file "+indexmodulename+".pkl... ",
        sys.stdout.flush()
    index = StatfileIndex(indexmodulename)
    if not opts.quiet:
        print >> sys.stdout, "done!"
    
    searchConfig = expconfig.buildMatchAllConfig()
    results = StatResults(index, searchConfig, False, opts.quiet)
    
    evaluateATDAccuracy(results, opts, np)
         
if __name__ == '__main__':
    main()
