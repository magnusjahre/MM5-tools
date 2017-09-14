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
    parser.add_option("--outfile", action="store", dest="outfile", type="string", default=None, help="Filename of the plot file")
    parser.add_option("--analyse-cores", action="store_true", dest="analyseCores", default=False, help="Find the minium energy points for each core configuration")
    parser.add_option("--single-scatter", action="store_true", dest="singleScatter", default=False, help="Analyse a single architecture with all frequency pairs")
    
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

class VoltagePoint:
    
    def __init__(self, v, f):
        self.v = v
        self.f = f

class OperatingPoint:
    
    def __init__(self, serVP, paraVP, cores, serialFraction, opts, model):
        self.serVP = serVP
        self.paraVP = paraVP
        self.cores = cores
        self.serialFraction = serialFraction
        self.opts = opts
        self.model = model
    
    def estimateEnergy(self):
        self.eDyn = self.model["ALPHA-D"]*self.model["PERIOD-INSTRUCTIONS"]*self.paraVP.v**2
        if self.opts.verbose:
            print "alpha-d="+str(self.model["ALPHA-D"])+", instructions="+str(self.model["PERIOD-INSTRUCTIONS"])+", voltage="+str(self.paraVP.v)+" gives Pd="+str(self.eDyn)
        
        eStatConst = (self.model["ALPHA-S"]*self.serVP.v)/float(self.serVP.f)
        
        self.eStatSerial = self.model["PERIOD-INSTRUCTIONS"]*self.serialFraction*eStatConst
        self.eStatPara = self.model["PERIOD-INSTRUCTIONS"]*(1-self.serialFraction)*eStatConst*float(self.cores)
        
        if self.opts.verbose:
            print "alpha-s="+str(self.model["ALPHA-S"])+", I="+str(self.model["PERIOD-INSTRUCTIONS"])+", f="+str(self.serVP.f)+" gives static energy constant "+str(eStatConst)
            
        self.eTot = self.eDyn + self.eStatSerial + self.eStatPara
    
    def computeExecutionTime(self):
        self.executionTime = (self.model["PERIOD-INSTRUCTIONS"] * self.serialFraction) / self.serVP.f
        self.executionTime += (self.model["PERIOD-INSTRUCTIONS"]* (1-self.serialFraction)) / (self.paraVP.f * float(self.cores))
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
        self.EstatSer = []
        self.EstatPar = []
        self.Etot = []
        unitFactor = 10**6
        for op in self.ops:
            self.Edyn.append(op.eDyn*unitFactor)
            self.EstatSer.append(op.eStatSerial*unitFactor)
            self.EstatPar.append(op.eStatPara*unitFactor)
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
    serialFractions = [0.25,0.5,0.75]
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
    
    figTitle = "Period "+str(model["PERIOD-TIME"])+"s and "+str(model["PERIOD-INSTRUCTIONS"]/10**6)+" million instructions"
    
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
    
    printEnergyData(opd.getvRange(), [["Edyn"]+opd.Edyn, ["EstatSer"]+opd.EstatSer, ["EstatPar"]+opd.EstatPar, ["Etot"]+opd.Etot], opts)
    
    bestIndex = opd.findMinEP()
    
    if bestIndex == -1:
        print 
        print "Excecution time at maxiumum frequency ("+str(opd.execTimes[-1])+"s) does not meet contraint "+str(model["PERIOD-TIME"])+"s"
        return
    
    print
    print "Optimal Voltage is "+str(opd.bestVoltage)+" with total energy "+str(opd.bestEnergy)+" uJ and execution time "+str(opd.bestExecTime)
    
    figTitle = "Period "+str(model["PERIOD-TIME"])+"s and "+str(model["PERIOD-INSTRUCTIONS"]/10**6)+" million instructions with "+str(cores)+" cores and s="+str(serialFraction)
    opLabel = "Best Operating Point\nE = "+("%.2f uJ" % opd.bestEnergy)+("\nSlack %.3f s" % (model["PERIOD-TIME"]-opd.bestExecTime))
    
    plotRawLinePlot(opd.getvRange(),
                    [opd.Edyn, opd.EstatSer, opd.EstatPar, opd.Etot],
                    titles=["E-dynamic","E-static-serial-section","E-static-parallel-section", "E-total"],
                    legendColumns=4,
                    mode="None",
                    xlabel="$V_{dd}$",
                    ylabel="uJ",
                    figtitle=figTitle,
                    separators=str(opd.bestVoltage),
                    labels=str(opd.bestVoltage*1.01)+","+str(opd.bestEnergy*1.2)+","+opLabel,
                    filename=opts.outfile)

def analyseFrequencies(model, cores, serialFraction, opts):
    opd = OperatingPointData(model, cores, serialFraction, opts)
    
    execTimes = []
    energies = []
    
    for op in opd.ops:
        execTimes.append(op.executionTime)
        energies.append(op.eTot)
        
    plotRawScatter(execTimes, energies)
    

def main():
    args, opts = parseArgs()
    model = readModelFile(args[0])
    cores = int(args[1])
    serialFraction = float(args[2])
    
    if opts.analyseCores:
        analyseCores(model, cores, opts)
        return
    
    if opts.singleScatter:
        analyseFrequencies(model, cores, serialFraction, opts)
        return
    
    analyseSingleCase(model, cores, serialFraction, opts)
    

if __name__ == '__main__':
    main()