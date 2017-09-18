#!/usr/bin/env python

import sys
from optparse import OptionParser
from sag import fatal

from statparse.plotResults import plotRawLinePlot, plotRawScatter
from statparse.printResults import printData, numberToString

def parseArgs():
    parser = OptionParser(usage="evaluatePeriodicApplication.py [options] model-file cores serial-fraction")

    parser.add_option("--verbose", action="store_true", dest="verbose", default=False, help="Enable verbose output")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--instructions", action="store", dest="insts", type="int", default=15, help="Number of million instructions in program")
    parser.add_option("--outfile", action="store", dest="outfile", type="string", default=None, help="Filename of the plot file")
    parser.add_option("--analyse-cores", action="store_true", dest="analyseCores", default=False, help="Find the minium energy points for each core configuration")
    parser.add_option("--single-scatter", action="store_true", dest="singleScatter", default=False, help="Analyse a single architecture with all frequency pairs")
    parser.add_option("--scatter-feasible", action="store_true", dest="scatterFeasible", default=False, help="Zoom scatter on the feasible points")
    parser.add_option("--test", action="store_true", dest="test", default=False, help="Run regression test suite")
    
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
                value = float(eval(data[1][1:]))
            else:
                assert data[1][0] == "v"
                value = [float(eval(v)) for v in data[1][1:].split(";")]
        except:
            fatal("Cannot parse model config line:\n"+str(l))
        
        assert key not in model
        model[key] = value
    
    assert len(model["f"]) == len(model["V"])
    operatingPoints = []
    for i in range(len(model["f"])):
        operatingPoints.append( (model["V"][i], model["f"][i]) )
        
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

def getInsts(opts):
    return opts.insts * 10**6

class VoltagePoint:
    
    def __init__(self, v, f):
        self.v = v
        self.f = f

class OperatingPoint:
    
    def __init__(self, serVP, paraVP, cores, serialFraction, opts, model):
        self.serVP = serVP
        self.paraVP = paraVP
        self.cores = cores
        if self.cores == 1:
            self.serialFraction = 1.0
        else:
            self.serialFraction = serialFraction
        self.opts = opts
        self.model = model
    
    def estimateEnergy(self):
        
        self.eDynSer = self.serialFraction*self.model["ALPHA-D"]*getInsts(self.opts)*self.serVP.v**2
        self.eDynPara = (1-self.serialFraction)*self.model["ALPHA-D"]*getInsts(self.opts)*self.paraVP.v**2
        self.eDyn = self.eDynSer + self.eDynPara
        
        eStatConstSerial = (self.model["ALPHA-S"]*self.serVP.v)/float(self.serVP.f)
        self.eStatSerial = getInsts(self.opts)*self.serialFraction*eStatConstSerial
        
        eStatConstPara = (self.model["ALPHA-S"]*self.paraVP.v)/float(self.paraVP.f)
        self.eStatPara = getInsts(self.opts)*(1-self.serialFraction)*eStatConstPara
        self.eStat = self.eStatSerial + self.eStatPara
           
        self.eTot = self.eDyn + self.eStat
    
    def computeExecutionTime(self):
        self.executionTime = (getInsts(self.opts) * self.serialFraction) / self.serVP.f
        self.executionTime += (getInsts(self.opts)* (1-self.serialFraction)) / (self.paraVP.f * float(self.cores))
        if self.executionTime <= self.model["PERIOD-TIME"]:
            self.feasible = True
        else:
            self.feasible = False
        
