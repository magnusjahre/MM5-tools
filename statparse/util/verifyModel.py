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
from workloadfiles.workloads import Workloads
from workloadfiles.workloads import TYPED_WL

def parseArgs():
    parser = OptionParser(usage="verifyModel.py [options] np [workload]")

    parser.add_option("--period", action="store", type="int", dest="period", default=2**20, help="The period size for the scheme")
    parser.add_option("--verbose", action="store_true", dest="verbose", default=False, help="Verbose output")
    parser.add_option("--trace-mshrs", action="store_true", dest="traceMSHRs", default=False, help="Write a trace file of the MSHR occupancy which can be visualized with the visualizeMSHRs.py script")
    parser.add_option("--trace-arrival-rates", action="store_true", dest="traceArrivalRate", default=False, help="Write tracefiles for the arrival rates which can be visualized with the plotTrace.py script")
    parser.add_option("--decimals", action="store", type="int", dest="decimals", default=6, help="Number of decimals in prints")
    parser.add_option("--outfilename", action="store", dest="outfilename", default="model-accuracy-trace.txt", help="Model accuracy output file")
    
    opts, args = parser.parse_args()
    
    if len(args) < 1 or len(args) > 2:
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
    
    if opts.traceMSHRs:
        extraArgs.append( ("DO-MSHR-TRACE", True) )
    
    runM5("scheme", wl, np, extraArgs, opts.verbose)
    
    return IniFile("scheme/throttling-data-dump.txt")

def runVerify(estimates, wl, np, opts, cpuID):
    extraArgs = []
    
    testPeriod = estimates.data["optimal-periods"][cpuID]
    extraArgs.append( ("MODEL-THROTLING-POLICY-PERIOD", testPeriod) )
    extraArgs.append( ("SIMULATETICKS", testPeriod+1000) )
    
    extraArgs.append( ("AGG-MSHR-MLP-EST", True) )
    extraArgs.append( ("MISS-BW-PERF-METHOD", "no-mlp") )
    extraArgs.append( ("MODEL-THROTLING-POLICY", "stp") )
    extraArgs.append( ("--ModelThrottlingPolicy.verify", True) )
    
    if opts.traceMSHRs:
        extraArgs.append( ("DO-MSHR-TRACE", True) ) 
        
    if opts.traceArrivalRate:
        extraArgs.append( ("DO-ARRIVAL-RATE-TRACE", True) )
    
    statkeyname = "optimal-arrival-rates"
    argstr = str(estimates.data[statkeyname][0])
    for cpuid in range(1, np):
        argstr += ","+str(estimates.data[statkeyname][cpuid])
    
    extraArgs.append( ("MODEL-THROTLING-POLICY-STATIC", argstr) )
    
    
    
    dirname = "verify"+str(cpuid)
    
    runM5(dirname, wl, np, extraArgs, opts.verbose)
    
    return IniFile(dirname+"/throttling-data-dump.txt")

def printArrivalRateAccuracy(estimate, verifydata, estkey, verkey, np, opts):
    titles = ["", "Goal", "Result", "Error (%)"]
    textarray = [titles]
    for i in range(np):
        line = []
        line.append(str(i))
        
        accuracy = computeAccuracy(estimate, verifydata, estkey, verkey, i)
        
        line.append(numberToString(accuracy.goalval,opts.decimals))
        line.append(numberToString(accuracy.verval, opts.decimals))
        line.append(numberToString(accuracy.accuracy, opts.decimals))
        
        textarray.append(line)
        
    leftjust = [True, False, False, False]
    printData(textarray, leftjust, sys.stdout, opts.decimals)

class GoalAccuracy:
    
    def __init__(self, cpuid, goalval, verval):
        self.cpuid = cpuid
        self.goalval = goalval
        self.verval = verval
        self.accuracy = computePercError(verval, goalval)
        
    def dump(self, wlname):
        print wlname+"("+str(self.cpuid)+"): goal="+str(self.goalval)+", actual="+str(self.verval)+", accuracy="+str(self.accuracy)+"%"
    
def computeAccuracy(goaldata, verifydata, goalkey, verifykey, cpuID):
    goalval = goaldata.data[goalkey][cpuID]
    verval = verifydata.data[verifykey][cpuID]
    
    acc = GoalAccuracy(cpuID, goalval, verval)
    return acc
    
