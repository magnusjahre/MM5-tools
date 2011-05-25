#!/usr/bin/python

import sys
import os

from optparse import OptionParser
from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
from statparse.plotResults import plotLines
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
    
    patterns = ["COM:count",
                "sim_ticks",
                "interferenceManager.cpu_stall_cycles",
                "interferenceManager.bus_latency",
                "interferenceManager.no_bus_latency",
                "interferenceManager.requests",
                "membus0.reads_per_cpu",
                "interferenceManager.latency_bus_service"]
    
    invalid  = "N/A"

    def __init__(self, bmname, results):
        
        self.bmname = bmname
        
        self.searchRes = results.searchForPatterns(self.patterns)

        # Set up bw allocation structures
        self.arrivalRates = []
        for r in self.searchRes["detailedCPU0.COM:count"]:
            self.arrivalRates.append(self.getBW(r))
        self.arrivalRates.sort()
        self.indexMap = {}
        for i in range(len(self.arrivalRates)):
            self.indexMap[self.arrivalRates[i]] = i
        self.numConfigs = len(self.indexMap)
        self.calibrateToID = self.numConfigs-1
        
        # Store selected statistics
        self.committedInstructions = self.getStat("detailedCPU0.COM:count")
        self.ticks = self.getStat("sim_ticks")
        self.stallCycles = self.getStat("interferenceManager.cpu_stall_cycles")
        self.busCycles = self.getStat("interferenceManager.bus_latency")
        self.noBusCycles = self.getStat("interferenceManager.no_bus_latency")
        self.busServiceCycles = self.getStat("interferenceManager.latency_bus_service")
        self.requests = self.getStat("interferenceManager.requests")
        self.busReads = self.getStat("membus0.reads_per_cpu")
        
        self.avgBusServiceCycles = [self.busServiceCycles[i] / self.requests[i] for i in range(self.numConfigs)]
        
        self.overlap = self.stallCycles[self.calibrateToID] / (self.busCycles[self.calibrateToID] + self.noBusCycles[self.calibrateToID])
        self.computeCycles = self.ticks[self.calibrateToID] - self.stallCycles[self.calibrateToID] 
        self.CPIinfL2 = (self.computeCycles + (self.noBusCycles[self.calibrateToID] * self.overlap)) / self.committedInstructions[self.calibrateToID]
        
        # TODO: may want to get bus writes as well
        
        print "Parameter arrival rates: "+str(self.arrivalRates)
        print "Actual arrival rates:    "+str(sorted([self.busReads[i] / self.ticks[i] for i in range(self.numConfigs)]))
    
    def getBW(self, r):
        return float(r.parameters["MODEL-THROTLING-POLICY-STATIC"])
    
    def getStat(self, key):
        tmp = [self.invalid for i in range(len(self.arrivalRates))]
        for r in self.searchRes[key]:
            tmp[self.indexMap[self.getBW(r)]] = float(self.searchRes[key][r])
        return tmp
    
    def getLiuModel(self):
        
        liumodel = [0 for i in range(self.numConfigs)]
        
        
        return liumodel
    
    def getRatemodel(self):
        ratemodel = [0 for i in range(self.numConfigs)]

        calibrateLambda = self.busReads[self.calibrateToID] / self.ticks[self.calibrateToID]
        calibrateT = self.busCycles[self.calibrateToID] / self.busReads[self.calibrateToID]
        calibrateN = self.busCycles[self.calibrateToID] / self.ticks[self.calibrateToID]

        print calibrateLambda, calibrateN, calibrateT

        modelConst = (self.overlap * calibrateT**2 * self.busReads[self.calibrateToID]) / self.ticks[self.calibrateToID]

        print modelConst

        for i in range(self.numConfigs):
            arrivalRate = self.busReads[i] / self.ticks[i]
            ratemodel[i] = self.CPIinfL2 / (1 - (arrivalRate * modelConst) )
            
        return ratemodel
        
    def getSimpleModel(self):
        
        simplemodel = [0 for i in range(self.numConfigs)]
        
        calibrateT = self.busCycles[self.calibrateToID] / self.busReads[self.calibrateToID]
        calibrateLambda = self.busReads[self.calibrateToID] / self.ticks[self.calibrateToID]
        
        modelconst = calibrateLambda * self.overlap * calibrateT**2 * self.busReads[self.calibrateToID]
        
        for i in range(self.numConfigs):
            arrivalRate = self.busReads[i] / self.ticks[i]
            arrivalRatio = calibrateLambda / arrivalRate 
            print "Estimated bus time: "+str(arrivalRatio*modelconst)+", actual "+str(self.busCycles[i])
            simplemodel[i] = self.CPIinfL2 + ((arrivalRatio*modelconst) / self.committedInstructions[i]) 
        
        return simplemodel
         
    def plot(self, opts):
        actualCPI = [self.ticks[i] / self.committedInstructions[i] for i in range(self.numConfigs)]
        
        rateModel = self.getRatemodel()
        liu = self.getLiuModel()
        simple = self.getSimpleModel()
        
        plotLines([self.arrivalRates, self.arrivalRates, self.arrivalRates, self.arrivalRates],
                  [actualCPI, rateModel, liu, simple],
                  legendTitles = ["Actual CPI", "Rate Model", "Liu et al.", "Simple"],
                  ylabel="CPI",
                  xlabel="Arrival Rate",
                  title=self.bmname)

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
    curModel.plot(opts)

if __name__ == '__main__':
    main()