class OperatingPointData:
    
    def __init__(self, model, cores, serialFraction, opts, singleFrequency=False):
        self.ops = []
        
        if singleFrequency:
            for v,f in model["OP"]:
                op = OperatingPoint(VoltagePoint(v, f), VoltagePoint(v, f), cores, serialFraction, opts, model)
                op.estimateEnergy()
                op.computeExecutionTime()
                self.ops.append(op)
        else:
            for sv,sf in model["OP"]:
                for pv,pf in model["OP"]:
                    op = OperatingPoint(VoltagePoint(sv, sf), VoltagePoint(pv, pf), cores, serialFraction, opts, model)
                    op.estimateEnergy()
                    op.computeExecutionTime()
                    self.ops.append(op)
        
        self.Edyn = []
        self.Estat = []
        self.Etot = []
        unitFactor = 10**6
        for op in self.ops:
            self.Edyn.append(op.eDyn*unitFactor)
            self.Estat.append(op.eStat*unitFactor)
            self.Etot.append((op.eTot)*unitFactor)
            
    def findMinEP(self):
        index = -1
        Emin = 10**10
        for i in range(len(self.Etot)):
            if self.Etot[i] < Emin and self.ops[i].feasible:
                Emin = self.Etot[i]
                index = i
                
        self.bestVoltage = self.ops[index].serVP.v
        self.bestEnergy = Emin
        self.bestExecTime = self.ops[index].executionTime
                
        return index
    
    def getvRange(self):
        vRange = []
        for op in self.ops:
            vRange.append(op.serVP.v)
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
    
    figTitle = "Period "+str(model["PERIOD-TIME"])+"s and "+str(getInsts(opts)/10**6)+" million instructions"
    
    plotRawLinePlot(cores,
                    data,
                    titles=[str(s) for s in serialFractions],
                    legendColumns=len(serialFractions),
                    mode="None",
                    xlabel="Number of cores",
                    ylabel="Energy Normalized to Single Core",
                    yrange="0.6,1.2",
                    figtitle=figTitle,
                    filename=opts.outfile)

def analyseSingleCase(model, cores, serialFraction, opts):
    
    opd = OperatingPointData(model, cores, serialFraction, opts, True)
    
    if opts.verbose:
        printEnergyData(opd.getvRange(), [["Edyn"]+opd.Edyn, ["Estat"]+opd.Estat, ["Etot"]+opd.Etot], opts)
    
    bestIndex = opd.findMinEP()
    
    if bestIndex == -1:
        print 
        print "Excecution time at maxiumum frequency ("+str(opd.bestExecTime)+"s) does not meet contraint "+str(model["PERIOD-TIME"])+"s"
        return
    
    if opts.verbose:
        print
        print "Optimal Voltage is "+str(opd.bestVoltage)+" with total energy "+str(opd.bestEnergy)+" uJ and execution time "+str(opd.bestExecTime)
    
    figTitle = "Period "+str(model["PERIOD-TIME"])+"s and "+str(getInsts(opts)/10**6)+" million instructions with "+str(cores)+" cores and s="+str(serialFraction)
    opLabel = "Best Operating Point\nE = "+("%.2f uJ" % opd.bestEnergy)+("\nSlack %.3f s" % (model["PERIOD-TIME"]-opd.bestExecTime))
    
    plotRawLinePlot(opd.getvRange(),
                    [opd.Edyn, opd.Estat, opd.Etot],
                    titles=["Dynamic Energy Consumption","Static Energy Consumption", "Total Energy Consumption"],
                    legendColumns=3,
                    mode="None",
                    xlabel="$V_{dd}$",
                    ylabel="Energy (uJ)",
                    figtitle=figTitle,
                    separators=str(opd.bestVoltage),
                    labels=str(opd.bestVoltage*1.01)+","+str(opd.bestEnergy*1.2)+","+opLabel,
                    filename=opts.outfile)

