#!/usr/bin/env python

import sys
from optparse import OptionParser
from misc.sag import fatal

from statparse.plotResults import plotRawLinePlot, plotRawScatter
from statparse.printResults import printData, numberToString

def parseArgs():
    parser = OptionParser(usage="evaluatePeriodicApplication.py [options] model-file cores serial-fraction")

    parser.add_option("--verbose", action="store_true", dest="verbose", default=False, help="Enable verbose output")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--outfile", action="store", dest="outfile", type="string", default=None, help="Filename of the plot file")
    parser.add_option("--analyse-cores", action="store_true", dest="analyseCores", default=False, help="Find the minium energy points for each core configuration")
    parser.add_option("--single-scatter", action="store_true", dest="singleScatter", default=False, help="Analyse a single architecture with all frequency pairs")
    parser.add_option("--scatter-feasible", action="store_true", dest="scatterFeasible", default=False, help="Zoom scatter on the feasible points")
    parser.add_option("--datafile", action="store", dest="datafile", default="", help="Write data according to specification in this file")
    parser.add_option("--test", action="store_true", dest="test", default=False, help="Run regression test suite")
    parser.add_option("--utilization", action="store", dest="utilization", type="float", default=0.75, help="Percentage of computing capacity used to process a sample")
    
    opts, args = parser.parse_args()

    if len(args) != 3:
        print
        print "Commandline error:"
        print parser.usage
        print 
        sys.exit(0)
        
    return args, opts

def readModelFile(modelfilename):
    model = {}
    f = open(modelfilename)
    for l in f:
        # Note: Eval of non-validated input is very bad practise since it may
        # enable evaluation of arbitrary code
        try:
            data = l.split("=")
            key = data[0].strip()
            if data[1][0] == "s":
                value = [float(eval(data[1][1:]))]
            else:
                assert data[1][0] == "v"
                value = [float(eval(v)) for v in data[1][1:].split(";")]
        except:
            fatal("Cannot parse model config line:\n"+str(l))
        
        assert key not in model
        if key[0] == "P":
            model[key] = [v*10**-6 for v in value]
        else:
            model[key] = value
    
    assert len(model["f"]) == len(model["V"])
    operatingPoints = []
    for i in range(len(model["f"])):
        operatingPoints.append( (model["V"][i], model["f"][i]*10**6) )
        
    assert "OP" not in model
    model["OP"] = operatingPoints
    
    return model

def printEnergyData(vRange, data, opts):
    
    lines = []
    header = [""]
    justify = [True]
    for v in vRange:
        header.append(numberToString(v, opts.decimals))
        justify.append(False)
    lines.append(header)
    
    for series in data:
        line = [series[0]]
        for d in series[1:]:
            line.append(numberToString(d, opts.decimals))
        lines.append(line)
    
    print
    print "Estimated Energy:"
    print
    printData(lines, justify, sys.stdout, opts.decimals)

class VoltagePoint:
    
    def __init__(self, v, f):
        self.v = v
        self.f = f

class OperatingPoint:
    
    def __init__(self, serOPIndex, paraOPIndex, cores, serialFraction, model):
        
        self.serDynPower = model["Pdyn"][serOPIndex]
        self.serStatPower = model["Pstat"][serOPIndex]
        self.paraDynPower = model["Pdyn"][paraOPIndex]
        self.paraStatPower = model["Pstat"][paraOPIndex]
        
        self.serV, self.serFreq = model["OP"][serOPIndex]
        self.paraV, self.paraFreq = model["OP"][paraOPIndex]
        
        self.cores = cores
        if self.cores == 1:
            self.serialFraction = 1.0
        else:
            self.serialFraction = serialFraction
        
        self.model = model
        
        self.period = 1.0
        self.maxInsts = model["OP"][-1][1] #Assuming one IPC, a period of 1s and that the OPs are sorted
        
        self.executionTime = 0
        self.serialExecTime = 0
    
    def estimateEnergy(self):
        
        assert self.serialExecTime != 0
        
        self.eDynSer = self.serialExecTime * self.serDynPower
        self.eDynPara = self.paraExecTime * self.paraDynPower * self.cores
        self.eDyn = self.eDynSer + self.eDynPara
        
        self.eStatSerial = self.serialExecTime * self.serStatPower
        self.eStatSleep = self.serialExecTime * self.model["Psleep"][0] * (self.cores - 1)
        self.eStatSerial += self.eStatSleep
        
        self.eStatPara = self.paraExecTime * self.paraStatPower * self.cores
        self.eStat = self.eStatSerial + self.eStatPara
        
        if self.feasible:
            self.eSlack = (self.period - self.executionTime) * self.cores * self.model["Psleep"][0]
        else:
            # Slack energy is 0 if there is no slack.
            self.eSlack = 0
        
        self.eTot = self.eDyn + self.eStat + self.eSlack
    
    def computeExecutionTime(self, utilization):
        insts = utilization * self.maxInsts

        self.serialExecTime = (insts * self.serialFraction) / self.serFreq
        self.paraExecTime = (insts* (1-self.serialFraction)) / (self.paraFreq * float(self.cores))
        self.executionTime = self.serialExecTime + self.paraExecTime
        
        if self.executionTime <= self.period:
            self.feasible = True
        else:
            self.feasible = False
        
