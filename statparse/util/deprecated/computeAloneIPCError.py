#!/usr/bin/env python

import sys

from statparse.tracefile.tracefileData import TracefileData
import statparse.tracefile.tracefileData as tracefile
import deterministic_fw_wls as workloads

from optparse import OptionParser

from statparse.util import fatal
from statparse.util import warn
from statparse.util import getSingleParamExperimentDirs

from statparse.analysis import computeStddev
from statparse.analysis import computeMean
from statparse.analysis import computeRMS

from statparse.printResults import printData
from statparse.printResults import numberToString

TRACENAME="missBandwidthPolicyAloneIPCTrace.txt"

def parseArgs():
    parser = OptionParser(usage="computeAloneIPCError.py [options] np period")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--verbose", action="store_true", dest="verbose", default=False, help="Print extra progress output")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--include-params", action="store", dest="includeParams", type="string", default="", help="A standard parameter string that indicates the parameters to include")
    parser.add_option("--print-all", action="store_true", dest="printAll", default=False, help="Print results for each workload")
    parser.add_option("--relative", action="store_true", dest="relativeErrors", default=False, help="Print relative errors (Default: absolute)")
    parser.add_option("--use-avg-lat-estimate", action="store_true", dest="useAvgLatEstimate", default=False, help="Use the average latency based estimates (Default: stall time difference measurements)")
    parser.add_option("--sync-on-requests", action="store_true", dest="syncOnRequests", default=False, help="Use the number of finished memory requests to synchronize measurements")
    parser.add_option("--workload", action="store", dest="workload", default=".*", help="Only return workloads matching this pattern")
    parser.add_option("--plot-workload", action="store", dest="plotWorkload", default="", help="Plot IPC results for this workload")
    parser.add_option("--plot-optimal", action="store_true", dest="plotOptimal", default=False, help="Plot the optimal measurement results")

    opts, args = parser.parse_args()
    
    if len(args) != 2:
        fatal("command line error\nUsage: "+parser.usage)
    
    return opts,args

def getTracename(dir):
    return dir+"/"+TRACENAME

def getResultKey(wl, aloneCPUID, bmNames):
    return wl+"-"+str(aloneCPUID)+"-"+bmNames[aloneCPUID]

def computeNoMeasurementError(curCPUID, sharedSyncColID, sharedTrace, aloneSyncColID, aloneTrace, opts, period):
    errsum, errsqsum, numerrs = (0.0, 0.0, 0.0)
    
    sharedMWSColumn = sharedTrace.findColumnID("Max MLP MWS", curCPUID)
    sharedLatencyColumn = sharedTrace.findColumnID("Shared Avg Latency Measurement", curCPUID)
    sharedComInstColumn = sharedTrace.findColumnID("Committed Insts", curCPUID)
    sharedStallColumn = sharedTrace.findColumnID("Stall cycles", curCPUID)
    sharedNotStallColumn = sharedTrace.findColumnID("Run cycles", curCPUID)
    
    aloneMWSColumn = aloneTrace.findColumnID("Max MLP MWS", 0)
    aloneLatencyColumn = aloneTrace.findColumnID("Alone Avg Latency Measurement", 0)
    aloneIPCColumn = aloneTrace.findColumnID("Alone IPC Measurement", 0)
    
    aloneSyncVals = []
    aloneEstimates = []
    
    aloneTraceIndex = 0
    for aloneSyncVal in aloneTrace.data[aloneSyncColID]:
        
        closestSharedSyncIndex = tracefile.findLowestEndpoint(aloneSyncVal, sharedTrace.data[sharedSyncColID])
        
        interpolatedShLatency = tracefile.interpolate(aloneSyncVal, closestSharedSyncIndex, sharedTrace.data[sharedSyncColID], sharedTrace.data[sharedLatencyColumn])
        interpolatedShMWS = tracefile.interpolate(aloneSyncVal, closestSharedSyncIndex, sharedTrace.data[sharedSyncColID], sharedTrace.data[sharedMWSColumn])
        interpolatedShComInsts = tracefile.interpolate(aloneSyncVal, closestSharedSyncIndex, sharedTrace.getColumn(sharedSyncColID), sharedTrace.getColumn(sharedComInstColumn))
        interpolatedShStall = tracefile.interpolate(aloneSyncVal, closestSharedSyncIndex, sharedTrace.getColumn(sharedSyncColID), sharedTrace.getColumn(sharedStallColumn))
        interpolatedShNonStall = tracefile.interpolate(aloneSyncVal, closestSharedSyncIndex, sharedTrace.getColumn(sharedSyncColID), sharedTrace.getColumn(sharedNotStallColumn))
        
        aloneLatency = aloneTrace.getValue(aloneLatencyColumn, aloneTraceIndex)
        aloneMWS = aloneTrace.getValue(aloneMWSColumn, aloneTraceIndex)
        
        if interpolatedShLatency != 0 and interpolatedShMWS != 0 and aloneLatency != 0 and aloneMWS != 0:
            sharedFactor = interpolatedShLatency / interpolatedShMWS
            aloneFactor =  aloneLatency / aloneMWS
            adjustmentFactor = aloneFactor / sharedFactor        
            aloneStallEstimate = interpolatedShStall * adjustmentFactor
        else:
            aloneStallEstimate = interpolatedShStall
                
        aloneIPCEstimate = interpolatedShComInsts / (interpolatedShNonStall + aloneStallEstimate)
        aloneIPCMeasurement = aloneTrace.getValue(aloneIPCColumn, aloneTraceIndex)

        error = aloneIPCEstimate - aloneIPCMeasurement
        
        if opts.relativeErrors:
            assert aloneIPCMeasurement > 0
            error = error / aloneIPCMeasurement
            error = error * 100
    
        errsum += error
        errsqsum += error*error
        numerrs += 1
        
        aloneSyncVals.append(aloneSyncVal)
        aloneEstimates.append(aloneIPCEstimate)
    
        aloneTraceIndex += 1

    optimalTrace = TracefileData("")
    optimalTrace.buildFromLists(["Sync val", "No Measurement Error Estimate"], [aloneSyncVals, aloneEstimates])

    return optimalTrace, errsum, errsqsum, numerrs 

