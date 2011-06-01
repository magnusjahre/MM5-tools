#!/usr/bin/python

import sys
import os

from optparse import OptionParser
from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults
from statparse.plotResults import plotLines
from math import sqrt, fabs
import statparse.experimentConfiguration as expconfig 
from statparse.analysis import computePercError
from statparse.printResults import printData, numberToString
from util.subfigure import Subfigure

import workloadfiles.workloads as wls

modelAlternatives = ["cpi", "bus", "overlap"]

def parseArgs():
    parser = OptionParser(usage="verifyQueueModel.py [options] [benchmark]")
    
    parser.add_option("--metric", action="store", dest="metric", default="cpi", help="The metric to model (Alternatives: " + str(modelAlternatives) + ")")
    parser.add_option("--calibrate-to", action="store", type="int", dest="calibrateTo", default= -1, help="The configuration to calibrate the model against")
    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    
    parser.add_option("--cutoff", action="store", type="float", dest="cutoff", default=5, help="Only include figures where the absolute error is larger than this value")
    
    parser.add_option("--fig-title", action="store", dest="figtitle", default="CPI Accuracy", help="Figure title")
    parser.add_option("--fig-width", action="store", type="float", dest="figwidth", default=0.2, help="Figure width")
    parser.add_option("--fig-cols", action="store", type="int", dest="figcols", default=4, help="Figure columns")
    
    opts, args = parser.parse_args()
    if len(args) > 1:
        print "Command line error..."
        print "Usage " + parser.usage
        sys.exit(-1)
    
    return opts, args

class ErrorMeasurement:
    
    def __init__(self, actual, estimate):
        self.actual = actual
        self.estimate = estimate
        self.percerr = computePercError(estimate, actual)

class ModelErrors:
    
    def __init__(self):
        self.cpidata = {}
        self.busdata = {}
        self.overlapdata = {}
        
        self.arrivalRates = []
        
    def add(self, bwModel):
        assert bwModel.bmname not in self.cpidata
        assert bwModel.bmname not in self.busdata
        assert bwModel.bmname not in self.overlapdata
        
        self.cpidata[bwModel.bmname] = bwModel.cpistats
        self.busdata[bwModel.bmname] = bwModel.busstats
        self.overlapdata[bwModel.bmname] = bwModel.overlapstats
        
        if self.arrivalRates == []:
            self.arrivalRates = bwModel.arrivalRates
        
    def dump(self):
        self.printPercErrorData("cpi-perc-err.txt", self.cpidata)
        self.printPercErrorData("bus-perc-err.txt", self.busdata)
        self.printPercErrorData("overlap-perc-err.txt", self.overlapdata)
        
    def printPercErrorData(self, filename, data):
        lines = []
        header = [""]
        leftjust = [True]
        for i in self.arrivalRates:
            header.append(str(i))
            leftjust.append(False)
        lines.append(header)
        
        for bm in data:
            line = [bm]
            for e in data[bm]:
                line.append(numberToString(e.percerr, 2))
            lines.append(line)
            
        outfile = open(filename, "w")
        printData(lines, leftjust, outfile, 2)
        outfile.close()
        

