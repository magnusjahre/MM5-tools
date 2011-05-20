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
from statparse.util import fatal

def parseArgs():
    parser = OptionParser(usage="verifyModel.py [options] np [workload]")

    parser.add_option("--period", action="store", type="int", dest="period", default=2**20, help="The period size for the scheme")
    parser.add_option("--verbose", action="store_true", dest="verbose", default=False, help="Verbose output")
    parser.add_option("--trace-mshrs", action="store_true", dest="traceMSHRs", default=False, help="Write a trace file of the MSHR occupancy which can be visualized with the visualizeMSHRs.py script")
    parser.add_option("--trace-arrival-rates", action="store_true", dest="traceArrivalRate", default=False, help="Write tracefiles for the arrival rates which can be visualized with the plotTrace.py script")
    parser.add_option("--throttle-policy", action="store", type="string", dest="throttlingPolicy", default="token", help="The throttling policy to use to enforce bandwidth allocations")
    parser.add_option("--impl", action="store", type="string", dest="impl", default="nfq", help="The policy to use to enforce allocations (nfq or throttle)")
    parser.add_option("--decimals", action="store", type="int", dest="decimals", default=6, help="Number of decimals in prints")
    parser.add_option("--outfilename", action="store", dest="outfilename", default="model-accuracy-trace.txt", help="Model accuracy output file")
    
    opts, args = parser.parse_args()
    
    if len(args) < 1 or len(args) > 2:
        print "Command line error"
        print "Usage: "+parser.usage
        sys.exit(-1)
    
    return opts,args

def runM5(dir, workload, np, otherArgs, verbose, isSingle=False):
    if os.path.exists(dir):
        shutil.rmtree(dir)
    os.mkdir(dir)
    
    os.chdir(dir)
    cmd = M5Command()
    if isSingle:
        cmd.setUpTest(workload, 1, "RingBased", 1, np)
    else:
        cmd.setUpTest(workload, np, "RingBased", 1)
    cmd.setArgument("USE-CHECKPOINT", "/home/jahre/newchk")
    
    for arg, val in otherArgs:
        cmd.setArgument(arg, val)
    
    cmd.run(0, "", verbose, False)
    
    os.chdir("..")    

def runScheme(wl, np, opts):
    
    extraArgs = []
    
    extraArgs.append( ("AGG-MSHR-MLP-EST", True) )
    extraArgs.append( ("MISS-BW-PERF-METHOD", "no-mlp") )
    extraArgs.append( ("MODEL-THROTLING-POLICY", "stp") )
    extraArgs.append( ("MODEL-THROTLING-POLICY-PERIOD", opts.period+2) )
    extraArgs.append( ("SIMULATETICKS", opts.period) )
    extraArgs.append( ("--ModelThrottlingPolicy.verify", True) )
    
    if opts.impl == "throttle":
        extraArgs.append( ("MEMORY-BUS-SCHEDULER", "RDFCFS") )
        extraArgs.append( ("MODEL-THROTLING-IMPL-STRAT", "throttle") )
    elif opts.impl == "nfq":
        extraArgs.append( ("MEMORY-BUS-SCHEDULER", "TNFQ") )
        extraArgs.append( ("MODEL-THROTLING-IMPL-STRAT", "nfq") )
    elif opts.impl == "fixedbw":
        extraArgs.append( ("MEMORY-BUS-SCHEDULER", "FBW") )
        extraArgs.append( ("MODEL-THROTLING-IMPL-STRAT", "fixedbw") )
    else:
        fatal("Unknown bandwidth allocation implementation policy")
    
    if opts.traceMSHRs:
        extraArgs.append( ("DO-MSHR-TRACE", True) )

    if opts.traceArrivalRate:
        extraArgs.append( ("DO-ARRIVAL-RATE-TRACE", True) )
    
    runM5("scheme", wl, np, extraArgs, opts.verbose)
    
    return IniFile("scheme/throttling-data-dump.txt")

