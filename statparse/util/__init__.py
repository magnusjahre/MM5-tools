
from statparse.printResults import createSortedParamList, paramsToString
from statparse.tracefile.errorStatistics import ErrorStatistics
from statparse.tracefile.tracefileData import TracefileData, computeErrors, MalformedTraceFileException

from workloadfiles.workloads import Workloads, isWorkloadType, typedWorkloadIdentifiers

import sys
import os
import re
from copy import deepcopy

from optparse import OptionParser
import optcomplete
import statparse.tracefile.errorStatistics as errorStats

NO_WORKLOAD_TYPE_FILTER = "all"

def fatal(message):
    print
    print "ERROR: "+message
    print
    sys.exit(-1)
    
def warn(message):
    print "Warning: "+message
    
    
def getSingleParamExperimentDirs(np, includeParams, **kwargs):
    if not os.path.exists("pbsconfig.py"):
        fatal("pbsconfig.py not found!")
    
    pbsconfig = __import__("pbsconfig")
    configobj = pbsconfig.config

    paramDict = {}
    if includeParams != "":
        import statparse.experimentConfiguration as expconf
        paramDict, paramSpec = expconf.parseParameterString(includeParams)

    if "workload" in kwargs:
        workloadPattern = kwargs["workload"]
    else:
        workloadPattern = ".*"

    experimentdirs = []
    for cmd, shparams in pbsconfig.commandlines:
        
        expNp = configobj.getParam(shparams, "np")
        if expNp != np:
            continue
        
        includeDirs = True
        for includeParam in paramDict:
            paramval = configobj.getNamedParamVal(shparams, includeParam)
            if paramval != paramDict[includeParam]:
                includeDirs = False
        
        wl = configobj.getParam(shparams, "wl")
        if includeDirs and re.search(workloadPattern, wl):
            
            sharedFileID = configobj.getFileIdentifier(shparams)
    
            aloneFileIDs = []
            for i in range(np):
                aparams = configobj.getSPMParameters(shparams, wl, i)
                aloneFileID = configobj.getFileIdentifier(aparams)
                aloneFileIDs.append(aloneFileID)
            
            experimentdirs.append( (wl, sharedFileID, aloneFileIDs) )
    
    return experimentdirs

def getPrivateModeDirs():
    if not os.path.exists("pbsconfig.py"):
        fatal("pbsconfig.py not found!")
    
    pbsconfig = __import__("pbsconfig")
    configobj = pbsconfig.config
    
    dirs = []
    
    for cmd, shparams in pbsconfig.privModeCommandlines:
        dirs.append(configobj.getFileIdentifier(shparams))
        
    return dirs

def getSingleCoreExpDirs():
    if not os.path.exists("pbsconfig.py"):
        fatal("pbsconfig.py not found!")
       
    pbsconfig = __import__("pbsconfig")
    configobj = pbsconfig.config
    
    experimentdirs = []
    for cmd, params in pbsconfig.commandlines:
        
        expNp = configobj.getParam(params, "np")
        if expNp != 1:
            raise Exception("getSingleCoreExpDirs() only handles single core experiments")
        
        varparams = configobj.getVariableParameters(params)
        benchmark = configobj.getParam(params, "bm")
        fileID = configobj.getFileIdentifier(params)

        experimentdirs.append( (benchmark, varparams, fileID) )
    
    allparams = findAllParams(experimentdirs, 1)
    allparams.sort()
    
    return experimentdirs, allparams           

