#!/usr/bin/python

import sys
import pbsconfig
import os
import interferencemethods as intmethods
import deterministic_fw_wls as workloads
from optparse import OptionParser
from math import sqrt

samplesizes = [1,5,10,25,50,75,100,200,300,400,500,1000,10000, 100000]

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
    
def writeSSOutput(maxdict, sumdict, samplesdict, filename):
    outfile = open(filename, "w")
    
    samplessizes = maxdict.keys()
    samplessizes.sort()
    
    width = 30
    
    outfile.write("".ljust(width))
    outfile.write("Max".rjust(width))
    outfile.write("Average".rjust(width))
    outfile.write("\n")
    
    for k in samplessizes:
        outfile.write(str(k).ljust(width))
        outfile.write(str(maxdict[k]).rjust(width))
        if samplesdict[k] > 0:
            average = float(sumdict[k]) / float(samplesdict[k])
            outfile.write( ("%.3f" % average).rjust(width) )
        else:
            outfile.write( "Inf".rjust(width) )
        outfile.write("\n")
    
    outfile.flush()
    outfile.close()
    
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
    for type in errors:
        assert type in numReqs
        avgs[type] = {}
        for ss in errors[type]:
            if numReqs[type][ss] == 0:
                avgs[type][ss] = "Inf"
            else:
                avgs[type][ss] = float(errors[type][ss]) / float(numReqs[type][ss])
            
    return avgs

def computeRMS(errorSquareSum, numSamples):
    avgs = {}
    for ss in errorSquareSum:
        avgs[ss] = {}
        for type in errorSquareSum[ss]:
            if numSamples[ss] == 0:
                avgs[ss][type] = "Inf"
            else:
                avgs[ss][type] =  sqrt(float(errorSquareSum[ss][type]) / float(numSamples[ss]))
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
    aggregateReqs = {}
    
    maxLatRes = {}
    aggregateLat = {}
    aggregateSamples = {}
    
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
                
                errsum, maxlat, sumlat, numsamp, leftreqs = intmethods.getTraceEstimateError(sharedestfn, alonelatfn, samplesizes, sharedlatfn, wl+"-"+benchmarks[i])
                writeOutput(computeRMS(errsum, numsamp), outputdir+"/bmerrs-"+wl+"-"+benchmarks[i]+".txt")
                aggregateErr = addToAggregate(aggregateErr, errsum)
                aggregateReqs = addToSSAggregate(aggregateReqs, numsamp, False)
                
                writeSSOutput(maxlat, sumlat, numsamp, outputdir+"/latencies-"+wl+"-"+benchmarks[i]+".txt")
                
                maxLatRes = addToSSAggregate(maxLatRes, maxlat, True)
                aggregateLat = addToSSAggregate(aggregateLat, sumlat, False)
                aggregateSamples = addToSSAggregate(aggregateSamples, numsamp, False)
                
                missedReqs[wl+"-"+benchmarks[i]] = leftreqs
                
    writeOutput(computeAvg(aggregateErr, aggregateReqs), outputdir+"/"+searchkey+"-average.txt")
    writeSSOutput(maxLatRes, aggregateLat, aggregateSamples, outputdir+"/"+searchkey+"-latency.txt")
    writeMissedReqOutput(missedReqs, outputdir+"/"+searchkey+"-missed-reqs.txt")
            
    return 0

if __name__ == "__main__":
    sys.exit(main())
