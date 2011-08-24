#!/usr/bin/python

import sys
import os

from optparse import OptionParser
import optcomplete

from statparse.util import fatal, warn
from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
from statparse.plotResults import plotImage
from statparse.plotResults import plotRawScatter
from workloadfiles.workloads import Workload

import statparse.experimentConfiguration as expconfig
import statparse.processResults as procres
import statparse.printResults as printres
import re
import random
import pickle

ERRVAL = "N/A"

class ProfileResult:
    
    def __init__(self, xstat, xnames, ystat, ynames):
        self.xnames = xnames
        self.ynames = ynames
        self.xstat = xstat
        self.ystat = ystat
        
        self.xmap = {}
        self.ymap = {}
        self.profile = []
        
        self.maxySpeedup = 0
        self.maxxSpeedup = 0
        
        for y in range(len(self.ynames)):
            self.profile.append([ERRVAL for i in self.xnames])
            self.ymap[self.ynames[y]] = y
        
        for x in range(len(self.xnames)):
            self.xmap[self.xnames[x]] = x 
                
    def addResult(self, xname, yname, value):
        self.profile[self.ymap[yname]][self.xmap[xname]] = value
        
    def getResult(self, xname, yname):
        return self.profile[self.ymap[yname]][self.xmap[xname]]
    
    def updateSpeedups(self):
        
        self.maxySpeedup = 0
        self.maxxSpeedup = 0
        
        for i in range(len(self.ynames)):
            curxSpeedup = self.profile[i][-1] / self.profile[i][0]
            if curxSpeedup > self.maxxSpeedup:
                self.maxxSpeedup = curxSpeedup
    
        for i in range(len(self.xnames)):
            curySpeedup = self.profile[-1][i] / self.profile[0][i]
            if curySpeedup > self.maxySpeedup:
                self.maxySpeedup = curySpeedup

class ProfileSpeedups:
    
    def __init__(self):
        self.xSpeedups = []
        self.ySpeedups = []
        self.benchmarks = []
        
        self.xstat = ""
        self.ystat = ""
        
    def checkStat(self, profile):
        xstat = profile.xstat
        ystat = profile.ystat
        
        if self.xstat != "":
            assert(self.xstat == xstat)
        else:
            self.xstat = xstat
            
        if self.ystat != "":
            assert(self.ystat == ystat)
        else:
            self.ystat = ystat
            
    def addStat(self, profile, bm):
        self.benchmarks.append(bm)
        self.xSpeedups.append(profile.maxxSpeedup)
        self.ySpeedups.append(profile.maxySpeedup)
        
    def plot(self):
        plotRawScatter(self.xSpeedups,
                       self.ySpeedups,
                       xlabel = self.xstat,
                       ylabel = self.ystat)
        
    def classify(self, opts):
        
        xlim = 2.0
        ylim = 1.5
        
        both = []
        ysens = []
        xsens = []
        none = []
        
        for i in range(len(self.xSpeedups)):
            if self.xSpeedups[i] > xlim and self.ySpeedups[i] > ylim:
                both.append(self.benchmarks[i])
            elif self.xSpeedups[i] > xlim:
                xsens.append(self.benchmarks[i])
            elif self.ySpeedups[i] > ylim:
                ysens.append(self.benchmarks[i])
            else:
                none.append(self.benchmarks[i])
        
        random.seed(42)
        
        print
        print "Benchmark classification with xlim="+str(xlim)+" and ylim="+str(ylim)
        print
        print "Both: "+str(both)
        print self.ystat+": "+str(ysens)
        print self.xstat+": "+str(xsens)
        print "None: "+str(none)
        print
        
        self.workloads = {}
        self.coverage = {}
        for np in [2,4,8]:
            self.workloads[np] = {}
            self.coverage[np] = [False for i in range(len(self.benchmarks))]
            self.addWlType(np, "a", 10, both)
            self.addWlType(np, "b", 10, xsens)
            self.addWlType(np, "c", 10, ysens)
            self.addWlType(np, "n", 10, none)
        
        print
        print "Generated the following workloads"
        print
        for np in self.workloads:
            print np
            print "Benchmarks not included: ",
            for i in range(len(self.coverage[np])):
                if not self.coverage[np][i]:
                    print self.benchmarks[i],
                    if self.benchmarks[i] not in none:
                        print "(NOT NONE)",
                    
            print
            
            for type in self.workloads[np]:
                print type
                for wl in self.workloads[np][type]:
                    print str(wl)
                    
        outfile = open("typewls.pkl", "w")
        pickle.dump(self.workloads, outfile)
        outfile.close()
        
                
    def addWlType(self, np, key, count, bms):
        self.workloads[np][key] = []
        for i in range(count):
            self.workloads[np][key].append(self.findWorkload(bms, np))
    
    def findWorkload(self, bms, np):
        wl = Workload()
       
        while wl.getNumBms() < np:
            index = random.randint(0, len(bms)-1)
            wl.addBenchmark(bms[index])
            
            for i in range(len(self.benchmarks)):
                if bms[index] == self.benchmarks[i]:
                    self.coverage[np][i] = True
        return wl

