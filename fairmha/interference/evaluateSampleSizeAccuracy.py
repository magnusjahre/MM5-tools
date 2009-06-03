#!/usr/bin/python

import sys
import pbsconfig
import os
import re
import interferencemethods as intmethods
import deterministic_fw_wls as workloads
from optparse import OptionParser
from math import sqrt

runTraceFile = "all-experiment-data.txt"
rtWidth = 40

def writeOutput(errordict, filename, samplesizes):
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


def addToAggregate(aggregate, newvals, key, isSampleSize):

    if not isSampleSize:
        if key not in aggregate:
            aggregate[key] = {}
            for type in newvals[1]:
                aggregate[key][type] = 0

        for type in aggregate[key]:
            aggregate[key][type] += newvals[1][type]

        return aggregate

    if aggregate == {}:
        return newvals
    
    for type in aggregate:
        assert type in newvals
        for ss in aggregate[type]:
            assert ss in aggregate[type]
            aggregate[type][ss] += newvals[type][ss]
            
    return aggregate

def addToSSAggregate(aggregate, newvals, max, key, isSampleSize):

    if not isSampleSize:
        if key not in aggregate:
            aggregate[key] = 0
        aggregate[key] += newvals[1]
        return aggregate

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

def analyzeSampleExperiment(aggregates, searchkey):

    samplesizes = [2**i for i in range(21)]

    print
    print "Analyzing sample sizes for key "+searchkey 
    print

    outputdir = "samplesize-"+searchkey 
    os.mkdir(outputdir)
    
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
                
                results = intmethods.getTraceEstimateError("../"+sharedestfn, "../"+alonelatfn, samplesizes, "../"+sharedlatfn, searchkey+"-"+wl+"-"+benchmarks[i])
                aggregates = writeResultOutput(results,outputdir,wl+"-"+benchmarks[i],aggregates, samplesizes, key, True)

    errorAvg,errorStdDev,errorRMS,relErrAvg,relErrStdDev,relErrRMS =  computeEstimators(aggregates)
    
    writeOutput(errorRMS, outputdir+"/"+searchkey+"-rms.txt", samplesizes)
    writeOutput(errorAvg, outputdir+"/"+searchkey+"-mean.txt", samplesizes)
    writeOutput(errorStdDev, outputdir+"/"+searchkey+"-stddev.txt", samplesizes)
    
    writeSSOutput(aggregates["maxLatRes"], aggregates["aggregateLat"], aggregates["aggregateNumSamples"], aggregates["aggregateLatSquare"], outputdir+"/"+searchkey+"-latency.txt")
    writeMissedReqOutput(aggregates["missedReqs"], outputdir+"/"+searchkey+"-missed-reqs.txt")

    dumpDictFile(aggregates, searchkey+"-results.py", errorAvg, errorStdDev, errorRMS)

def dumpDictFile(aggregates, filename, errorAvg, errorStdDev, errorRMS, relErrAvg = None, relErrStdDev = None, relErrRMS = None):

    dictdumpfile = open(filename, "w")
    
    dictdumpfile.write("aggregateErr = "+str(aggregates["aggregateErr"])+"\n\n")
    dictdumpfile.write("aggregateErrSquare = "+str(aggregates["aggregateErrSquare"])+"\n\n")
    
    dictdumpfile.write("aggregateLat = "+str(aggregates["aggregateLat"])+"\n\n")
    dictdumpfile.write("aggregateLatSquare = "+str(aggregates["aggregateLatSquare"])+"\n\n")

    dictdumpfile.write("aggregateNumSamples = "+str(aggregates["aggregateNumSamples"])+"\n\n")
    
    dictdumpfile.write("errorRMS = "+str(errorRMS)+"\n\n")
    dictdumpfile.write("errorAvg = "+str(errorAvg)+"\n\n")
    dictdumpfile.write("errorStdDev = "+str(errorStdDev)+"\n\n")
    
    if relErrRMS != None:
        dictdumpfile.write("relErrorRMS = "+str(relErrRMS)+"\n\n")
    if relErrAvg != None:
        dictdumpfile.write("relErrorAvg = "+str(relErrAvg)+"\n\n")
    if relErrStdDev != None:
        dictdumpfile.write("relErrorStdDev = "+str(relErrStdDev)+"\n\n")
    
    dictdumpfile.flush()
    dictdumpfile.close()

def traceTotalData(name, average, stddev, rms):

    assert len(average.keys()) == 1
    assert average.keys()[0] == 1

    of = open(runTraceFile, "a")
    of.write(name.ljust(rtWidth))
    of.write(("%.3f" % average[1]["Total"]).rjust(rtWidth))
    of.write(("%.3f" % stddev[1]["Total"]).rjust(rtWidth))
    of.write(("%.3f" % rms[1]["Total"]).rjust(rtWidth))
    of.write("\n")
    of.flush()
    of.close()