def computeIPCEstimateErrors(dirs, np, opts, period):
    
    results = {}
    
    aggErrSum = 0
    aggErrSqSum = 0
    aggNumErrs = 0
    
    aggMesSum = 0
    aggMesSumSq = 0
    aggMesErrs = 0
    
    for wl, shDirID, aloneDirIDs in dirs:
        
        if opts.verbose:
            print
            print "Processing workload "+wl+" with shared trace "+getTracename(shDirID)
        
        sharedTrace = TracefileData(getTracename(shDirID))
        
        try:
            sharedTrace.readTracefile()
        except IOError:
            if not opts.quiet:
                warn("File "+getTracename(shDirID)+" cannot be opened, skipping...")
            continue
        
        bmNames = workloads.getBms(wl, np, False)
        
        for aloneCPUID in range(len(aloneDirIDs)):
            if opts.verbose:
                print "Processing shared trace with alone trace " + getTracename(aloneDirIDs[aloneCPUID])
            
            
            if opts.syncOnRequests:
                sharedSyncColID = sharedTrace.findColumnID("Cummulative Requests", aloneCPUID)
            else:
                sharedSyncColID = sharedTrace.findColumnID("Cummulative Insts", aloneCPUID)    
            assert sharedSyncColID != -1
            if opts.useAvgLatEstimate:
                sharedAloneIPCID = sharedTrace.findColumnID("Avg Latency Based Alone IPC Estimate", aloneCPUID)
            else:
                sharedAloneIPCID = sharedTrace.findColumnID("Alone IPC Estimate", aloneCPUID)
            assert sharedAloneIPCID != -1
            
            
            aloneTrace = TracefileData(getTracename(aloneDirIDs[aloneCPUID]))
            aloneTrace.readTracefile()
            
            
            if opts.syncOnRequests:
                aloneSyncColID = aloneTrace.findColumnID("Cummulative Requests", 0)
            else:
                aloneSyncColID = aloneTrace.findColumnID("Cummulative Insts", 0)
            assert aloneSyncColID != -1
            
            aloneIPCColID = aloneTrace.findColumnID("Alone IPC Measurement", 0)
            assert aloneIPCColID != -1
            errsum, errsqsum, numerrs = tracefile.computeInterpolatedErrors(aloneTrace, 
                                                                            aloneSyncColID, 
                                                                            aloneIPCColID,
                                                                            sharedTrace,
                                                                            sharedSyncColID,
                                                                            sharedAloneIPCID,
                                                                            opts.relativeErrors,
                                                                            opts.quiet)
            if getResultKey(wl, aloneCPUID, bmNames) in results:
                fatal("IPC estimation only handles one set of workloads at the time")
            
            aggErrSum += errsum
            aggErrSqSum += errsqsum
            aggNumErrs += numerrs
            
            avgErr = computeMean(numerrs, errsum)
            rmsErr = computeRMS(numerrs, errsqsum)
            stddev = computeStddev(numerrs, errsum, errsqsum)
            
            syntheticTrace, noMesErrSum, noMesErrSqSum, noMesNumErrs = computeNoMeasurementError(aloneCPUID,
                                                                                                 sharedSyncColID,
                                                                                                 sharedTrace,
                                                                                                 aloneSyncColID,
                                                                                                 aloneTrace,
                                                                                                 opts,
                                                                                                 period)            
            aggMesSum += noMesErrSum
            aggMesSumSq += noMesErrSqSum
            aggMesErrs += noMesNumErrs
            
            avgMesErr = computeMean(noMesNumErrs, noMesErrSum)
            rmsMesErr = computeRMS(noMesNumErrs, noMesErrSqSum)
            mesStddev = computeStddev(noMesNumErrs, noMesErrSum, noMesErrSqSum)
            
            results[getResultKey(wl, aloneCPUID, bmNames)] = (avgErr, rmsErr, stddev, avgMesErr, rmsMesErr, mesStddev)
            
            if wl == opts.plotWorkload:
                useFiles = [aloneTrace, sharedTrace]
                useXCols = [(0,aloneSyncColID), (1,sharedSyncColID)]
                useYCols = [(0,aloneIPCColID), (1,sharedAloneIPCID)]
                
                if opts.plotOptimal:
                    useFiles.append(syntheticTrace)
                    useXCols.append( (2,0) )
                    useYCols.append( (2,1) )
                
                xColSpec = tracefile.buildColSpec(useXCols)
                yColSpec = tracefile.buildColSpec(useYCols)
                
                outfilename = "ipcest-"+getResultKey(wl, aloneCPUID, bmNames)+"-plot.pdf"
                
                if opts.syncOnRequests:
                    xlabel = "Number of Requests"
                else:
                    xlabel = "Number of Committed Instructions"
                
                xmax = max(aloneTrace.getColumn(aloneSyncColID))*1.05
                
                if not opts.quiet:
                    print "Plotting results in file "+outfilename
                tracefile.plot(useFiles, xColSpec, yColSpec, filename=outfilename, xlabel=xlabel, ylabel="IPC", xrange="0,"+str(xmax))
    
    if aggNumErrs > 0:
        aggAvgErr = computeMean(aggNumErrs, aggErrSum)
        aggRmsErr = computeRMS(aggNumErrs, aggErrSqSum)
        aggStddev = computeStddev(aggNumErrs, aggErrSum, aggErrSqSum)
        
        aggMesAvgErr = computeMean(aggMesErrs, aggMesSum)
        aggMesRmsErr = computeRMS(aggMesErrs, aggMesSumSq)
        aggMesStddev = computeStddev(aggMesErrs, aggMesSum, aggMesSumSq)
        
    else:
        aggAvgErr = float("inf")
        aggRmsErr = float("inf")
        aggStddev = float("inf")
        
        aggMesAvgErr = float("inf") 
        aggMesRmsErr = float("inf")
        aggMesStddev = float("inf")
        
    return results, (aggAvgErr, aggRmsErr, aggStddev, aggMesAvgErr, aggMesRmsErr, aggMesStddev)
        