def getNpExperimentDirs(np):
    if not os.path.exists("pbsconfig.py"):
        fatal("pbsconfig.py not found!")
    
    if np <= 1:
        fatal("getNpExperimentDirs only handles multi-core results")
    
    pbsconfig = __import__("pbsconfig")
    configobj = pbsconfig.config
    
    experimentdirs = []
    for cmd, shparams in pbsconfig.commandlines:
        
        expNp = configobj.getParam(shparams, "np")
        if expNp != np:
            continue
        
        varparams = configobj.getVariableParameters(shparams)
        varparamlist = configobj.getVariableParametersList(shparams)
        
        wl = configobj.getParam(shparams, "wl")
        sharedFileID = configobj.getFileIdentifier(shparams)
        
        aloneFileIDs = []
        if hasattr(pbsconfig, "privModeCommandlines") and pbsconfig.privModeCommandlines != []:
            wls = Workloads()
            bms = wls.getBms(wl, np, True)
            for i in range(np):
                aparams = configobj.getParams(np, wl, bms[i], i, varparamlist)
                aloneFileID = configobj.getFileIdentifier(aparams)
                aloneFileIDs.append(aloneFileID)
        else:
            for i in range(np):
                aparams = configobj.getSPMParameters(shparams, wl, i)
                if "USE-SIMPOINT" in varparams:
                    aparams.append(varparams["USE-SIMPOINT"])
                
                aloneFileID = configobj.getFileIdentifier(aparams)
                aloneFileIDs.append(aloneFileID)
        
        experimentdirs.append( (wl, varparams, sharedFileID, aloneFileIDs) )
    
    allparams = findAllParams(experimentdirs, np)
    allparams.sort()
    
    return experimentdirs, allparams

def getBenchmarkName(dirname):
    result = re.search("s6-[a-zA-Z0-9]+", dirname)
    if result:
        return result.group(0) 
    
    spec2000bm = dirname.split("-")[5]
    return spec2000bm[0:len(spec2000bm)-1]

def getSingleCoreResKey(bm):
    return bm

def getResultKey(wl, aloneCPUID, np, varparams):
    wls = Workloads()
    bmNames = wls.getBms(wl, np, False)
    
    prefix = wl+"-"
    postfix = str(aloneCPUID)+"-"+bmNames[aloneCPUID]
    if "USE-SIMPOINT" in varparams:
        prefix += "sp"+str(varparams["USE-SIMPOINT"])+"-"
    
    return prefix+postfix

def getSimpleVarparamKey(varparams):
    return getVarparamKey(None, -1, -1, varparams)

def getVarparamKey(wl, aloneCPUID, np, varparams):
    paramcopy = deepcopy(varparams)
    if "USE-SIMPOINT" in paramcopy:
        del paramcopy["USE-SIMPOINT"]
    
    return paramsToString(paramcopy)

def findAllParams(dirs, np):
    allparams = []
    for wl, varparams, shDirID, aloneDirIDs in dirs:
        for i in range(np):
            varparamkey = getVarparamKey(wl, i, np, varparams)
            if varparamkey not in allparams:
                allparams.append(varparamkey)
                
    return allparams

def computeSingleCoreTraceError(dirs, mainColumnName, otherColumnName, getTracename, relative, params):
    
    results = {}    
    aggregateErrors = {}
    
    for p in params:
        aggregateErrors[p] = ErrorStatistics(relative) 
    
    for bm, varparams, dirID in dirs:
        traceFileName = getTracename(dirID, 0, False)
        
        fileData = TracefileData(traceFileName)
        fileData.readTracefile()
        
        curStats = computeErrors(fileData, mainColumnName, fileData, otherColumnName, relative)
        
        reskey = getSingleCoreResKey(bm)
        paramkey = getSimpleVarparamKey(varparams)
        
        assert paramkey in aggregateErrors
        aggregateErrors[paramkey].aggregate(curStats)
            
        if reskey not in results:
            results[reskey] = {}
            
        assert paramkey not in results[reskey]
        results[reskey][paramkey] = curStats
    
    return results, aggregateErrors