class BandwidthModel:
    
    patterns = ["COM:count",
                "sim_ticks",
                "interferenceManager.cpu_stall_cycles",
                "interferenceManager.bus_latency",
                "interferenceManager.no_bus_latency",
                "interferenceManager.requests",
                "membus0.reads_per_cpu",
                "interferenceManager.latency_bus_service"]
    
    invalidKey = "N/A"

    def __init__(self, bmname, results, calTo):
        
        self.bmname = bmname
        
        self.searchRes = results.searchForPatterns(self.patterns)

        # Set up bw allocation structures
        self.arrivalRates = []
        for r in self.searchRes["detailedCPU0.COM:count"]:
            self.arrivalRates.append(self.getBW(r))
        self.arrivalRates.sort()
        
        if self.arrivalRates == []:
            self.invalid = True
            return
        self.invalid = False
        
        self.indexMap = {}
        for i in range(len(self.arrivalRates)):
            self.indexMap[self.arrivalRates[i]] = i
        self.numConfigs = len(self.indexMap)
        
        self.cpistats = [None for i in range(self.numConfigs)]
        self.overlapstats = [None for i in range(self.numConfigs)]
        self.busstats = [None for i in range(self.numConfigs)]
        
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
        tmp = [self.invalidKey for i in range(len(self.arrivalRates))]
        for r in self.searchRes[key]:
            tmp[self.indexMap[self.getBW(r)]] = float(self.searchRes[key][r])
        return tmp
    
    def getLiuModel(self):
        
        fclk = 4.0 * (10 ** 9) #Hz
        k = 64 # byte
        B = 6.4 * 10 ** 9 # Bps
        
        liumodel = [0 for i in range(self.numConfigs)]
        
        ma = (self.busReads[self.calibrateToID] * fclk) / self.ticks[self.calibrateToID]
        
        modcons = (ma ** 2 * k ** 2) / (B ** 2)

        for i in range(self.numConfigs):
            arrivalRate = self.busReads[i] / self.ticks[i]
            beta = arrivalRate / self.getLambda(self.calibrateToID)

            betaSqInv = 1 / (beta ** 2)
            
            liumodel[i] = self.CPIinfL2 / (1 - modcons * betaSqInv)
            
        return liumodel
    
    def getRatemodel(self):
        ratemodel = [0 for i in range(self.numConfigs)]

        for i in range(self.numConfigs):
            numerator = self.overlap[self.calibrateToID] * self.busReads[self.calibrateToID] * self.ticks[i]
            denom = self.ticks[self.calibrateToID] ** 2 * self.getCalibrateBW()
            
            ratemodel[i] = self.CPIinfL2 / (1 - (numerator / denom))  
        
        return ratemodel
    
    def getLambda(self, id):
        return self.busReads[id] / self.ticks[id]
    
    def getTsq(self, id, useLambda):
        return self.busCycles[id] / (self.busReads[id] * useLambda) 
        
    def getSimpleModel(self, opts):
        
        simplemodel = [0 for i in range(self.numConfigs)]
                
        for i in range(self.numConfigs):
            simplemodel[i] = self.CPIinfL2 + ((self.overlap[self.calibrateToID] * self.busReads[self.calibrateToID] * self.getAvgBusEstimate(i)) / self.committedInstructions[self.calibrateToID]) 
            actual = self.ticks[i] / self.committedInstructions[i]
            self.cpistats[i] = ErrorMeasurement(actual, simplemodel[i])
        
        return simplemodel
         
    def plot(self, opts, filename = ""):
        actualCPI = [self.ticks[i] / self.committedInstructions[i] for i in range(self.numConfigs)]
        
        rateModel = self.getRatemodel()
        #liu = self.getLiuModel()
        simple = self.getSimpleModel(opts)
        
        plotLines([self.arrivalRates, self.arrivalRates, self.arrivalRates],
                  [actualCPI, rateModel, simple],
                  legendTitles=["Actual CPI", "Rate Model", "Simple"],
                  ylabel="CPI",
                  xlabel="Arrival Rate",
                  yrange="0," + str(max(actualCPI) * 1.1),
                  title=self.bmname,
                  filename=filename)

    def getCalibrateBW(self):
        return self.busReads[self.calibrateToID] / self.busCycles[self.calibrateToID]
    
    def getAvgBusEstimate(self, id):
        return (self.ticks[id] / self.ticks[self.calibrateToID]) * (1.0 / self.getCalibrateBW())

    def plotBus(self, opts, filename = ""):
        actualBusLat = [self.busCycles[i] / self.busReads[i] for i in range(self.numConfigs)]
        
        estimateBusLat = [0 for i in range(self.numConfigs)]
        for i in range(self.numConfigs):
            estimateBusLat[i] = self.getAvgBusEstimate(i)
            self.busstats[i] = ErrorMeasurement(self.busCycles[i] / self.busReads[i], estimateBusLat[i])
        
        plotLines([self.arrivalRates, self.arrivalRates],
                  [actualBusLat, estimateBusLat],
                  legendTitles=["Actual", "Estimate"],
                  ylabel="Average Bus Latency (Clock Cycles)",
                  xlabel="Arrival Rate (Requests/Cycle)",
                  yrange="0," + str(max(actualBusLat) * 1.1),
                  title=self.bmname,
                  filename=filename)
        
    def plotOverlap(self, opts, filename = ""):
        
        for i in range(self.numConfigs):
            self.overlapstats[i] = ErrorMeasurement(self.overlap[i], self.overlap[self.calibrateToID])
        
        plotLines([self.arrivalRates, self.arrivalRates],
                  [self.overlap, [self.overlap[self.calibrateToID] for i in range(self.numConfigs)]],
                  legendTitles=["Actual", "Estimate"],
                  ylabel="Overlap",
                  yrange="0," + str(max(self.overlap) * 1.05),
                  xlabel="Arrival Rate (Requests/Cycle)",
                  title=self.bmname,
                  filename=filename)

def main():
    opts, args = parseArgs()
    
    if opts.metric not in modelAlternatives:
        print "ERROR: Unknown metric argument, alternatives are " + str(modelAlternatives)
        return - 1
    
    if not os.path.exists("pbsconfig.py"):
        print "ERROR: pbsconfig.py not found"
        return - 1
    
    if not os.path.exists("index-all.pkl"):
        print "ERROR: cannot find index index-all.pkl, run searchStats.py to generate index"
        return - 1
    
    if not opts.quiet:
        print >> sys.stdout, "Reading index file index-all.pkl... ",
        sys.stdout.flush()
    index = StatfileIndex("index-all")
    if not opts.quiet:
        print >> sys.stdout, "done!"
    
    if len(args) == 1:
    
        bm = args[0]
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
            
    else:
        
        errors = ModelErrors()
        subfig = Subfigure("cpi-accuracy.tex")
        
        for bm in wls.getAllBenchmarks():
            
            if not opts.quiet:
                print "Processing benchmark " + bm
            
            searchConfig = expconfig.buildMatchAllConfig()
            searchConfig.benchmark = bm
            results = StatResults(index, searchConfig, False, opts.quiet)

            curModel = BandwidthModel(bm, results, opts.calibrateTo)
            
            if not curModel.invalid:
                cpiname = bm + "-cpi.pdf"
                curModel.plot(opts, cpiname)
                curModel.plotBus(opts, bm + "-bus.pdf")
                curModel.plotOverlap(opts, bm + "-overlap.pdf")
                
                if fabs(curModel.cpistats[0].percerr) > opts.cutoff:
                    subfig.addFigure(cpiname, bm)
                
                errors.add(curModel)
            else:
                print "Warning: search failed for benchmark "+bm


        errors.dump()
        subfig.writeLatex(opts.figtitle, "fig:cpiAccuracy", opts.figwidth, opts.figcols)

if __name__ == '__main__':
    main()