def writeResultOutput(results, outputdir, basename, aggregates, samplesizes, key, isSampleSize = False):

    avgResult,stddevResult,rmsResult = computeResultEstimators(results)
    
    writeOutput(rmsResult, outputdir+"/bm-rmserror-"+basename+".txt", samplesizes)
    writeOutput(avgResult, outputdir+"/bm-avgerror-"+basename+".txt", samplesizes)
    writeOutput(stddevResult, outputdir+"/bm-stddev-"+basename+".txt", samplesizes)

    if not isSampleSize:
        traceTotalData(basename, avgResult,stddevResult,rmsResult)

    aggregates["aggregateErr"] = addToAggregate(aggregates["aggregateErr"], results["sumError"], key, isSampleSize)
    aggregates["aggregateErrSquare"] = addToAggregate(aggregates["aggregateErrSquare"], results["sumSquareError"], key, isSampleSize)
    
    aggregates["aggregateRelErr"] = addToAggregate(aggregates["aggregateRelErr"], results["sumRelativeError"], key, isSampleSize)
    aggregates["aggregateRelErrSquare"] = addToAggregate(aggregates["aggregateRelErrSquare"], results["sumSquareRelativeError"], key, isSampleSize)
    
    aggregates["aggregateNumSamples"] = addToSSAggregate(aggregates["aggregateNumSamples"],
                                                         results["numSamples"],
                                                         False,
                                                         key,
                                                         isSampleSize)

    writeSSOutput(results["maxlat"], results["sumLatency"], results["numSamples"],
                  results["sumSquareLatency"], outputdir+"/latencies-"+basename+".txt")

    if isSampleSize:
        aggregates["maxLatRes"] = addToSSAggregate(aggregates["maxLatRes"], results["maxlat"], True, "", isSampleSize)
        aggregates["aggregateLat"] = addToSSAggregate(aggregates["aggregateLat"], results["sumLatency"], False, "", isSampleSize)
        aggregates["aggregateLatSquare"] = addToSSAggregate(aggregates["aggregateLatSquare"],
                                                            results["sumSquareLatency"],
                                                            False, "",
                                                            isSampleSize)
                
    aggregates["missedReqs"][basename] = results["remaining"]

    return aggregates


def generateFilenames(searchkey, onlyIncludeNP):
    
    filenames = []

    searchPattern = re.compile(searchkey)

    for cmd, config in pbsconfig.commandlines:

        key = pbsconfig.get_key(cmd,config)
        np = pbsconfig.get_np(config)
        
        if np != -1 and np != onlyIncludeNP:
            continue
        
        if searchPattern.findall(key) != []:
            shareddir = pbsconfig.get_unique_id(config)
            wl = pbsconfig.get_workload(config)
            benchmarks = workloads.getBms(wl, np) 
            
            for i in range(np):
                aparams = pbsconfig.get_alone_params(wl, i, config)
                alonedir = pbsconfig.get_unique_id(aparams)
 
                sharedlatfn = shareddir+"/CPU"+str(i)+"LatencyTrace.txt"
                sharedestfn = shareddir+"/CPU"+str(i)+"InterferenceTrace.txt"
                alonelatfn = alonedir+"/CPU0LatencyTrace.txt"

                fndict = {"shared": "../"+sharedlatfn,
                          "estimate": "../"+sharedestfn,
                          "alone": "../"+alonelatfn,
                          "basename":key+"-"+wl+"-"+benchmarks[i],
                          "key":key}

                filenames.append(fndict)

    return filenames

def computeResultEstimators(results):

    errorRMS = computeRMS(results["sumSquareError"],results["numSamples"])
    errorAvg = computeAvg(results["sumError"], results["numSamples"])
    errorStdDev = computeStdDev(results["sumError"], results["sumSquareError"], results["numSamples"])

    return errorAvg, errorStdDev, errorRMS

def computeEstimators(aggregates):
    
    errorRMS = computeRMS(aggregates["aggregateErrSquare"], aggregates["aggregateNumSamples"])
    errorAvg =  computeAvg(aggregates["aggregateErr"], aggregates["aggregateNumSamples"])
    errorStdDev = computeStdDev(aggregates["aggregateErr"], aggregates["aggregateErrSquare"], aggregates["aggregateNumSamples"]) 

    relErrorRMS = computeRMS(aggregates["aggregateRelErrSquare"],aggregates["aggregateNumSamples"])
    relErrorAvg = computeAvg(aggregates["aggregateRelErr"], aggregates["aggregateNumSamples"])
    relErrorStdDev = computeStdDev(aggregates["aggregateRelErr"], aggregates["aggregateRelErrSquare"], aggregates["aggregateNumSamples"])

    return errorAvg, errorStdDev, errorRMS, relErrorAvg, relErrorStdDev, relErrorRMS