def runVerify(estimates, wl, np, opts, cpuID):
    extraArgs = []
    
    extraArgs.append( ("MODEL-THROTLING-POLICY-PERIOD", opts.period+2) )
    extraArgs.append( ("SIMULATETICKS", opts.period) )

    extraArgs.append( ("AGG-MSHR-MLP-EST", True) )
    extraArgs.append( ("MISS-BW-PERF-METHOD", "no-mlp") )
    extraArgs.append( ("MODEL-THROTLING-POLICY", "stp") )
    extraArgs.append( ("--ModelThrottlingPolicy.verify", True) )
    extraArgs.append( ("CACHE-THROTLING-POLICY", opts.throttlingPolicy) )
    

    
    if opts.traceMSHRs:
        extraArgs.append( ("DO-MSHR-TRACE", True) ) 
        
    if opts.traceArrivalRate:
        extraArgs.append( ("DO-ARRIVAL-RATE-TRACE", True) )
    
    if opts.impl == "throttle":
        extraArgs.append( ("MEMORY-BUS-SCHEDULER", "RDFCFS") )
        extraArgs.append( ("MODEL-THROTLING-IMPL-STRAT", "throttle") )
        
        statkeyname = "optimal-arrival-rates"
        argstr = str(estimates.data[statkeyname][0])
        for i in range(1, np):
            argstr += ","+str(estimates.data[statkeyname][i])
    
        extraArgs.append( ("MODEL-THROTLING-POLICY-STATIC", argstr) )
        
    elif opts.impl == "nfq" or opts.impl == "fixedbw":
        statkeyname = "optimal-bw-shares"
        argstr = str(estimates.data[statkeyname][0])
        for i in range(1, np):
            argstr += ","+str(estimates.data[statkeyname][i])
        
        if opts.impl == "nfq":
            extraArgs.append( ("MEMORY-BUS-SCHEDULER", "TNFQ") )
            extraArgs.append( ("MODEL-THROTLING-IMPL-STRAT", "nfq") )
        else:
            extraArgs.append( ("MEMORY-BUS-SCHEDULER", "FBW") )
            extraArgs.append( ("MODEL-THROTLING-IMPL-STRAT", "fixedbw") )
            argstr += ","+str(estimates.data["uncontrollable-request-share"][estimates.NO_CPU_KEY])
        
        extraArgs.append( ("MODEL-THROTLING-POLICY-STATIC", argstr) )
    else:
        fatal("Unknown bandwidth allocation implementation policy")
    

    
    dirname = "verify"+str(cpuID)
    
    runM5(dirname, wl, np, extraArgs, opts.verbose)
    
    return IniFile(dirname+"/throttling-data-dump.txt")