class OperatingPointData:
    
    def __init__(self, model, cores, serialFraction, opts, singleFrequency=False):
        self.ops = []
        
        if singleFrequency:
            for i in range(len(model["OP"])):
                op = OperatingPoint(i, i, cores, serialFraction, model)
                op.computeExecutionTime(opts.utilization)
                op.estimateEnergy()
                self.ops.append(op)
        else:
            for s in range(len(model["OP"])):
                for p in range(len(model["OP"])):
                    op = OperatingPoint(s, p, cores, serialFraction, model)
                    op.computeExecutionTime(opts.utilization)
                    op.estimateEnergy()
                    self.ops.append(op)
        
        self.Edyn = []
        self.Estat = []
        self.Eslack = []
        self.Etot = []
        unitFactor = 10**6
        for op in self.ops:
            self.Edyn.append(op.eDyn*unitFactor)
            self.Estat.append(op.eStat*unitFactor)
            self.Eslack.append(op.eSlack*unitFactor)
            self.Etot.append((op.eTot)*unitFactor)
            
    def findMinEP(self):
        index = -1
        Emin = 10**10
        for i in range(len(self.Etot)):
            if self.Etot[i] < Emin and self.ops[i].feasible:
                Emin = self.Etot[i]
                index = i
                
        self.bestVoltage = self.ops[index].serV
        self.bestEnergy = Emin
        self.bestExecTime = self.ops[index].executionTime
                
        return index
    
    def getvRange(self):
        vRange = []
        for op in self.ops:
            vRange.append(op.serV)
        return vRange
        
def analyseCores(model, maxCores, opts):
    serialFractions = [0.05,0.1,0.25,0.5,0.75]
    cores = range(1,maxCores+1)
    minE = {}
    for s in serialFractions:
        minE[s] = []
        for c in cores:
            opd = OperatingPointData(model, c, s, opts)
            bestIndex = opd.findMinEP()
            minE[s].append(opd.Etot[bestIndex])
    
    data = []
    for s in serialFractions:
        norm = [e/minE[s][0] for e in minE[s]]
        data.append(norm)
    
    figTitle = ("Single core utilization %.1f" % (opts.utilization*100))+"\%"
    
    plotRawLinePlot(cores,
                    data,
                    titles=[str(s) for s in serialFractions],
                    legendColumns=len(serialFractions),
                    mode="None",
                    xlabel="Number of cores",
                    ylabel="Energy Normalized to Single Core",
                    yrange="0.0,1.2",
                    figtitle=figTitle,
                    filename=opts.outfile)

def analyseSingleCase(model, cores, serialFraction, opts):
    
    opd = OperatingPointData(model, cores, serialFraction, opts, True)
    
    if opts.verbose:
        printEnergyData(opd.getvRange(), [["Edyn"]+opd.Edyn, ["Estat"]+opd.Estat, ["Eslack"]+opd.Eslack, ["Etot"]+opd.Etot], opts)
    
    bestIndex = opd.findMinEP()
    
    if bestIndex == -1:
        print 
        print "Excecution time at maxiumum frequency ("+str(opd.bestExecTime)+"s) does not meet contraint "+str(model["PERIOD-TIME"])+"s"
        return
    
    if opts.verbose:
        print
        print "Optimal Voltage is "+str(opd.bestVoltage)+" with total energy "+str(opd.bestEnergy)+" uJ and execution time "+str(opd.bestExecTime)
    
    figTitle = "Utilization "+str(opts.utilization)+" with "+str(cores)+" cores and s="+str(serialFraction)
    opLabel = "Best Operating Point\nE = "+("%.2f uJ" % opd.bestEnergy)+("\nSlack %.3f s" % (1.0-opd.bestExecTime))
    
    plotRawLinePlot(opd.getvRange(),
                    [opd.Edyn, opd.Estat, opd.Eslack, opd.Etot],
                    titles=["Dynamic Energy Consumption","Static Energy Consumption", "Slack Energy Consumption", "Total Energy Consumption"],
                    legendColumns=4,
                    mode="None",
                    xlabel="$V_{dd}$",
                    ylabel="Energy (uJ)",
                    figtitle=figTitle,
                    separators=str(opd.bestVoltage),
                    labels=str(opd.bestVoltage*1.01)+","+str(opd.bestEnergy*1.2)+","+opLabel+",horizontal",
                    filename=opts.outfile)

