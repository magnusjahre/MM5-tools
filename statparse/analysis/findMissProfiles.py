#!/usr/bin/python

import sys
import os

from optparse import OptionParser

from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
import statparse.experimentConfiguration as expconfig 

from statparse.plotResults import plotLines

import workloadfiles.workloads as wls
import shutil

def parseArgs():
    parser = OptionParser(usage="verifyQueueModel.py [options] [benchmark]")
    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    
    opts, args = parser.parse_args()
    if len(args) > 1:
        print "Command line error..."
        print "Usage " + parser.usage
        sys.exit(-1)
    
    return args, opts

class MissProfile:
    
    SETS = 16
    BANKS = 4
    
    def __init__(self, bm, index, opts):
        
        self.opts = opts
        self.benchmark = bm
        
        searchConfig = expconfig.buildMatchAllConfig()
        searchConfig.benchmark = bm
        searchConfig.np = 1
        results = StatResults(index, searchConfig, False, opts.quiet)
        
        self.rawdata = results.searchForPatterns(["SharedCache.*cache_hit_distribution_0.dist",
                                                  "SharedCache.*overall_misses"])
    
        if self.rawdata["SharedCache0.cache_hit_distribution_0.dist"] == {}:
            self.valid = False
            print "ERROR: empty search results for benchmark "+bm
            return
        else:
            self.valid = True
        
        self.hitDistribution = [0 for i in range(self.SETS)]
        
        self.minmisses = 0

        for b in range(self.BANKS):
            thisStat = self.getStatVector("SharedCache"+str(b)+".cache_hit_distribution_0.dist")
            self.accumulateDistribution(thisStat)
            
        for b in range(self.BANKS):
            self.minmisses += self.getStat("SharedCache"+str(b)+".overall_misses")
        
        cumulativeHits = [self.hitDistribution[0] for i in range(self.SETS)]
        for i in range(1, self.SETS):
            cumulativeHits[i] = cumulativeHits[i-1] + self.hitDistribution[i]
        
        self.maxmisses = self.minmisses+cumulativeHits[-1]
        
        self.missDistribution = [self.maxmisses-cumulativeHits[i] for i in range(self.SETS)]

    def accumulateDistribution(self, newdata):
        assert len(newdata) == len(self.hitDistribution)
        for i in range(len(newdata)):
            self.hitDistribution[i] += newdata[i]

    def getStat(self, key):
        assert len(self.rawdata[key].keys()) == 1
        curconf = self.rawdata[key].keys()[0]
        return float(self.rawdata[key][curconf])

    def getStatVector(self, key):
        assert len(self.rawdata[key].keys()) == 1
        curconf = self.rawdata[key].keys()[0]
        tmp = [float(self.rawdata[key][curconf][i]) for i in range(self.SETS)]
        return tmp

    def plot(self, filename = ""):
        plotLines([[i for i in range(1, self.SETS+1)]],
                  [self.missDistribution],
                  title=self.benchmark,
                  xlabel="Shared Cache Sets",
                  ylabel="Number of Cache Misses",
                  yrange="0,"+str(max(self.missDistribution)*1.1),
                  filename=filename)

def main():
    args, opts = parseArgs()
    
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
    
    if len(args) == 1:
        profile = MissProfile(args[0], index, opts)
        if profile.valid:
            profile.plot()
        
    else:
        foldername = "missprofiles"
        
        os.mkdir(foldername)
        
        for bm in wls.getAllBenchmarks():
            
            if not opts.quiet:
                print "Processing benchmark " + bm
                
            profile = MissProfile(bm, index, opts)
            if profile.valid:
                profile.plot(foldername+"/"+bm+"-missprofile.pdf")
        

if __name__ == '__main__':
    main()