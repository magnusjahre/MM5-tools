#!/usr/bin/python

import sys
import pbsconfig
import os
import interferencemethods as intmethods
import deterministic_fw_wls as workloads
from optparse import OptionParser
from math import sqrt

samplesizes = [2**i for i in range(21)]

def writeOutput(errordict, filename):
    outfile = open(filename, "w")
    
    errorkeys = errordict[samplesizes[0]].keys()
    errorkeys.sort()
    
    width = 20
    
    outfile.write("".ljust(width))
    for ss in samplesizes:
        outfile.write(str(ss).rjust(width))
    outfile.write("\n")
    
    for k in errorkeys:
        outfile.write( k.ljust(width))
        for ss in samplesizes:
            if errordict[ss][k] != -1:
                outfile.write( ("%.3f" % errordict[ss][k]).rjust(width))
            else:
                outfile.write( "NaN".rjust(width))
        outfile.write("\n")
    
    outfile.flush()
    outfile.close()
    
def writeSSOutput(maxdict, sumdict, samplesdict, sumSquares, filename):
    outfile = open(filename, "w")
    
    samplessizes = maxdict.keys()
    samplessizes.sort()
    
    width = 20
    
    outfile.write("".ljust(width))
    outfile.write("Max".rjust(width))
    outfile.write("Average".rjust(width))
    outfile.write("Std Dev".rjust(width))
    outfile.write("\n")
    
    for k in samplessizes:
        outfile.write(str(k).ljust(width))
        outfile.write(str(maxdict[k]).rjust(width))
        if samplesdict[k] > 0:
            average = float(sumdict[k]) / float(samplesdict[k])
            outfile.write( ("%.3f" % average).rjust(width) )
        else:
            outfile.write( "Inf".rjust(width) )
            
        if samplesdict[k] > 1:
            stddev = calculateStddev(samplesdict[k], sumSquares[k], sumdict[k])
            outfile.write( ("%.3f" % stddev).rjust(width) )
        else:
            outfile.write("0".rjust(width))
            
        outfile.write("\n")
    
    outfile.flush()
    outfile.close()
    
def calculateStddev(n, sumsq, sum):
    
    n = float(n)
    sumsq = float(sumsq)
    sum = float(sum)
    
    assert n > 1
    if n * sumsq < sum*sum:
        errtrace = open("errortrace.txt", "a")
        errtrace.write("n*sumsq = "+str(n*sumsq)+"\n")
        errtrace.write("sum*sum = "+str(sum*sum)+"\n")
        errtrace.write("n*sumsq - sum*sum = "+str(n * sumsq - sum*sum)+"\n")
        assert abs(n * sumsq - sum*sum) < 2.0
    
    return  sqrt( max(((n * sumsq) - sum * sum) / (n * (n-1)), 0) )
    
def writeMissedReqOutput(missed, filename):
    outfile = open(filename, "w")
    
    mkeys = missed.keys()
    mkeys.sort()
    
    width = 30
    
    outfile.write("".ljust(width))
    outfile.write("Missed".rjust(width))
    outfile.write("\n")
    
    for mk in mkeys:
        outfile.write(str(mk).ljust(width))
        outfile.write(str(missed[mk]).rjust(width))
        outfile.write("\n")
    
    outfile.flush()
    outfile.close()


def addToAggregate(aggregate, newvals):
    if aggregate == {}:
        return newvals
    
    for type in aggregate:
        assert type in newvals
        for ss in aggregate[type]:
            assert ss in aggregate[type]
            aggregate[type][ss] += newvals[type][ss]
            
    return aggregate

def addToSSAggregate(aggregate, newvals, max):
    if aggregate == {}:
        return newvals
    
    for ss in aggregate:
        assert ss in newvals
        if max:
            if newvals[ss] > aggregate[ss]:
                aggregate[ss] = newvals[ss]
        else:
            aggregate[ss] += newvals[ss]
            
    return aggregate
        
def computeAvg(errors, numReqs):
    avgs = {}
    
    for ss in errors:
        assert ss in numReqs
        avgs[ss] = {}
        for type in errors[ss]:
            if numReqs[ss] == 0:
                avgs[ss][type] = -1
            else:
                avgs[ss][type] = float(errors[ss][type]) / float(numReqs[ss])
            
    return avgs

def computeRMS(errorSquareSum, numSamples):
    avgs = {}
    for ss in errorSquareSum:
        avgs[ss] = {}
        for type in errorSquareSum[ss]:
            if numSamples[ss] <= 0:
                avgs[ss][type] = -1
            else:
                avgs[ss][type] =  sqrt(float(errorSquareSum[ss][type]) / float(numSamples[ss]))
    return avgs

def computeStdDev(errorSum, errorSquareSum, numSamples):
    avgs = {}
    for ss in errorSquareSum:
        avgs[ss] = {}
        for type in errorSquareSum[ss]:
            if numSamples[ss] <= 1:
                avgs[ss][type] = 0
            else:
                avgs[ss][type] =  calculateStddev(numSamples[ss], errorSquareSum[ss][type], errorSum[ss][type])
    return avgs

