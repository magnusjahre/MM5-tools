#!/usr/bin/python

import sys
import os

from optparse import OptionParser
from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
from statparse.plotResults import plotLines
from math import sqrt
import statparse.experimentConfiguration as expconfig 
from statparse.analysis import computePercError

modelAlternatives = ["cpi", "bus", "overlap"]

def parseArgs():
    parser = OptionParser(usage="verifyQueueModel.py [options] benchmark")
    
    parser.add_option("--metric", action="store", dest="metric", default="cpi", help="The metric to model (Alternatives: "+str(modelAlternatives)+")")
    parser.add_option("--calibrate-to", action="store", type="int", dest="calibrateTo", default=-1, help="The configuration to calibrate the model against")
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

    def __init__(self, bmname, results, calTo):
        
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
        
        self.calibrateToID = calTo
        
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
        
        self.overlap = [self.stallCycles[i] / (self.busCycles[i] + self.noBusCycles[i]) for i in range(self.numConfigs)]
        self.computeCycles = self.ticks[self.calibrateToID] - self.stallCycles[self.calibrateToID] 
        self.CPIinfL2 = (self.computeCycles + (self.noBusCycles[self.calibrateToID] * self.overlap[self.calibrateToID])) / self.committedInstructions[self.calibrateToID]
        
        # TODO: may want to get bus writes as well
    
    def getBW(self, r):
        return float(r.parameters["MODEL-THROTLING-POLICY-STATIC"])
    
    def getStat(self, key):
        tmp = [self.invalid for i in range(len(self.arrivalRates))]
        for r in self.searchRes[key]:
            tmp[self.indexMap[self.getBW(r)]] = float(self.searchRes[key][r])
        return tmp
    
    def getLiuModel(self):
        
        fclk = 4.0*(10**9) #Hz
        k = 64 # byte
        B = 6.4 * 10**9 # Bps
        
        liumodel = [0 for i in range(self.numConfigs)]
        
        ma = (self.busReads[self.calibrateToID] *fclk) / self.ticks[self.calibrateToID]
        
        modcons = (ma**2 * k**2) / (B**2)

        for i in range(self.numConfigs):
            arrivalRate = self.busReads[i] / self.ticks[i]
            beta = arrivalRate / self.getLambda(self.calibrateToID)

            betaSqInv = 1 / (beta**2)
            
            liumodel[i] = self.CPIinfL2 / (1 - modcons*betaSqInv)
            
        return liumodel
    
    def getRatemodel(self):
        ratemodel = [0 for i in range(self.numConfigs)]

        for i in range(self.numConfigs):
            numerator = self.overlap[self.calibrateToID]*self.busReads[self.calibrateToID]*self.ticks[i]
            denom = self.ticks[self.calibrateToID]**2 * self.getMaxBW()
            
            ratemodel[i] = self.CPIinfL2 / (1 - (numerator/denom) )  
        
        return ratemodel
    
    def getLambda(self, id):
        return self.busReads[id] / self.ticks[id]
    
    def getTsq(self, id, useLambda):
        return self.busCycles[id] / (self.busReads[id] * useLambda) 
        
    def getSimpleModel(self, opts):
        
        simplemodel = [0 for i in range(self.numConfigs)]
                
        for i in range(self.numConfigs):
            simplemodel[i] = self.CPIinfL2 + ((self.overlap[self.calibrateToID]*self.busReads[self.calibrateToID]*self.getAvgBusEstimate(i)) / self.committedInstructions[self.calibrateToID]) 
            if not opts.quiet:
                actual = self.ticks[i] / self.committedInstructions[i]
                print "Simple CPI estimate", simplemodel[i], \
                      "actual", actual, \
                      "error", computePercError(simplemodel[i], actual), "%"
        
        return simplemodel
         
    def plot(self, opts):
        actualCPI = [self.ticks[i] / self.committedInstructions[i] for i in range(self.numConfigs)]
        
        rateModel = self.getRatemodel()
        #liu = self.getLiuModel()
        simple = self.getSimpleModel(opts)
        
        plotLines([self.arrivalRates, self.arrivalRates, self.arrivalRates],
                  [actualCPI, rateModel, simple],
                  legendTitles = ["Actual CPI", "Rate Model", "Simple"],
                  ylabel="CPI",
                  xlabel="Arrival Rate",
                  title=self.bmname)

    def getMaxBW(self):
        return self.busReads[self.calibrateToID] / self.busCycles[self.calibrateToID]
    
    def getAvgBusEstimate(self, id):
        return (self.ticks[id] / self.ticks[self.calibrateToID]) * (1.0 / self.getMaxBW())

    def plotBus(self, opts):
        actualBusLat = [self.busCycles[i] / self.busReads[i] for i in range(self.numConfigs)]
        
        estimateBusLat = [0 for i in range(self.numConfigs)]
        for i in range(self.numConfigs):
            estimateBusLat[i] = self.getAvgBusEstimate(i)
            if not opts.quiet:
                print "Bus latency estimate", estimateBusLat[i], \
                      "actual", self.busCycles[i] / self.busReads[i], \
                      "error", computePercError(estimateBusLat[i], self.busCycles[i] / self.busReads[i]), "%"
        
        plotLines([self.arrivalRates, self.arrivalRates],
                  [actualBusLat, estimateBusLat],
                  legendTitles = ["Actual", "Estimate"],
                  ylabel="Average Bus Latency (Clock Cycles)",
                  xlabel="Arrival Rate (Requests/Cycle)",
                  title=self.bmname)
        
    def plotOverlap(self, opts):
        
        if not opts.quiet:
            for i in range(self.numConfigs):
                print "Overlap estimate ", self.overlap[self.calibrateToID], \
                      "actual", self.overlap[i], \
                      "error", computePercError(self.overlap[self.calibrateToID], self.overlap[i]), "%"
        
        plotLines([self.arrivalRates, self.arrivalRates],
                  [self.overlap, [self.overlap[self.calibrateToID] for i in range(self.numConfigs)]],
                  legendTitles = ["Actual", "Estimate"],
                  ylabel="Overlap",
                  yrange="0,"+str(max(self.overlap)*1.05),
                  xlabel="Arrival Rate (Requests/Cycle)",
                  title=self.bmname)

def main():
    opts,args = parseArgs()
    bm = args[0]
    
    if opts.metric not in modelAlternatives:
        print "ERROR: Unknown metric argument, alternatives are "+str(modelAlternatives)
        return -1
    
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
    
    curModel = BandwidthModel(bm, results, opts.calibrateTo)
    
    if opts.metric == "cpi":
        curModel.plot(opts)
    elif opts.metric == "bus":
        curModel.plotBus(opts)
    elif opts.metric == "overlap":
        curModel.plotOverlap(opts)

if __name__ == '__main__':
    main()