def parseArgs():
    parser = OptionParser(usage="getProfile.py [options] statistic-pattern [statistic-pattern]")

    parser.add_option("--plot", action="store_true", dest="plot", default=False, help="Print the results as a heat map")
    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Suppress output")
    parser.add_option("--vector-dist", action="store_true", dest="vectorDist", default=False, help="The pattern identifies a Vector Distribution")
    parser.add_option("--index-file", action="store", dest="indexfile", default="index-all", help="Use a different index file")
    parser.add_option("--benchmark", action="store", dest="benchmark", default="", help="Only print profile for given benchmark")
    parser.add_option("--decimals", action="store", dest="decimals", default=2, type="int", help="Number of decimals to print")
    parser.add_option("--generate-wls", action="store_true", dest="genWls", default=False, help="Generate multiprogrammed workloads")

    optcomplete.autocomplete(parser)

    opts, args = parser.parse_args()
    
    if len(args) == 0 or len(args) > 2:
        print "Command line error..."
        print "Usage : "+parser.usage
        sys.exit(-1)
    
    return opts, args

def doSearch(pattern, benchmark, index, opts):
    searchConfig = expconfig.buildMatchAllConfig()
    searchConfig.benchmark = benchmark
    results = StatResults(index,
                          searchConfig,
                          False,
                          opts.quiet)
    
    results.plainSearch(pattern)
    return results

def cleanDistributionKeys(distribution):
    removekeys = ["max_value", "min_value", "overflows", "samples"]
    for k in removekeys:
        if k in distribution:
            distribution.remove(k)
    return distribution

def getIDFromStatNames(names):
    map = {}
    for n in names:
        val = re.search("([0-9]+).dist", n)
        if not val:
            fatal("Pattern "+n+" does not have the expected format")
        id = int(val.group(1))
        map[id] = n
    return map

def doDistVectorSearch(pattern, benchmark, index, opts):
    searchConfig = expconfig.buildMatchAllConfig()
    searchConfig.benchmark = benchmark
    results = StatResults(index,
                          searchConfig,
                          False,
                          opts.quiet)
    
    searchRes = results.searchForPatterns([pattern])
    print
    idStatMap = getIDFromStatNames(searchRes.keys())
    
    xnames = sorted(idStatMap.keys())
    results.plainSearch(idStatMap[xnames[0]])
    if len(results.matchingConfigs) != 1:
        fatal("0 or more than one config matched the pattern")
    ynames = sorted(cleanDistributionKeys(results.noPatResults[results.matchingConfigs[0]].keys()))
    profile = ProfileResult("", xnames, "", ynames)
    
    for id in xnames:
        results.plainSearch(idStatMap[id])
        if len(results.matchingConfigs) != 1:
            fatal("0 or more than one config matched the pattern")
            
        dist = results.noPatResults[results.matchingConfigs[0]]
        keys = sorted(cleanDistributionKeys(dist.keys()))
        
        assert len(keys) == len(ynames)
        for i in range(len(keys)):
            assert keys[i] == ynames[i]
        
        for k in ynames:
            profile.addResult(id, k, dist[k])
        
    return profile