def printResults(results, opts):
    wlbms = results.keys()
    wlbms.sort()
    
    lines = []
    if opts.relativeErrors:
        lines.append(["",
                      "Rel Average Error (%)",
                      "Rel RMS Error (%)",
                      "Rel STD (%)",
                      "OM Rel Average Error (%)",
                      "OM Rel RMS Error (%)",
                      "OM Rel STD (%)",])
    else:
        lines.append(["",
                      "Average Error",
                      "RMS Error",
                      "Standard Deviation",
                      "OM Average Error",
                      "OM RMS Error",
                      "OM Standard Deviation"])
    justify = [True, False, False, False, False, False, False]
    
    for key in wlbms:
        avgErr, rmsErr, stddev, mesAvg, mesRMS, mesStddev= results[key]
        line = [key,
                numberToString(avgErr, opts.decimals),
                numberToString(rmsErr, opts.decimals),
                numberToString(stddev, opts.decimals),
                numberToString(mesAvg, opts.decimals),
                numberToString(mesRMS, opts.decimals),
                numberToString(mesStddev, opts.decimals)]
        lines.append(line)
        
    printData(lines, justify, sys.stdout, opts.decimals)

def main():

    opts,args = parseArgs()
    try:
        np = int(args[0])
    except:
        fatal("Number of CPUs must be an integer")
    
    try:
        period = int(args[1])
    except:
        fatal("Sample period must be an integer")
    
    if not opts.quiet:
        print
        print "Alone IPC Prediction Accuracy Estimation"
        print
    
    dirs = getSingleParamExperimentDirs(np, opts.includeParams, workload=opts.workload)
    results, aggRes = computeIPCEstimateErrors(dirs, np, opts, period)
    
    if opts.printAll:
        printResults(results, opts)
    else:
        aggavg, aggrms, aggstd, aggMesAvg, aggMesRMS, aggMesStd = aggRes
        
        print
        if opts.relativeErrors:
            print "Aggregate Relative Errors (in %):"
        else:
            print "Aggregate Absolute Errors:"
        print ("Average error:            %."+str(opts.decimals)+"f") % aggavg
        print ("RMS error:                %."+str(opts.decimals)+"f") % aggrms
        print ("Error standard deviation: %."+str(opts.decimals)+"f") % aggstd
        print
        if opts.relativeErrors:
            print "Relative Errors without Optimal Measurements (in %):"
        else:
            print "Aggregate Absolute Errors with Optimal Measurements:"
        print ("Average error:            %."+str(opts.decimals)+"f") % aggMesAvg
        print ("RMS error:                %."+str(opts.decimals)+"f") % aggMesRMS
        print ("Error standard deviation: %."+str(opts.decimals)+"f") % aggMesStd
        
    

if __name__ == '__main__':
    main()