def runBaseline(estimates, wl, np, opts, cpuID):
    extraArgs = []
    
    comInstructions = estimates.data["committed-instructions"][cpuID]
    extraArgs.append( ("SIMINSTS", comInstructions) )
    extraArgs.append( ("MODEL-THROTLING-POLICY-PERIOD", opts.period*np) )
    
    extraArgs.append( ("AGG-MSHR-MLP-EST", True) )
    extraArgs.append( ("MISS-BW-PERF-METHOD", "no-mlp") )
    extraArgs.append( ("MODEL-THROTLING-POLICY", "stp") )
    extraArgs.append( ("--ModelThrottlingPolicy.verify", True) )
    extraArgs.append( ("MEMORY-BUS-SCHEDULER", "RDFCFS") )
    extraArgs.append( ("MODEL-THROTLING-IMPL-STRAT", "throttle") ) # not used, but required
    
    if opts.traceArrivalRate:
        extraArgs.append( ("DO-ARRIVAL-RATE-TRACE", True) )
    
    if opts.traceMSHRs:
        extraArgs.append( ("DO-MSHR-TRACE", True) ) 
        
    if opts.traceArrivalRate:
        extraArgs.append( ("DO-ARRIVAL-RATE-TRACE", True) )
    
    dirname = "alone"+str(cpuID)
    
    wls = Workloads()
    bms = wls.getBms(wl, np, True)
    runM5(dirname, bms[cpuID], np, extraArgs, opts.verbose, True)
    
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
        self.keyToName = {}
        
    def computeAccuracy(self):
        self.percentageAccuracies["arrival-rate"] = self._computePercAccuracyFromKeys("optimal-arrival-rates", "measured-request-rate")
        self.keyToName["arrival-rate"] = "Arrival Rate Accuracy (%)" 
        
        self.percentageAccuracies["com-inst"] = self._computePercAccuracyFromKeys("committed-instructions", "committed-instructions")
        self.keyToName["com-inst"] = "Committed Instruction Accuracy (%)"
        
        self.percentageAccuracies["num-req"] = self._computePercAccuracyFromKeys("requests", "requests")
        self.keyToName["num-req"] = "Number of Requests Accuracy (%)"
        
        self.percentageAccuracies["met-val"] = self._computePercAccuracyFromKeys("opt-metric-value", "cur-metric-value")
        self.keyToName["met-val"] = "Metric Value Estimate Error (%)" 
    
    def _computePercAccuracyFromKeys(self, estimatekey, verifykey):
        if len(self.estimates.data[estimatekey].keys()) > 1:
            estimatevals = [self.estimates.data[estimatekey][i] for i in range(self.np)]
        else:
            estimatevals = [self.estimates.data[estimatekey][self.estimates.NO_CPU_KEY] for i in range(self.np)]
            
        if len(self.verdata[i].data[verifykey].keys()) > 1:
            verifyvals = [self.verdata[i].data[verifykey][i] for i in range(self.np)]
        else:
            verifyvals = [self.verdata[i].data[verifykey][self.verdata[i].NO_CPU_KEY] for i in range(self.np)]
        
        retvals = ["N/A" for i in range(self.np)]
        for i in range(self.np):
            if verifyvals[i] != 0:
                retvals[i] = computePercError(estimatevals[i], verifyvals[i])
        
        return retvals
    
    def dumpAccuracies(self):
        titles = [""]
        leftjust = [True]
        for i in range(self.np):
            titles.append("CPU "+str(i))
            leftjust.append(False)
            
        textlines = [titles]
        for k in sorted(self.percentageAccuracies):
            line = [self.keyToName[k]]
            assert len(self.percentageAccuracies[k]) == self.np
            for d in self.percentageAccuracies[k]:
                line.append(numberToString(d, self.decimals))
            textlines.append(line)
            
        printData(textlines, leftjust, sys.stdout, self.decimals)

class ResultElement:
    
    def __init__(self, valFromTest, actualVal):
        self.valFromTest = valFromTest
        self.actualVal = actualVal
    
    def accuracy(self):
        return computePercError(self.valFromTest, self.actualVal)
        
    def __str__(self):
        return "Test: "+str(self.valFromTest)+", Actual: "+str(self.actualVal)+", Error: "+str(self.accuracy())+" %"

