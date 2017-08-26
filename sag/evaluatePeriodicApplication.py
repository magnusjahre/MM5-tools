#!/usr/bin/env python

import sys
from optparse import OptionParser
from sag import fatal

from statparse.plotResults import plotRawLinePlot

def parseArgs():
    parser = OptionParser(usage="evaluatePeriodicApplication.py [options] model-file")

    parser.add_option("--verbose", action="store_true", dest="verbose", default=False, help="Enable verbose output")
    
    opts, args = parser.parse_args()

    if len(args) != 1:
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
    
    print model
    return model

def estimateEnergy(voltage, frequency, model, opts):
    
    pDyn = model["ALPHA-D"]*frequency*voltage**2
    pStat = model["ALPHA-S"]*voltage
    
    if opts.verbose:
        print "v="+str(voltage)+", f="+str(frequency)+" gives Pd="+str(pDyn)+" and Ps="+str(pStat)
    
    # Assuming a one-IPC performance model
    clockPeriod = 1.0/float(frequency)
    runtime = model["PERIOD-INSTRUCTIONS"] * clockPeriod
    
    eTot = pDyn*runtime + pStat*runtime
    
    if opts.verbose:
        print "clockPeriod="+str(clockPeriod)+" gives runtime="+str(runtime)+" and Etot="+str(eTot)
    
    return eTot

def main():
    args, opts = parseArgs()
    model = readModelFile(args[0])
    
    vRange = []
    energy = []
    for v,f in model["OP"]:
        vRange.append(v)
        energy.append(estimateEnergy(v, f, model, opts))
    
    print vRange
    print energy
    
    plotRawLinePlot(vRange, [energy])

if __name__ == '__main__':
    main()