def getProfile(benchmark, opts, pattern, pbsconfigobj, index, pattern2 = None):
    
    if opts.vectorDist:
        if pattern2 != None:
            warn("Distribution vector parsing, second statistic pattern ignored...")
        return doDistVectorSearch(pattern, benchmark, index, opts)
    else:
        results = doSearch(pattern, benchmark, index, opts)
    
    if results.noPatResults == {}:
        fatal("No results found, for pattern "+pattern+" and benchmark "+benchmark)
    
    if pattern2 != None:

        results2 = doSearch(pattern2, benchmark, index, opts)
        if results2.noPatResults == {}:
            fatal("No results found, for pattern "+pattern2+" and benchmark "+benchmark)
            
    
    keys = pbsconfigobj.variableSimulatorArguments.keys()
    if len(keys) != 2:
        fatal("This script handles exactly two variable arguments in the pbsconfig file")
        
    searchConfig = expconfig.buildMatchAllConfig()
    
    xargs = pbsconfigobj.variableSimulatorArguments[keys[0]]
    yargs = pbsconfigobj.variableSimulatorArguments[keys[1]]
    profile = ProfileResult(keys[0], xargs, keys[1], yargs)
    
    for y in yargs:
        for x in xargs:
            searchConfig.parameters[keys[0]] = x
            searchConfig.parameters[keys[1]] = y
            
            configRes = procres.filterConfigurations(results.matchingConfigs, searchConfig)
            if pattern2 != None:
                configRes2 = procres.filterConfigurations(results2.matchingConfigs, searchConfig)
            
            if(len(configRes) > 1):
                fatal("Multiple results for benchmark "+str(benchmark)+", pattern must be refined")
            elif len(configRes) == 0:
                continue
            
            if pattern2 != None:
                res = float(results.noPatResults[configRes[0]]) / float(results2.noPatResults[configRes2[0]])
            else:
                res = results.noPatResults[configRes[0]]
            
            profile.addResult(x, y, res)

    return profile

def printTable(profile, opts, outfilename = ""):
    
    header = [""]
    for x in profile.xnames:
        header.append(printres.numberToString(x, opts.decimals))
    
    textarray = []
    textarray.append(header)
    
    for y in profile.ynames:
        line = [printres.numberToString(y, opts.decimals)]
        for x in profile.xnames:
            line.append(printres.numberToString(profile.getResult(x,y), opts.decimals))
    
        textarray.append(line)
    
    just = [True]
    for i in profile.xnames:
        just.append(False)
        
    if outfilename != "":
        outfile = open(outfilename, "w")
    else:
        outfile = sys.stdout
        
    printres.printData(textarray, just, outfile, opts.decimals)

    if outfilename != "":
        outfile.close() 

def doPlot(benchmark, pattern, profile, filename = ""):
    
    yrangestr = "-0.5,"+str(len(profile.ynames)-0.5)
    xrangestr = "-0.5,"+str(len(profile.xnames)-0.5)
    zrangestr = "0,"+str(max(max(profile.profile)))
    
    plotImage(profile.profile,
              xlabel=profile.xstat,
              ylabel=profile.ystat,
              zlabel=pattern,
              title=benchmark,
              xticklabels=profile.xnames,
              yticklabels=profile.ynames,
              yrange=yrangestr,
              xrange=xrangestr,
              zrange=zrangestr,
              filename=filename)

def main():
    
    opts,args = parseArgs()
    
    pattern = args[0]
    if len(args) == 2:
        pattern2 = args[1]
    else:
        pattern2 = None
        
    if not os.path.exists("pbsconfig.py"):
        if not opts.vectorDist:
            print fatal("pbsconfig.py not found")
        pbsconfigobj = None
    else:
        pbsconfigmodule = __import__("pbsconfig")
        pbsconfigobj = pbsconfigmodule.config

    if not os.path.exists(opts.indexfile+".pkl"): 
        print fatal("Index file does not exist")
    

    if not opts.quiet:
        print
        print "Retrieving profile..."
        print
        print "Loading index "+str(opts.indexfile)+"...",
        sys.stdout.flush()
    index = StatfileIndex(opts.indexfile)
    if not opts.quiet:
        print "done!"

    speedupProfile = ProfileSpeedups()
    
    if opts.benchmark != "":
        profile = getProfile(opts.benchmark, opts, pattern, pbsconfigobj, index, pattern2)
        printTable(profile, opts)
        profile.updateSpeedups()
        
        if opts.plot:
            doPlot(opts.benchmark, pattern, profile)
    else:
        
        if pbsconfigobj == None:
            fatal("pbsconfig.py file needed for multi-benchmark analysis, specify the --benchmark option if you want single benchmark analysis")
        
        if 1 not in pbsconfigobj.workloads:
            fatal("Cannot find any single core experiments in configuration file")
        
        for bm in pbsconfigobj.workloads[1]:
            if not opts.quiet:
                print "Processing "+bm
            profile = getProfile(bm, opts, pattern, pbsconfigobj, index, pattern2)
            printTable(profile, opts, "profile-data-"+bm+".txt")
            profile.updateSpeedups()
            
            speedupProfile.checkStat(profile)
            speedupProfile.addStat(profile, bm)
            
            if opts.plot:
                doPlot(bm, pattern, profile, "profile-plot-"+bm+".pdf")
        
        if opts.genWls:
            speedupProfile.classify(opts)
        

if __name__ == '__main__':
    main()