class SystemAccuracy:
    
    def __init__(self, estimates, verdatalist, baselinelist, np, decimals):
        self.np = np
        self.decimals = decimals        
        
        self.estimates = estimates
        self.verdatalist = verdatalist
        self.baselinelist = baselinelist
        
        self.results = []
    
    def computeAccuracies(self):
        
        self.accuracies = {}
        
        self.accuracies["Metric"] = ["N/A" for i in range(self.np)]
        estimate = self.estimates.data["opt-metric-value"][self.estimates.NO_CPU_KEY]
        for i in range(self.np):
            actual = self.verdatalist[i].data["cur-metric-value"][self.estimates.NO_CPU_KEY]
            self.accuracies["Metric"][i] = ResultElement(estimate, actual)
            
        self.accuracies["Estimate Alone Cycles"] = ["N/A" for i in range(self.np)]
        for i in range(self.np):
            estimate = self.estimates.data["alone-cycles"][i]
            actual = self.baselinelist[i].data["ticks"][0]
            self.accuracies["Estimate Alone Cycles"][i] = ResultElement(estimate, actual)
            
        self.accuracies["Scheme Alone Cycles"] = ["N/A" for i in range(self.np)]
        for i in range(self.np):
            estimate = self.verdatalist[i].data["alone-cycles"][i]
            actual = self.baselinelist[i].data["ticks"][0]
            self.accuracies["Scheme Alone Cycles"][i] = ResultElement(estimate, actual) 
    
    def dumpAccuracies(self):
        for k in self.accuracies:
            print
            print k
            for i in range(self.np):
                print str(i)+": "+str(self.accuracies[k][i])
    
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

    baselinelist = []
    for i in range(np):
        print 
        print "Running verification for CPU "+str(i)
        baselinedata = runBaseline(estimates, wl, np, opts, i)
        baselinelist.append(baselinedata)
        
        print "Verify returned values: "
        baselinedata.dump()
        
    systemres = SystemAccuracy(estimates, verdatalist, baselinelist, np, opts.decimals)
    systemres.computeAccuracies()
    systemres.dumpAccuracies()

    printMetrics(estimates, verdatalist, baselinelist, np, opts)

def printMetrics(estimates, verdatalist, baselinelist, np, opts):
    sharedIPC = [float(estimates.data["committed-instructions"][i]) / float(opts.period) for i in range(np)]
    aloneIPC = [float(baselinelist[i].data["committed-instructions"][0]) / float(baselinelist[i].data["ticks"][0]) for i in range(np)]
    
    print
    sumIPC = 0.0
    for i in range(np):
        speedup = (sharedIPC[i]/aloneIPC[i])
        print "CPU "+str(i)+" estimate: shared "+str(sharedIPC[i])+", alone "+str(aloneIPC[i])+", speedup "+str(speedup)
        sumIPC += speedup
        
    print "Actual System Throughput is "+str(sumIPC)
        
    for i in range(np):
        sharedIPC = [float(verdatalist[i].data["committed-instructions"][j]) / float(verdatalist[i].data["ticks"][j]) for j in range(np)]
    
        print    
        verSumIPC = 0.0
        for j in range(np):
            speedup = (sharedIPC[j]/aloneIPC[j])
            print "CPU "+str(j)+" actual:  shared "+str(sharedIPC[j])+", alone "+str(aloneIPC[j])+", speedup "+str(speedup)
            verSumIPC += speedup
            
        print "Verify "+str(i)+" System Throughput is "+str(verSumIPC)
    print
        
def printMultiRes(results, opts, np):
    
    titles = [""]
    leftjust = [True]
    titlesInited = False
    textarray = [[]]
    
    for wl in sorted(results.keys()):
        for cpuid in range(np):
            line = [wl+"-"+str(cpuid)] 
            for k in sorted(results[wl].percentageAccuracies):
                if not titlesInited:
                    titles.append(results[wl].keyToName[k])
                    leftjust.append(False)
                line.append(numberToString(results[wl].percentageAccuracies[k][cpuid], opts.decimals))    
            titlesInited = True
            textarray.append(line)
            
    textarray[0] = titles

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
        verdatalist = [None for i in range(np)]
        for i in range(np):
            verdatalist[i] = runVerify(goaldata, wl, np, opts, i)
        
        print 
        print wl
        accuracyobj = ModelAccuracy(goaldata, verdatalist, np, opts.decimals)
        accuracyobj.computeAccuracy()
        accuracyobj.dumpAccuracies()
        sys.stdout.flush()
        
        assert wl not in results
        results[wl] = accuracyobj
        
    printMultiRes(results, opts, np)

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