def analyseFrequencies(model, cores, serialFraction, opts):
    opd = OperatingPointData(model, cores, serialFraction, opts)

    data = {}
    
    for op in opd.ops:
        if op.serV not in data:
            data[op.serV] = ([],[])
        data[op.serV][0].append(op.executionTime)
        data[op.serV][1].append(op.eTot * 10**6)
    
    execTimes = []
    energies = []
    legend = []
    for v in sorted(data.keys()):
        et, e = data[v]
        legend.append(str(v))
        execTimes.append(et)
        energies.append(e)
    
    maxE = max(max(energies))
    minE = min(min(energies))
    maxTime = max(max(execTimes))
    minTime = min(min(execTimes))
    
    xrangeSpec = "0,"+str(maxTime*1.25)
    if opts.scatterFeasible:
        xrangeSpec = "0,1.25"
    
    plotRawScatter(execTimes,
                   energies,
                   xlabel="Execution Time (s)",
                   ylabel="Energy (uJ)",
                   legend=legend,
                   legendColumns=12,
                   hseparators=str(minE),
                   vseparators=str(minTime)+",1.0",
                   xrange=xrangeSpec,
                   yrange="0,"+str(maxE*1.1),
                   title=str(cores)+"-core with s="+str(serialFraction)+" and utilization "+str(opts.utilization),
                   filename=opts.outfile)

METRIC_PERFORMANCE = "perf"
METRIC_ENERGY = "en"
METRIC_EDP = "edp"
METRIC_PERF_PER_WATT = "P/W"

METRIC_NAMES = {METRIC_PERFORMANCE: "Execution_Time", METRIC_ENERGY:"Energy", METRIC_EDP: "EDP", METRIC_PERF_PER_WATT: "Performance/Watt"}

def readDataFile(datafile):
    experimentSpec = {}
    f = open(datafile)
    for l in f:
        d = l.split("=")
        if d[0] == "CORES":
            experimentSpec["c"] = [int(v) for v in d[1].split(",")]
        elif d[0] == "SF":
            experimentSpec["s"] = [float(v) for v in d[1].split(",")]
        elif d[0] == "INTENSITY":
            experimentSpec["i"] = [float(v) for v in d[1].split(",")]
        elif d[0] == "HETEROGENEOUS":
            assert d[1].strip() == "Both"
            experimentSpec["h"] = False
        elif d[0] == "METRIC":
            if d[1].strip() == "Performance":
                experimentSpec["m"] = METRIC_PERFORMANCE
            elif d[1].strip() == "Energy":
                experimentSpec["m"] = METRIC_ENERGY
            elif d[1].strip() == "EDP":
                experimentSpec["m"] = METRIC_EDP
            elif d[1].strip() == "P/W":
                experimentSpec["m"] = METRIC_PERF_PER_WATT
            else:
                fatal("Datafile: Unknown metric "+d[1])
        else:
            fatal("Datafile parse error: "+l)

    if "h" not in experimentSpec:
        experimentSpec["h"] = True
    return experimentSpec

def getHeader(dataColNames):
    lines = []
    header = [""]
    justify = [True]
    for v in dataColNames:
        header.append(str(v))
        justify.append(False)
    lines.append(header)
    return lines, justify

def opToStr(v,f):
    return "%.1f_MHz" % (f/10**6)

def computeEDP(energy, execTime):
    return (energy*execTime)

def computePerfPerWatt(energy, execTime):
    avgWatt = energy/execTime
    perf = 1.0/execTime
    #In this case, Performance/Watt is actually 1/Energy
    return perf/avgWatt

