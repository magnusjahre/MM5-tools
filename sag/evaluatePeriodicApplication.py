#!/usr/bin/env python

import sys
from optparse import OptionParser
from sag import fatal

from statparse.plotResults import plotRawLinePlot
from statparse.printResults import printData, numberToString

def parseArgs():
    parser = OptionParser(usage="evaluatePeriodicApplication.py [options] model-file cores serial-fraction")

    parser.add_option("--verbose", action="store_true", dest="verbose", default=False, help="Enable verbose output")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--outfile", action="store", dest="outfile", type="string", default=None, help="Filename of the plot file")
    parser.add_option("--analyse-cores", action="store_true", dest="analyseCores", default=False, help="Find the minium energy points for each core configuration")
    
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

def estimateEnergy(op, model, opts):
    
    eDyn = model["ALPHA-D"]*model["PERIOD-INSTRUCTIONS"]*op.v**2
    if opts.verbose:
        print "alpha-d="+str(model["ALPHA-D"])+", instructions="+str(model["PERIOD-INSTRUCTIONS"])+", voltage="+str(op.v)+" gives Pd="+str(eDyn)
    
    eStatConst = (model["ALPHA-S"]*op.v)/float(op.f)
    
    eStatSerial = model["PERIOD-INSTRUCTIONS"]*op.serialFraction*eStatConst
    eStatPara = model["PERIOD-INSTRUCTIONS"]*(1-op.serialFraction)*eStatConst*float(op.cores)
    
    if opts.verbose:
        print "alpha-s="+str(model["ALPHA-S"])+", I="+str(model["PERIOD-INSTRUCTIONS"])+", f="+str(op.f)+" gives static energy constant "+str(eStatConst)
    
    return eDyn, eStatSerial, eStatPara

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

def findMinEP(Etot, feasible):
    index = -1
    Emin = 10**10
    for i in range(len(Etot)):
        if Etot[i] < Emin and feasible[i]:
            Emin = Etot[i]
            index = i
    return index

def isFeasible(et, model):
    if et <= model["PERIOD-TIME"]:
        return True
    return False

def getExecutionTime(model, op):
    p = 1-op.serialFraction
    t = (model["PERIOD-INSTRUCTIONS"] * (op.serialFraction + (p/float(op.cores)))) / op.f
    return t

class OperatingPoint:
    
    def __init__(self, v, f, cores, serialFraction):
        self.v = v
        self.f = f
        self.cores = cores
        self.serialFraction = serialFraction
        

class OperatingPointData:
    
    def __init__(self, model, cores, serialFraction, opts):
        self.vRange = []
        self.energy = []
        self.execTimes = []
        self.feasible = []
        for v,f in model["OP"]:
            op = OperatingPoint(v, f, cores, serialFraction)
            self.vRange.append(v)
            self.energy.append(estimateEnergy(op, model, opts))
            et = getExecutionTime(model, op)
            self.execTimes.append(et)
            self.feasible.append(isFeasible(et, model))
        
        self.Edyn = []
        self.EstatSer = []
        self.EstatPar = []
        self.Etot = []
        unitFactor = 10**6
        for d,ss,sp in self.energy:
            self.Edyn.append(d*unitFactor)
            self.EstatSer.append(ss*unitFactor)
            self.EstatPar.append(sp*unitFactor)
            self.Etot.append((d+ss+sp)*unitFactor)
        
def analyseCores(model, maxCores, opts):
    serialFractions = [0.25,0.5,0.75]
    cores = range(1,maxCores+1)
    minE = {}
    for s in serialFractions:
        minE[s] = []
        for c in cores:
            opd = OperatingPointData(model, c, s, opts)
            bestIndex = findMinEP(opd.Etot, opd.feasible)
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
    
    opd = OperatingPointData(model, cores, serialFraction, opts)
    
    printEnergyData(opd.vRange, [["Edyn"]+opd.Edyn, ["EstatSer"]+opd.EstatSer, ["EstatPar"]+opd.EstatPar, ["Etot"]+opd.Etot], opts)
    
    bestIndex = findMinEP(opd.Etot, opd.feasible)
    
    if bestIndex == -1:
        print 
        print "Excecution time at maxiumum frequency ("+str(opd.execTimes[-1])+"s) does not meet contraint "+str(model["PERIOD-TIME"])+"s"
        return
    
    print
    print "Optimal Voltage is "+str(opd.vRange[bestIndex])+" with total energy "+str(opd.Etot[bestIndex])+" uJ and execution time "+str(opd.execTimes[bestIndex])
    
    figTitle = "Period "+str(model["PERIOD-TIME"])+"s and "+str(model["PERIOD-INSTRUCTIONS"]/10**6)+" million instructions with "+str(cores)+" cores and s="+str(serialFraction)
    opLabel = "Best Operating Point\nE = "+("%.2f uJ" % opd.Etot[bestIndex])+("\nSlack %.3f s" % (model["PERIOD-TIME"]-opd.execTimes[bestIndex]))
    
    plotRawLinePlot(opd.vRange,
                    [opd.Edyn, opd.EstatSer, opd.EstatPar, opd.Etot],
                    titles=["E-dynamic","E-static-serial-section","E-static-parallel-section", "E-total"],
                    legendColumns=4,
                    mode="None",
                    xlabel="$V_{dd}$",
                    ylabel="uJ",
                    figtitle=figTitle,
                    separators=str(opd.vRange[bestIndex]),
                    labels=str(opd.vRange[bestIndex]*1.01)+","+str(opd.Etot[bestIndex]*1.2)+","+opLabel,
                    filename=opts.outfile)

def main():
    args, opts = parseArgs()
    model = readModelFile(args[0])
    cores = int(args[1])
    serialFraction = float(args[2])
    
    if opts.analyseCores:
        analyseCores(model, cores, opts)
        return
    analyseSingleCase(model, cores, serialFraction, opts)
    

if __name__ == '__main__':
    main()