def computePrivateTraceError(dirs, mainColumnName, otherColumnName, getTracename, relative):
    
    results = {}
    aggregateErrors = {}
    paramkey = "Alone"
    aggregateErrors[paramkey] = ErrorStatistics(relative)
    
    for dir in dirs:
        traceFileName = getTracename(dir, 0, False)
        
        actualFileData = TracefileData(traceFileName)
        actualFileData.readTracefile()
        
        estimateFileData = TracefileData(traceFileName)
        estimateFileData.readTracefile()
        
        curStats = computeErrors(actualFileData, mainColumnName, estimateFileData, otherColumnName, relative)
        
        reskey = getBenchmarkName(dir)
        
        aggregateErrors[paramkey].aggregate(curStats)
            
        if reskey not in results:
            results[reskey] = {}
        
        if paramkey in results[reskey]:
            results[reskey][paramkey].aggregate(curStats)
        else:
            results[reskey][paramkey] = curStats
    
    return results, aggregateErrors

""" Computes the deviation between an estimate and the actual value in tracefile columns

    dirs: the directories to examine
    np: number of processors
    getTracename: function with signature (string directory, int aloneCPUID, bool sharedMode)
    relative: use relative errors
    quiet: don't print output
    
    Keyword arguments
    baselineFunc: function with signature (string shDirID, int aloneCPUID) that returns the tuple (filename, columnName)
"""
def computeTraceError(dirs, np, getTracename, relative, quiet, mainColumnName, otherColumnName, useCPUID, compareToAlone, **kwargs):
    
    results = {}
    
    aggregateErrors = {}
    allParams = findAllParams(dirs, np)
    for p in allParams:
        aggregateErrors[p] = ErrorStatistics(relative) 
    
    onlyWlType = None
    if "filterType" in kwargs:
        if kwargs["filterType"] != NO_WORKLOAD_TYPE_FILTER:
            onlyWlType = kwargs["filterType"]
    
    for wl, varparams, shDirID, aloneDirIDs in dirs:
        
        if not isWorkloadType(wl, onlyWlType):
            continue
        
        for aloneCPUID in range(len(aloneDirIDs)):
            
            sharedTraceFilename = getTracename(shDirID, aloneCPUID, True)
            aloneTraceFilename = getTracename(aloneDirIDs[aloneCPUID], 0, False)
            
            if "baselineFunc" in kwargs:
                if kwargs["baselineFunc"] != None:
                    baselineTraceFilename, baselineColumn = kwargs["baselineFunc"](shDirID, aloneCPUID)
            
            if useCPUID:
                cpuID = aloneCPUID
            else:
                cpuID = -1
            
            sharedTrace = TracefileData(sharedTraceFilename)
        
            try:
                sharedTrace.readTracefile()
            except IOError:
                if not quiet:
                    warn("File "+sharedTraceFilename+" cannot be opened, skipping...")
                continue
            
            if "baselineFunc" in kwargs:
                if kwargs["baselineFunc"] != None:
                    aloneTrace = TracefileData(aloneTraceFilename)
                    aloneTrace.readTracefile()
                    
                    baselineTrace = TracefileData(baselineTraceFilename)
                    baselineTrace.readTracefile()
                
                    try:
                        curStats = computeErrors(aloneTrace, mainColumnName, sharedTrace, otherColumnName, relative, cpuID=cpuID, baselineTrace=baselineTrace, baselineColumnName=baselineColumn)
                    except MalformedTraceFileException:
                        warn("Malformed tracefile with baseline")
                        continue
            
            elif compareToAlone:
                aloneTrace = TracefileData(aloneTraceFilename)
                try:
                    aloneTrace.readTracefile()
                except IOError:    
                    warn("File "+aloneTraceFilename+" cannot be opened, skipping...")
                    continue
                
                try:
                    curStats = computeErrors(aloneTrace, mainColumnName, sharedTrace, otherColumnName, relative, cpuID=cpuID)
                except MalformedTraceFileException:
                    warn("Malformed tracefile for files "+sharedTraceFilename+" and "+aloneTraceFilename)
                    continue
            else:
                try:
                    curStats = computeErrors(sharedTrace, mainColumnName, sharedTrace, otherColumnName, relative, cpuID=cpuID)
                except MalformedTraceFileException:
                    warn("Malformed tracefile for file "+sharedTraceFilename)
                    continue            
            
            reskey = getResultKey(wl, aloneCPUID, np, varparams)
            paramkey = getVarparamKey(wl, aloneCPUID, np, varparams)
            
            assert paramkey in aggregateErrors
            aggregateErrors[paramkey].aggregate(curStats)
            
            if reskey not in results:
                results[reskey] = {}
            
            assert paramkey not in results[reskey]
            results[reskey][paramkey] = curStats
    
    return results, aggregateErrors