def computeMetric(metric, op):
    if metric == METRIC_PERFORMANCE:
        return op.executionTime # seconds
    elif metric == METRIC_ENERGY:
        return op.eTot * 10**3 # mJ
    elif metric == METRIC_EDP:
        return computeEDP(op.eTot, op.executionTime)
    elif metric == METRIC_PERF_PER_WATT:
        return computePerfPerWatt(op.eTot, op.executionTime)
    fatal("metric not implemented")
    return None

def getOutfile(opts):
    if opts.outfile == None:
        return sys.stdout
    return open(opts.outfile, "w")

def getPercString(v):
    return str(int(v*100))+"\%"

def getPercStrings(values):
    return [getPercString(v) for v in values]

def printCoresVsOp(model, cores, s, metric, h, opts):
    lines, justify = getHeader(opToStr(v, f) for v,f in model["OP"])
    for c in cores:
        line = [str(c)]
        opd = OperatingPointData(model, c, s, opts, h)
        for op in opd.ops:
            line.append(numberToString(computeMetric(metric, op), opts.decimals))
        lines.append(line)
    
    printData(lines, justify, getOutfile(opts), opts.decimals)
    
def printCoresVsS(model, cores, serialFractions, metric, h, opts):
    lines, justify = getHeader(getPercStrings(serialFractions))
    for c in cores:
        line = [str(c)]
        for s in serialFractions:
            opd = OperatingPointData(model, c, s, opts, h)
            minEP = opd.findMinEP()
            op = opd.ops[minEP]
            line.append(numberToString(computeMetric(metric, op), opts.decimals))
        lines.append(line)
    
    printData(lines, justify, getOutfile(opts), opts.decimals)

def printSfVsCompInt(model, c, sfs, metric, compInt, h, opts):
    
    if len(sfs) == 1:
        lines, justify = getHeader([METRIC_NAMES[metric]])
    else:
        lines, justify = getHeader(getPercStrings(sfs))
    for i in range(len(compInt)):
        line = [str(compInt[i])]
        opts.utilization = compInt[i]
        for s in sfs:
            opd = OperatingPointData(model, c, s, opts, h)
            minEP = opd.findMinEP()
            op = opd.ops[minEP]
            if op.feasible:
                line.append(numberToString(computeMetric(metric, op), opts.decimals))
            else:
                line.append("NoData")
        lines.append(line)
    
    printData(lines, justify, getOutfile(opts), opts.decimals)
    
def printSfVsHeterogeneous(model, c, sfs, metric, opts):
    
    lines, justify = getHeader(["Single_OP", "Different_OPs"])
    for s in sfs:
        line = [getPercString(s)]
        for h in (True, False):
            opd = OperatingPointData(model, c, s, opts, h)
            minEP = opd.findMinEP()
            op = opd.ops[minEP]
            line.append(numberToString(computeMetric(metric, op), opts.decimals))
        lines.append(line)
    
    printData(lines, justify, getOutfile(opts), opts.decimals)
    
def coresToHeading(cores):
    out = []
    for c in cores:
        if c == 1:
            out.append("Single-core")
        else:
            out.append(str(c)+"-core")
    return out
def printCoresVsCompInt(model, cores, s, metric, compInt, h, opts):
    
    if metric == METRIC_PERF_PER_WATT: #Higher is better metrics
        opts.utilization = min(compInt)
    else: # Lower is better metrics
        opts.utilization = 1.0
        
    opd = OperatingPointData(model, 1, s, opts, h)
    minEP = opd.findMinEP()
    op = opd.ops[minEP]
    maxMetricVal = computeMetric(metric, op)        
    
    lines, justify = getHeader(coresToHeading(cores))
    for i in range(len(compInt)):
        line = [str(compInt[i])]
        opts.utilization = compInt[i]
        for c in cores:
            opd = OperatingPointData(model, c, s, opts, h)
            minEP = opd.findMinEP()
            op = opd.ops[minEP]
            
            if op.feasible:
                metricVal = computeMetric(metric, op) 
                relVal = metricVal / maxMetricVal 
                line.append(numberToString(relVal, opts.decimals))
            else:
                line.append("NoData")
        lines.append(line)
    
    printData(lines, justify, getOutfile(opts), opts.decimals)