def analyzeAllKeys(aggregates, searchkey, rowid, rowkeyIsInt, swapColRow, onlyIncludeNP):
        
    outputdir = "allkeys-tmp-storage"
    if onlyIncludeNP != -1:
        outputdir = str(onlyIncludeNP)+"-"+outputdir
    
    os.mkdir(outputdir)

    for filenames in generateFilenames(searchkey, onlyIncludeNP):
        
        print "Analyzing workload with ID "+filenames["basename"]
        
        results = intmethods.getTraceEstimateError(filenames["estimate"],
                                                   filenames["alone"],
                                                   [1],
                                                   filenames["shared"],
                                                   filenames["basename"])

        aggregates = writeResultOutput(results, outputdir, filenames["basename"], aggregates, [1], filenames["key"])

    keys = aggregates["aggregateErr"].keys()

    keystorage = {}
    rowkeys = []
    colkeys = []
    for k in keys:
        splitted = k.split("-")
        prev = splitted[0:rowid]
        if rowkeyIsInt:
            rk = int(splitted[rowid])
        else:
            rk = splitted[rowid]
        post = splitted[rowid+1:]
                
        colKey = ""
        for e in prev:
            colKey += e+"-"
        for e in post:
            colKey += e+"-"

        if rk not in rowkeys:
            rowkeys.append(rk)
        if colKey not in colkeys:
            colkeys.append(colKey)
        keystorage[(rk, colKey)] = k 

    rowkeys.sort()
    colkeys.sort()

    if swapColRow:
        tmp = rowkeys
        rowkeys = colkeys
        colkeys = tmp

    errorAvg, errorStdDev, errorRMS, relErrorAvg, relErrorStdDev, relErrorRMS =  computeEstimators(aggregates)

    outdata = {"agg-avgerr.txt": errorAvg, 
                "agg-error-stddev.txt": errorStdDev,
                "agg-rmserr.txt": errorRMS,
                "agg-relative-avgerr.txt": relErrorAvg, 
                "agg-relative-error-stddev.txt": relErrorStdDev,
                "agg-relative-rmserr.txt": relErrorRMS, 
                }
    
    for fn in outdata: 
        outfn = fn
        if searchkey != ".*":
            outfn = searchkey.replace(".*","") + "-"+ fn
        writeKeybasedData(outputdir+"/"+outfn, keystorage, rowkeys, colkeys, outdata[fn], "Total", swapColRow)
    
    dumpFilename = "results.py"
    if searchkey != ".*":
        dumpFilename= searchkey.replace(".*","") + "-"+ dumpFilename
    if onlyIncludeNP != -1:
        dumpFilename = str(onlyIncludeNP)+"-"+dumpFilename
    
    dumpDictFile(aggregates, dumpFilename, errorAvg, errorStdDev, errorRMS, relErrorAvg, relErrorStdDev, relErrorRMS)

def writeKeybasedData(filename, keystorage, rowkeys, colkeys, data, printkey, swapped):
    
    print "Writing output to file "+filename
    
    width = 30
    outfile = open(filename, "w")

    outfile.write("".ljust(width))
    for ck in colkeys:
        outfile.write(str(ck).rjust(width))
    outfile.write("\n")

    
    for rk in rowkeys:
        outfile.write(str(rk).ljust(width))
        for ck in colkeys:
            if not swapped:
                reskey = keystorage[(rk,ck)]
            else:
                reskey = keystorage[(ck,rk)]
            outfile.write(("%.3f" % data[reskey][printkey]).rjust(width))
        outfile.write("\n")
    

def main():
    parser = OptionParser(usage="evaluateSampleSizeAccuracy.py [options] command")
    parser.add_option("-k", "--search-key", action="store", dest="searchkey", default=".*", help="Only include results that matches this key")
    parser.add_option("-r", "--row-key-pos", type="int", action="store", dest="rowkeyid", default=0, help="Position to key to use in table rows")
    parser.add_option("--rowkey-is-int", action="store_true", dest="rowkeyIsInt", default=False, help="Position to key to use in table rows")
    parser.add_option("--swap-col-and-row", action="store_true", dest="swapColRow", default=False, help="Print the row elements in columns and vice versa")
    parser.add_option("--only-np", action="store", type="int", dest="np", default=-1, help="Only include results with this processor count")
    options,args = parser.parse_args()

    cmdErrStr  = "Unknown command, alternatives are: samplesize, allkeys"

    if len(args) != 1:
        print "Usage: "+parser.usage
        print cmdErrStr
        print
        return 0

    rt = open(runTraceFile, "w")
    rt.write("".ljust(rtWidth))
    rt.write("Average".rjust(rtWidth))
    rt.write("Stddev".rjust(rtWidth))
    rt.write("RMS".rjust(rtWidth)+"\n")
    rt.flush()
    rt.close()

    aggregates = {"aggregateErr": {},
                  "aggregateNumSamples": {},
                  "aggregateErrSquare": {},
                  "maxLatRes": {},
                  "aggregateLat": {},
                  "aggregateLatSquare": {},
                  "missedReqs": {},
                  "aggregateRelErr": {},
                  "aggregateRelErrSquare": {}}
    
    if args[0] == "samplesize":
        assert options.searchkey != ".*"
        analyzeSampleExperiment(aggregates, options.searchkey)
    elif args[0] == "allkeys":
        analyzeAllKeys(aggregates, options.searchkey, options.rowkeyid, options.rowkeyIsInt, options.swapColRow, options.np)
    else:
        print parser.usage
        print cmdErrStr
        print

    return 0

if __name__ == "__main__":
    sys.exit(main())