class ModelAccuracy:
    
    def __init__(self, estimate, verdatalist, np, decimals):
        self.estimates = estimate
        self.verdata = verdatalist
        self.np = np
        self.decimals = decimals
        self.percentageAccuracies = {}
        
    def computeAccuracy(self):
        self.percentageAccuracies["Arrival Rate Accuracy (%)"] = self._computePercAccuracyFromKeys("optimal-arrival-rates", "measured-request-rate")
        self.percentageAccuracies["Committed Instruction Accuracy (%)"] = self._computePercAccuracyFromKeys("committed-instructions", "committed-instructions")
        self.percentageAccuracies["Number of Requests Accuracy (%)"] = self._computePercAccuracyFromKeys("requests", "requests")
    
    def _computePercAccuracyFromKeys(self, estimatekey, verifykey):
        estimatevals = [self.estimates.data[estimatekey][i] for i in range(self.np)]
        verifyvals = [self.verdata[i].data[verifykey][i] for i in range(self.np)]
        return [computePercError(estimatevals[i], verifyvals[i]) for i in range(self.np)]
    
    def dumpAccuracies(self):
        titles = [""]
        leftjust = [True]
        for i in range(self.np):
            titles.append("CPU "+str(i))
            leftjust.append(False)
            
        textlines = [titles]
        for k in sorted(self.percentageAccuracies):
            line = [k]
            assert len(self.percentageAccuracies[k]) == self.np
            for d in self.percentageAccuracies[k]:
                line.append(numberToString(d, self.decimals))
            textlines.append(line)
            
        printData(textlines, leftjust, sys.stdout, self.decimals)
    
def runSingle(wl, np, opts):
    print
    print "Model Throttling Validation of workload "+wl+" with "+str(np)+" cores"
    print 

    print "Running scheme..."
    estimates = runScheme(wl, np, opts)
    
    print "Scheme run returned values: "
    estimates.dump()
    
    verdatalist = [None for i in range(np)]
    
    for i in range(np):
        print 
        print "Running verification for CPU "+str(i)
        verdata = runVerify(estimates, wl, np, opts, i)
        
        print "Verify returned values: "
        verdata.dump()
        
        print
        print "Arrival rate offset:"
        print
        printArrivalRateAccuracy(estimates, verdata, "optimal-arrival-rates", "measured-request-rate", np, opts)
        
        verdatalist[i] = verdata
    
    print
    print "Result summary:"
    result = ModelAccuracy(estimates, verdatalist, np, opts.decimals)
    result.computeAccuracy()
    result.dumpAccuracies()

def printMultiRes(results, opts):
    titles = ["", "Goal", "Result", "Error (%)"]
    textarray = [titles]
    for wl in sorted(results.keys()):
        for cpuid in sorted(results[wl].keys()):
            line = [wl+"-"+str(cpuid), 
                    numberToString(results[wl][cpuid].goalval, opts.decimals), 
                    numberToString(results[wl][cpuid].verval, opts.decimals), 
                    numberToString(results[wl][cpuid].accuracy, opts.decimals)]
            textarray.append(line)
    leftjust = [True, False, False, False]
    outfile = open(opts.outfilename, "w")
    printData(textarray, leftjust, outfile, opts.decimals)
    outfile.close()

def runMulti(np, opts):

    print
    print "Model Throttling Validation of workload with "+str(np)+" cores"
    print 
    
    wls = Workloads()
    
    results = {}
    
    for wl in wls.getWorkloads(np, TYPED_WL):
        goaldata = runScheme(wl, np, opts)
        verdata = runVerify(goaldata, wl, np, opts)
        
        assert wl not in results
        results[wl] = {}
        
        for i in range(np):
            accuracy = computeAccuracy(goaldata, verdata, "optimal-arrival-rates", "measured-request-rate", i)
            accuracy.dump(wl)
            results[wl][i] = accuracy
        sys.stdout.flush()
            
    printMultiRes(results, opts)

def main():
    opts, args = parseArgs()
    np = int(args[0])
    
    if len(args) == 2:
        wl = args[1]
        runSingle(wl, np, opts)
    else:
        runMulti(np, opts)


if __name__ == '__main__':
    main()