def analyseFrequencies(model, cores, serialFraction, opts):
    opd = OperatingPointData(model, cores, serialFraction, opts)

    data = {}
    
    for op in opd.ops:
        if op.serVP.v not in data:
            data[op.serVP.v] = ([],[])
        data[op.serVP.v][0].append(op.executionTime)
        data[op.serVP.v][1].append(op.eTot * 10**6)
    
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
        xrangeSpec = "0,"+str(model["PERIOD-TIME"]*1.25)
    
    plotRawScatter(execTimes,
                   energies,
                   xlabel="Execution Time (s)",
                   ylabel="Energy (uJ)",
                   legend=legend,
                   hseparators=str(minE),
                   vseparators=str(minTime)+","+str(model["PERIOD-TIME"]),
                   xrange=xrangeSpec,
                   yrange="0,"+str(maxE*1.1),
                   title=str(cores)+"-core with s="+str(serialFraction)+", "+str(opts.insts)+" million instructions and period "+str(model["PERIOD-TIME"])+"s",
                   filename=opts.outfile)
    

def main():
    args, opts = parseArgs()
    model = readModelFile(args[0])
    cores = int(args[1])
    serialFraction = float(args[2])
    
    if opts.test:
        test(model, opts)
        return
    
    if opts.analyseCores:
        analyseCores(model, cores, opts)
        return
    
    if opts.singleScatter:
        analyseFrequencies(model, cores, serialFraction, opts)
        return
    
    analyseSingleCase(model, cores, serialFraction, opts)

def checkAssertions(op1, v):
    assert "%.6f" % op1.eDynSer == v["eDynSer"], "Unexpeced EdynSer "+("%.6f" % op1.eDynSer)
    assert "%.6f" % op1.eDynPara == v["eDynPara"], "Unexpeced EdynPara "+("%.6f" % op1.eDynPara)
    assert "%.6f" % op1.eDyn == v["eDyn"], "Unexpeced Edyn "+("%.6f" % op1.eDyn)
    assert "%.6f" % op1.eStatSerial == v["eStatSerial"], "Unexpeced EstatSerial "+("%.6f" % op1.eStatSerial)
    assert "%.6f" % op1.eStatPara == v["eStatPara"], "Unexpeced EstatPara "+("%.6f" % op1.eStatPara)
    assert "%.6f" % op1.eTot == v["eTot"], "Unexpeced Etot "+("%.6f" % op1.eTot)

def test(model, opts):
    assert opts.insts == 15, "Must use default instruction count for the tests to work"
    
    print "Test 1: Single core with single voltage point"
    vp = VoltagePoint(0.55, 2.88*10**6)
    op1 = OperatingPoint(vp, vp, 1, 1.0, opts, model)
    op1.estimateEnergy()
    op1.computeExecutionTime()
    values = {"eDynSer": "0.000163", "eDynPara": "0.000000","eDyn": "0.000163", "eStatSerial": "0.001358", "eStatPara": "0.000000", "eTot": "0.001521" }
    checkAssertions(op1, values)
    print "Test passed!"
    
    print "Test 2: 4-core with single voltage point and serial fraction 0.25"
    vp = VoltagePoint(0.874, 92.16*10**6)
    op1 = OperatingPoint(vp, vp, 4, 0.25, opts, model)
    op1.estimateEnergy()
    op1.computeExecutionTime()
    values = {"eDynSer": "0.000103", "eDynPara": "0.000309", "eDyn": "0.000413", "eStatSerial": "0.000017", "eStatPara": "0.000051", "eTot": "0.000480" }
    checkAssertions(op1, values)
    print "Test passed!"
    
    print "Test 3: 4-core with two voltage point and serial fraction 0.1"
    vpSer = VoltagePoint(1.054, 184.32*10**6)
    vpPara = VoltagePoint(0.760, 46.08*10**6)
    op1 = OperatingPoint(vpSer, vpPara, 4, 0.1, opts, model)
    op1.estimateEnergy()
    op1.computeExecutionTime()
    values = {"eDynSer": "0.000060", "eDynPara": "0.000281", "eDyn": "0.000341", "eStatSerial": "0.000004", "eStatPara": "0.000106", "eTot": "0.000450" }
    checkAssertions(op1, values)
    print "Test passed!"
    

if __name__ == '__main__':
    main()