def main():
    parser = OptionParser(usage="%prog [options] key")
    options,args = parser.parse_args()
    
    assert len(args) == 1
    searchkey = args[0]
    
    print
    print "Analyzing sample sizes for key "+searchkey 
    print
    
    outputdir = "samplesize-"+searchkey 
    os.mkdir(outputdir)
    
    aggregateErr = {}
    aggregateNumSamples = {}
    aggregateErrSquare = {}
    
    maxLatRes = {}
    aggregateLat = {}
    aggregateLatSquare = {}
    
    missedReqs = {}
    
    for cmd, config in pbsconfig.commandlines:
        key = pbsconfig.get_key(cmd,config)
        np = pbsconfig.get_np(config)
        
        if key == searchkey:
            shareddir = pbsconfig.get_unique_id(config)
            wl = pbsconfig.get_workload(config)
            benchmarks = workloads.getBms(wl, np) 
            
            for i in range(np):
                aparams = pbsconfig.get_alone_params(wl, i, config)
                alonedir = pbsconfig.get_unique_id(aparams)
                
                sharedlatfn = shareddir+"/CPU"+str(i)+"LatencyTrace.txt"
                sharedestfn = shareddir+"/CPU"+str(i)+"InterferenceTrace.txt"
                alonelatfn = alonedir+"/CPU0LatencyTrace.txt"
                
                print "Analyzing workload "+wl+", "+benchmarks[i]+" (CPU "+str(i)+")"
                
                results = intmethods.getTraceEstimateError(sharedestfn, alonelatfn, samplesizes, sharedlatfn, searchkey+"-"+wl+"-"+benchmarks[i])
                
                writeOutput(computeRMS(results["sumSquareError"], results["numSamples"]), outputdir+"/bm-rmserror-"+wl+"-"+benchmarks[i]+".txt")
                writeOutput(computeAvg(results["sumError"], results["numSamples"]), outputdir+"/bm-avgerror-"+wl+"-"+benchmarks[i]+".txt")
                writeOutput(computeStdDev(results["sumError"], results["sumSquareError"], results["numSamples"]), outputdir+"/bm-stddev-"+wl+"-"+benchmarks[i]+".txt")
                
                aggregateErr = addToAggregate(aggregateErr, results["sumError"])
                aggregateErrSquare = addToAggregate(aggregateErrSquare, results["sumSquareError"])
                aggregateNumSamples = addToSSAggregate(aggregateNumSamples, results["numSamples"], False)
                
                writeSSOutput(results["maxlat"], results["sumLatency"], results["numSamples"], results["sumSquareLatency"], outputdir+"/latencies-"+wl+"-"+benchmarks[i]+".txt")
                
                maxLatRes = addToSSAggregate(maxLatRes, results["maxlat"], True)
                aggregateLat = addToSSAggregate(aggregateLat, results["sumLatency"], False)
                aggregateLatSquare = addToSSAggregate(aggregateLatSquare, results["sumSquareLatency"], False)
                
                missedReqs[wl+"-"+benchmarks[i]] = results["remaining"]
    
    errorRMS = computeRMS(aggregateErrSquare, aggregateNumSamples)
    errorAvg =  computeAvg(aggregateErr, aggregateNumSamples)
    errorStdDev = computeStdDev(aggregateErr, aggregateErrSquare, aggregateNumSamples) 
    
    writeOutput(errorRMS, outputdir+"/"+searchkey+"-rms.txt")
    writeOutput(errorAvg, outputdir+"/"+searchkey+"-mean.txt")
    writeOutput(errorStdDev, outputdir+"/"+searchkey+"-stddev.txt")
    writeSSOutput(maxLatRes, aggregateLat, aggregateNumSamples, aggregateLatSquare, outputdir+"/"+searchkey+"-latency.txt")
    writeMissedReqOutput(missedReqs, outputdir+"/"+searchkey+"-missed-reqs.txt")

    dictdumpfile = open(searchkey+"-results.py", "w")
    
    dictdumpfile.write("aggregateErr = "+str(aggregateErr)+"\n\n")
    dictdumpfile.write("aggregateErrSquare = "+str(aggregateErrSquare)+"\n\n")
    
    
    dictdumpfile.write("aggregateLat = "+str(aggregateLat)+"\n\n")
    dictdumpfile.write("aggregateLatSquare = "+str(aggregateLatSquare)+"\n\n")

    dictdumpfile.write("aggregateNumSamples = "+str(aggregateNumSamples)+"\n\n")
    
    dictdumpfile.write("errorRMS = "+str(errorRMS)+"\n\n")
    dictdumpfile.write("errorAvg = "+str(errorAvg)+"\n\n")
    dictdumpfile.write("errorStdDev = "+str(errorStdDev)+"\n\n")
    
    dictdumpfile.flush()
    dictdumpfile.close()
            
    return 0

if __name__ == "__main__":
    sys.exit(main())
