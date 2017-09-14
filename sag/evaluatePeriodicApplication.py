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

def estimateEnergy(voltage, frequency, cores, serialFraction, model, opts):
    
    eDyn = model["ALPHA-D"]*model["PERIOD-INSTRUCTIONS"]*voltage**2
    if opts.verbose:
        print "alpha-d="+str(model["ALPHA-D"])+", instructions="+str(model["PERIOD-INSTRUCTIONS"])+", voltage="+str(voltage)+" gives Pd="+str(eDyn)
    
    eStatConst = (model["ALPHA-S"]*voltage)/float(frequency)
    
    eStatSerial = model["PERIOD-INSTRUCTIONS"]*serialFraction*eStatConst
    eStatPara = model["PERIOD-INSTRUCTIONS"]*(1-serialFraction)*eStatConst*float(cores)
    
    if opts.verbose:
        print "alpha-s="+str(model["ALPHA-S"])+", I="+str(model["PERIOD-INSTRUCTIONS"])+", f="+str(frequency)+" gives static energy constant "+str(eStatConst)
    
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

def findMinEP(vRange, Etot):
    Emin = Etot[0]
    Vopt = vRange[0]
    for i in range(len(Etot))[1:]:
        if Etot[i] < Emin:
            Emin = Etot[i]
            Vopt = vRange[i]
    
    return Emin,Vopt

def getExecutionTime(model, Vopt, cores, serialFraction):
    useFreq = 0.0
    for v,f in model["OP"]:
        if v == Vopt:
            assert useFreq == 0.0
            useFreq = f
    assert useFreq != 0.0
    
    p = 1-serialFraction
    t = (model["PERIOD-INSTRUCTIONS"] * (serialFraction + (p/float(cores)))) / useFreq
    
    if t <= model["PERIOD-TIME"]:
        print "Execution time "+str(t)+" s at optimal voltage is feasible within period "+str(model["PERIOD-TIME"])
    else:
        print "Execution time "+str(t)+" s at optimal voltage is _not_ feasible within period "+str(model["PERIOD-TIME"])
    
    return t

def main():
    args, opts = parseArgs()
    model = readModelFile(args[0])
    cores = int(args[1])
    serialFraction = float(args[2])
    
    vRange = []
    energy = []
    for v,f in model["OP"]:
        vRange.append(v)
        energy.append(estimateEnergy(v, f, cores, serialFraction, model, opts))
    
    Edyn = []
    EstatSer = []
    EstatPar = []
    Etot = []
    unitFactor = 10**6
    for d,ss,sp in energy:
        Edyn.append(d*unitFactor)
        EstatSer.append(ss*unitFactor)
        EstatPar.append(sp*unitFactor)
        Etot.append((d+ss+sp)*unitFactor)
    
    printEnergyData(vRange, [["Edyn"]+Edyn, ["EstatSer"]+EstatSer, ["EstatPar"]+EstatPar, ["Etot"]+Etot], opts)
    
    Emin, Vopt = findMinEP(vRange, Etot)
    print
    print "Optimal Voltage is "+str(Vopt)+" with total energy "+str(Emin)+" uJ and execution time "+str(getExecutionTime(model, Vopt, cores, serialFraction))
    
    plotRawLinePlot(vRange,
                    [Edyn, EstatSer, EstatPar, Etot],
                    titles=["E-dynamic","E-static-serial-section","E-static-parallel-section", "E-total"],
                    legendColumns=4,
                    mode="None",
                    xlabel="$V_{dd}$",
                    ylabel="uJ",
                    separators=str(Vopt),
                    labels=str(Vopt*1.01)+","+str(Emin*1.2)+",Optimal Voltage",
                    filename=opts.outfile)

if __name__ == '__main__':
    main()