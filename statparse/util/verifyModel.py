#!/usr/bin/env python
import sys
import os
import shutil

from optparse import OptionParser
from m5test.M5Command import M5Command
from util.inifile import IniFile
from statparse.printResults import numberToString
from statparse.printResults import printData
from statparse.analysis import computePercError

def parseArgs():
    parser = OptionParser(usage="verifyModel.py [options] workload np")

    parser.add_option("--period", action="store", type="int", dest="period", default=2**20, help="The period size for the scheme")
    parser.add_option("--verbose", action="store_true", dest="verbose", default=False, help="Verbose output")
    parser.add_option("--decimals", action="store", type="int", dest="decimals", default=4, help="Number of decimals in prints")
    
    opts, args = parser.parse_args()
    
    if len(args) != 2:
        print "Command line error"
        print "Usage: "+parser.usage
        sys.exit(-1)
    
    return opts,args

def runM5(dir, workload, np, otherArgs, verbose):
    if os.path.exists(dir):
        shutil.rmtree(dir)
    os.mkdir(dir)
    
    os.chdir(dir)
    cmd = M5Command()
    cmd.setUpTest(workload, np, "RingBased", 1)
    cmd.setArgument("USE-CHECKPOINT", "/home/jahre/newchk")
    cmd.setArgument("MEMORY-BUS-SCHEDULER", "RDFCFS")
    
    for arg, val in otherArgs:
        cmd.setArgument(arg, val)
    
    cmd.run(0, "", verbose, False)
    
    os.chdir("..")    

def runScheme(wl, np, opts):
    
    extraArgs = []
    
    extraArgs.append( ("AGG-MSHR-MLP-EST", True) )
    extraArgs.append( ("MISS-BW-PERF-METHOD", "no-mlp") )
    extraArgs.append( ("MODEL-THROTLING-POLICY", "stp") )
    extraArgs.append( ("MODEL-THROTLING-POLICY-PERIOD", opts.period) )
    extraArgs.append( ("SIMULATETICKS", opts.period+1000) )
    extraArgs.append( ("--ModelThrottlingPolicy.verify", True) )
    
    runM5("scheme", wl, np, extraArgs, opts.verbose)
    
    return IniFile("scheme/throttling-data-dump.txt")

def runVerify(estimates, wl, np, opts):
    extraArgs = []
    
    extraArgs.append( ("AGG-MSHR-MLP-EST", True) )
    extraArgs.append( ("MISS-BW-PERF-METHOD", "no-mlp") )
    extraArgs.append( ("MODEL-THROTLING-POLICY", "stp") )
    extraArgs.append( ("SIMULATETICKS", opts.period+1000) )
    extraArgs.append( ("MODEL-THROTLING-POLICY-PERIOD", opts.period) )
    extraArgs.append( ("--ModelThrottlingPolicy.verify", True) ) 
    
    statkeyname = "optimal-arrival-rates"
    argstr = str(estimates.data[statkeyname][0])
    for cpuid in range(1, np):
        argstr += ","+str(estimates.data[statkeyname][cpuid])
    
    extraArgs.append( ("MODEL-THROTLING-POLICY-STATIC", argstr) )
    
    runM5("verify", wl, np, extraArgs, opts.verbose)
    
    return IniFile("verify/throttling-data-dump.txt")

def computeArrivalRateAccuracy(estimate, verifydata, np, opts):
    titles = ["", "Goal", "Result", "Error (%)"]
    textarray = [titles]
    for i in range(np):
        line = []
        line.append(str(i))
        
        goalval = estimate.data["optimal-arrival-rates"][i]
        line.append(numberToString(goalval,opts.decimals))
        
        resultingArrivalRate = float(verifydata.data["requests"][i]) / float(opts.period)
        
        line.append(numberToString(resultingArrivalRate, opts.decimals))
        
        line.append(numberToString(computePercError(resultingArrivalRate, goalval), opts.decimals))
        
        textarray.append(line)
        
    leftjust = [True, False, False, False]
    printData(textarray, leftjust, sys.stdout, opts.decimals)

def main():
    opts, args = parseArgs()
    wl = args[0]
    np = int(args[1])

    print
    print "Model Throttling Validation of workload "+wl+" with "+str(np)+" cores"
    print 

    print "Running scheme..."
    estimates = runScheme(wl, np, opts)
    
    print "Scheme run returned values: "
    estimates.dump()
    
    print 
    print "Running verification..."
    verdata = runVerify(estimates, wl, np, opts)
    
    print "Verify returned values: "
    verdata.dump()
    
    print
    print "Arrival rate offset:"
    print
    computeArrivalRateAccuracy(estimates, verdata, np, opts)

if __name__ == '__main__':
    main()