class CustomListCompleter:
    
    def __init__(self, lists):
        self.list = []
        for l in lists:
            for e in l:
                self.list.append(e)
        
    def __call__(self, pwd, line, point, prefix, suffix):
        return self.list

def parseUtilArgs(programName, commands):
    parser = OptionParser(usage=programName+" [options] np statistic [command]")

    printTypes= ["all", "statistics", "distribution"]

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--verbose", action="store_true", dest="verbose", default=False, help="Print extra progress output")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--print-type", action="store", dest="printType", default="all", help="Result print style to use (one of "+str(printTypes)+")")
    parser.add_option("--relative", action="store_true", dest="relativeErrors", default=False, help="Print relative errors (Default: absolute)")
    parser.add_option("--plot-box", action="store_true", dest="plotBox", default=False, help="Visualize data with box and whiskers plot")
    parser.add_option("--hide-outliers", action="store_true", dest="hideOutliers", default=False, help="Removes outliers from box and whiskers plot")
    parser.add_option("--all-error-file", action="store", dest="allErrorFile", default="", help="Write all errors to this file")
    parser.add_option("--only-type", action="store", dest="onlyType", default=NO_WORKLOAD_TYPE_FILTER, help="Only retrieve errors from this workload type. Type identifiers are "+str(typedWorkloadIdentifiers+[NO_WORKLOAD_TYPE_FILTER]))
    parser.add_option("--outfile", action="store", dest="outfile", default="", help="Write output to this file")   
    
    optcomplete.autocomplete(parser, CustomListCompleter([commands, errorStats.statNames]))
    opts, args = parser.parse_args()
    
    if len(args) < 2 or len(args) > 3:
        fatal("command line error\nUsage: "+parser.usage)
    
    if not errorStats.checkStatName(args[1]):
        fatal("Unknown statistic name. "+errorStats.getStatnameMessage()) 
    
    if len(args) == 3:
        if args[2] not in commands:
            fatal("Unknown command "+args[2]+", candidates are "+str(commands))
    
    if opts.printType not in printTypes:
        fatal("Print type needs to be one of "+str(printTypes))
    
    return opts,args

def readDataFile(datafile, columns, onlyWlType):
    header = datafile.readline().strip().split()
    data = []
    for l in datafile:
        rawline = l.strip().split()
        tmp = [rawline[0]]
        
        error = False
        for e in rawline[1:]:
            if e == "N/A":
                error = True
                continue
            elif e == "RM":
                error = True
                continue
            
            try:
                tmp.append(float(e))
            except:
                fatal("Parse error, cannot convert "+e+" to float")
        
        if not error:
            if onlyWlType != "":
                wlString = tmp[0].split("-")
                if wlString[1] != onlyWlType:
                    continue
            
            data.append(tmp)
    
    if len(header) != len(data[0])-1:
        fatal("Datafile parse error, header has length "+str(len(header))+", data length is "+str(len(data[0])))
    
    if columns != "":
        colstrs = columns.split(",")
        includelist = [float(s) for s in colstrs]
        
        newheader = []
        for i in range(len(header)):
            if i in includelist:
                newheader.append(header[i])
        
        newdata = []
        for l in data:
            newline = [l[0]]
            for i in range(len(header)):
                if i in includelist:
                    newline.append(l[i+1])
            newdata.append(newline)
        
        return newheader, newdata
    
    return header, data