def createDatafile(model, opts):
    spec = readDataFile(opts.datafile)
    
    if not spec["h"]:
        printSfVsHeterogeneous(model, spec["c"][0], spec["s"], spec["m"], opts)
        return
    
    if "i" in spec and len(spec["s"]) > 1:
        printSfVsCompInt(model, spec["c"][0], spec["s"], spec["m"], spec["i"], spec["h"], opts)
        return
    
    if "i" in spec:
        printCoresVsCompInt(model, spec["c"], spec["s"][0], spec["m"], spec["i"], spec["h"], opts)
        return
    
    if len(spec["s"]) == 1:
        printCoresVsOp(model, spec["c"], spec["s"][0], spec["m"], spec["h"], opts)
        return

    printCoresVsS(model, spec["c"], spec["s"], spec["m"], spec["h"], opts)
    
def main():
    args, opts = parseArgs()
    model = readModelFile(args[0])
    cores = int(args[1])
    serialFraction = float(args[2])
    
    if opts.test:
        test(model)
        return
    
    if opts.analyseCores:
        analyseCores(model, cores, opts)
        return
    
    if opts.singleScatter:
        analyseFrequencies(model, cores, serialFraction, opts)
        return
    
    if opts.datafile != "":
        createDatafile(model, opts)
        return
    
    analyseSingleCase(model, cores, serialFraction, opts)

def checkAssertions(op1, v, decimals):
    decimals = str(decimals)
    assert ("%."+decimals+"f") % op1.eDynSer == v["eDynSer"], "Unexpeced EdynSer "+(("%."+decimals+"f") % op1.eDynSer)
    assert ("%."+decimals+"f") % op1.eDynPara == v["eDynPara"], "Unexpeced EdynPara "+(("%."+decimals+"f") % op1.eDynPara)
    assert ("%."+decimals+"f") % op1.eDyn == v["eDyn"], "Unexpeced Edyn "+(("%."+decimals+"f") % op1.eDyn)
    assert ("%."+decimals+"f") % op1.eStatSleep == v["eStatSleep"], "Unexpeced EstatSleep "+(("%."+decimals+"f") % op1.eStatSleep)
    assert ("%."+decimals+"f") % op1.eStatSerial == v["eStatSerial"], "Unexpeced EstatSerial "+(("%."+decimals+"f") % op1.eStatSerial)
    assert ("%."+decimals+"f") % op1.eStatPara == v["eStatPara"], "Unexpeced EstatPara "+(("%."+decimals+"f") % op1.eStatPara)
    assert ("%."+decimals+"f") % op1.eSlack == v["eSlack"], "Unexpeced Eslack "+(("%."+decimals+"f") % op1.eSlack)
    assert ("%."+decimals+"f") % op1.eTot == v["eTot"], "Unexpeced Etot "+(("%."+decimals+"f") % op1.eTot)

def test(model):

    print "Test 1: Single core with utilization 10% @ 1.0V"
    op1 = OperatingPoint(6, 6, 1, 1.0, model)
    op1.computeExecutionTime(0.1)
    op1.estimateEnergy()
    values = {"eDynSer": "0.000041", "eDynPara": "0.000000","eDyn": "0.000041", "eStatSerial": "0.000000", "eStatPara": "0.000000", "eTot": "0.000042", "eSlack": "0.000000", "eStatSleep": "0.000000"}
    checkAssertions(op1, values, 6)
    print "Test passed!"
    
    print "Test 2: 4-core with utilization 50% @ 1.3V and serial fraction 0.25"
    op1 = OperatingPoint(12, 12, 4, 0.25, model)
    op1.computeExecutionTime(0.5)
    op1.estimateEnergy()
    values = {"eDynSer": "0.000087", "eDynPara": "0.000261", "eDyn": "0.000347", "eStatSerial": "0.000001", "eStatPara": "0.000002", "eTot": "0.000352", "eSlack": "0.000002", "eStatSleep": "0.000000"}
    checkAssertions(op1, values, 6)
    print "Test passed!"
    
    print "Test 3: 4-core with serial @ 2V and para @ 1V, utilization 50% and serial fraction 0.1"
    op1 = OperatingPoint(12, 6, 4, 0.1, model)
    op1.computeExecutionTime(0.5)
    op1.estimateEnergy()
    values = {"eDynSer": "0.000035", "eDynPara": "0.000185", "eDyn": "0.000220", "eStatSerial": "0.000000", "eStatPara": "0.000001", "eTot": "0.000223", "eSlack": "0.000002", "eStatSleep": "0.000000"}
    checkAssertions(op1, values, 6)
    print "Test passed!"
    

if __name__ == '__main__':
    main()