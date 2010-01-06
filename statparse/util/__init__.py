
from statparse.printResults import createSortedParamList, paramsToString
from statparse.tracefile.errorStatistics import ErrorStatistics
from statparse.tracefile.tracefileData import TracefileData, computeErrors, MalformedTraceFileException

import deterministic_fw_wls

import sys
import os
import re
from copy import deepcopy

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

def getNpExperimentDirs(np):
    if not os.path.exists("pbsconfig.py"):
        fatal("pbsconfig.py not found!")
    
    if np <= 1:
        fatal("getNpExperimentDirs only handles multi-core results")
    
    pbsconfig = __import__("pbsconfig")
    configobj = pbsconfig.config
    
    allparams = []
    experimentdirs = []
    for cmd, shparams in pbsconfig.commandlines:
        
        expNp = configobj.getParam(shparams, "np")
        if expNp != np:
            continue
        
        varparams = configobj.getVariableParameters(shparams)
        if varparams not in allparams:
            allparams.append(varparams)
        
        wl = configobj.getParam(shparams, "wl")
        
        sharedFileID = configobj.getFileIdentifier(shparams)
    
        aloneFileIDs = []
        for i in range(np):
            aparams = configobj.getSPMParameters(shparams, wl, i)
            aloneFileID = configobj.getFileIdentifier(aparams)
            aloneFileIDs.append(aloneFileID)
        
        experimentdirs.append( (wl, varparams, sharedFileID, aloneFileIDs) )
    
    sortedParams = createSortedParamList(allparams)
    sortedParamStrs = []
    for p in sortedParams:
        sortedParamStrs.append(paramsToString(p))
    
    return experimentdirs, sortedParamStrs

def getResultKey(wl, aloneCPUID, np, varparams):
    bmNames = deterministic_fw_wls.getBms(wl, np, False)
    
    prefix = wl+"-"
    postfix = str(aloneCPUID)+"-"+bmNames[aloneCPUID]
    if "USE-SIMPOINT" in varparams:
        prefix += "sp"+str(varparams["USE-SIMPOINT"])+"-"
    
    return prefix+postfix

def getVarparamKey(wl, aloneCPUID, np, varparams):
    paramcopy = deepcopy(varparams)
    if "USE-SIMPOINT" in paramcopy:
        warn("simpoint handling not tested")
        del paramcopy["USE-SIMPOINT"]
    
    paramstr = paramsToString(paramcopy)
    return paramstr

def findAllParams(dirs, np):
    allparams = []
    for wl, varparams, shDirID, aloneDirIDs in dirs:
        for i in range(np):
            varparamkey = getVarparamKey(wl, i, np, varparams)
            if varparamkey not in allparams:
                allparams.append(varparamkey)
                
    return allparams

""" Computes the deviation between an estimate and the actual value in tracefile columns

    dirs: the directories to examine
    np: number of processors
    getTracename: function with signature (string directory, int aloneCPUID, bool sharedMode)
    relative: use relative errors
    quiet: don't print output
    baselineFuc: function with signature (string shDirID, int aloneCPUID) that returns the tuple (filename, columnName)
"""
def computeTraceError(dirs, np, getTracename, relative, quiet, mainColumnName, otherColumnName, useCPUID, compareToAlone, baselineFunc = None):
    
    results = {}
    
    aggregateErrors = {}
    allParams = findAllParams(dirs, np)
    for p in allParams:
        aggregateErrors[p] = ErrorStatistics(relative) 
    
    for wl, varparams, shDirID, aloneDirIDs in dirs:
        
        for aloneCPUID in range(len(aloneDirIDs)):
            
            sharedTraceFilename = getTracename(shDirID, aloneCPUID, True)
            aloneTraceFilename = getTracename(aloneDirIDs[aloneCPUID], 0, False)
            
            if baselineFunc != None:
                baselineTraceFilename, baselineColumn = baselineFunc(shDirID, aloneCPUID)
            
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
            
            if baselineFunc != None:
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
                aloneTrace.readTracefile()
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