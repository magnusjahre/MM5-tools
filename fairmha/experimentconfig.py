
import sys
import os
import copy

import workloadfiles
from workloadfiles.workloads import Workloads
from workloadfiles.workloads import specnames
from workloadfiles.workloads import spec2006names
workloads = Workloads() 


class ExperimentConfiguration:
    
    noBMIndentifier = "b"
    noWlIdentifier = "w"
    
    binaryPath = ""
    configPath = ""
    simticks = 0
    
    fixedSimulatorArguments = {}
    variableSimulatorArguments = {}
    
    fixedSingleCoreArguments = {}
    variableSingleCoreArguments = {}
    
    singleProgramModeParams = {}
    singleProgramModeNotIssued = {}
    singleProgramModeIssuedSharedIDs = {}
    
    singleCoreVarArgs = {}
    
    workloads = {}
    
    typeToParamPos = {"np": 0,
                      "wl": 1,
                      "bm": 2,
                      "bmnum": 3,
                      "varargStart": 4}
    
    varArgNames = {}
    singleVarArgNames = {}
    
    specBenchmarks = [] 
    
    SUITE_ALL = 0
    SUITE_2000 = 1
    SUITE_2006 = 2
    
    def __init__(self, _root, _binaryPath, _configPath):
        self.binaryPath = _root +"/"+_binaryPath
        self.configPath = _root +"/"+_configPath
        self.simticks = -1
        self.baselineParameters = None
        for b in specnames:
            self.specBenchmarks.append(b+"0")
    
    """ Used for inhibiting the SPM benchmarks from iterating over the parameter space
    
        parameters - a list of (argument, value) pairs that identify values for the the 
        MPM variable arguments in SPM 
    """
    def setBaselineParameters(self, parameters):
        self.baselineParameters = parameters
    
    def setSimTicks(self, _simticks):
        self.simticks = _simticks

    def registerFixedArgument(self, argument, value):
        assert argument not in self.fixedSimulatorArguments
        self.fixedSimulatorArguments[argument] = value
    
    def registerFixedSingleCoreArgument(self, argument, value):
        assert argument not in self.fixedSingleCoreArguments
        self.fixedSingleCoreArguments[argument] = value
        
    def registerVariableArgument(self, argument, values):
        assert argument not in self.variableSimulatorArguments
        self.variableSimulatorArguments[argument] = values
    
    def registerVariableSingleCoreArgument(self, argument, values):
        assert argument not in self.variableSingleCoreArguments
        self.variableSingleCoreArguments[argument] = values
    
    def registerWorkload(self, np, type=None):
        
        if type == None:
            type = workloadfiles.workloads.ALL
        
        assert np not in self.workloads
        self.workloads[np] = workloads.getWorkloads(np, type)

    def registerWorkloadByType(self, np, wltype):
        if np not in self.workloads:
            self.workloads[np] = []
        
        for t in workloads.getWorkloadsByType(np, wltype):
            self.workloads[np].append(t)
                
    def registerWorkloadRange(self, np, ids):
        
        assert False, "registerWorkloadRange is deprecated"
        
        assert np not in self.workloads
        self.workloads[np] = []
        
        for i in ids:
            if i < 10:
                self.workloads[np].append("fair0"+str(i))
            else:
                self.workloads[np].append("fair"+str(i))
        
    def registerBenchmarks(self, memAddrParts, suite=SUITE_ALL):
        if suite == self.SUITE_2000:
            self.registerBenchmarksByName(specnames, memAddrParts)
        elif suite == self.SUITE_2006:
            self.registerBenchmarksByName(spec2006names, memAddrParts)
        else:
            bms = self.getAllBenchmarks()
            self.registerBenchmarksByName(bms, memAddrParts)
            
    def getAllBenchmarks(self):
        bms = []
        for b in specnames:
            bms.append(b)
        for b in spec2006names:
            bms.append(b)
        return bms
    
    def registerBenchmarksByName(self, bmnames, memAddrParts):
        """ Arguments:
                bmnames, list: names of spec benchmarks with 0 suffix, e.g ['ammp0', 'mesa0']
                memAddrParts, list: a list of the memory system to use, e.g. [4, 8]
        """
        
        assert 1 not in self.workloads
        self.workloads[1] = []
        for bm in bmnames:
            self.workloads[1].append(bm)
            
        self.registerVariableSingleCoreArgument("MEMORY-ADDRESS-PARTS", memAddrParts)
        self.registerFixedSingleCoreArgument("MEMORY-ADDRESS-OFFSET", 0)
    
    def generateAllArgumentCombinations(self, variableArguments):    
        
        if variableArguments == {}:
            return [[]]

        keys = variableArguments.keys()
        keys.sort()
        
        combinations = 1
        for k in keys:
            combinations *= len(variableArguments[k])
            
        periods = [combinations / len(variableArguments[keys[0]])]
        for i in range(len(keys))[1:]:
            periods.append(periods[i-1]/len(variableArguments[keys[i]]))
        
        paramCombinations = []
        for i in range(combinations):
            vals = []
            for j in range(len(keys)):
                index = i / periods[j] % len(variableArguments[keys[j]])
                vals.append( (keys[j], variableArguments[keys[j]][index]) )
            
            paramCombinations.append(vals)

        return paramCombinations
        
    def getParams(self, np, wl, bm, bmnum, varargs):
        params = ["" for i in range(len(self.typeToParamPos)-1)]
        params[self.typeToParamPos["np"]]    = np
        params[self.typeToParamPos["wl"]]    = wl
        params[self.typeToParamPos["bm"]]    = bm
        params[self.typeToParamPos["bmnum"]] = bmnum
        
        index = self.typeToParamPos["varargStart"]
        for arg, val in varargs:
            params.append(val)
            if np == 1:
                if index in self.singleVarArgNames:
                    assert self.singleVarArgNames[index] == arg
                else: 
                    self.singleVarArgNames[index] = arg
            else:
                if index in self.varArgNames:
                    assert self.varArgNames[index] == arg 
                else:
                    self.varArgNames[index] = arg
            index += 1
        return params
        
    def getParam(self, params, type):
        return params[self.typeToParamPos[type]]
    
    def getNamedParamVal(self, params, paramName):
        for index in self.varArgNames:
            if self.varArgNames[index] == paramName:
                return params[index]
        
        raise Exception("Parameter "+paramName+" not found")
    
    def getVarargsIdentifier(self, params):
        repr = ""
        for p in params[self.typeToParamPos["varargStart"]:]:
            repr += "-"+str(p)
        return repr[1:]
    
    def getVariableParameters(self, params):
        np = self.getParam(params, "np")
        if np == 1:
            nameStore = self.singleVarArgNames
        else:
            nameStore = self.varArgNames
        
        varparams = {}
        for i in range(self.typeToParamPos["varargStart"], len(params)):
            varparams[nameStore[i]] = params[i]
            
        return varparams
    
    def getUniqueIdentifier(self, params):
        filename = str(self.getParam(params, "np"))
        filename += "-"+str(self.getParam(params, "wl"))
        filename += "-"+str(self.getParam(params, "bm"))
        filename += "-"+str(self.getParam(params, "bmnum"))
        
        return filename+"-"+self.getVarargsIdentifier(params)
        
    def getFileIdentifier(self, params):
        return "res-"+self.getUniqueIdentifier(params)
        
    def makeArgument(self, argument, value):
        if value == None:
            return "-E"+argument
        return "-E"+argument+"="+str(value)
    
    def generateCommonCommands(self, args, np, workload, params, bm, bmid, siminsts, pmInstSampPath):
        
        if bmid == self.noBMIndentifier:
            args.append(self.makeArgument("NP", np))
            
            if workload != self.noWlIdentifier:
                args.append(self.makeArgument("BENCHMARK", workload))
            else:
                assert bm != self.noBMIndentifier
                args.append(self.makeArgument("BENCHMARK", bm))
                
            if self.simticks != -1:
                args.append(self.makeArgument("SIMULATETICKS", str(self.simticks)))
        else:
            assert siminsts
            args.append(self.makeArgument("NP", 1))
            args.append(self.makeArgument("BENCHMARK", bm))
            args.append(self.makeArgument("SIMINSTS", str(siminsts)))
            args.append(self.makeArgument("COMMIT-TRACE-INSTRUCTION-FILE", pmInstSampPath))
            args.append(self.makeArgument("MEMORY-ADDRESS-OFFSET", 0))
            
        args.append(self.makeArgument("STATSFILE", self.getFileIdentifier(params))+".txt")
        return args
    
    def getCommandlines(self, doSingleProgramMode=True):
        
        commandlines = []
        
        allCombs = self.generateAllArgumentCombinations(self.variableSimulatorArguments)
        
        sortedNps = self.workloads.keys()
        sortedNps.sort()
        for np in sortedNps:
            for wl in self.workloads[np]:

                if self.baselineParameters == None or np > 1:
                    
                    for varArgs in allCombs:
                        
                        if np > 1:
                            params = self.getParams(np, wl, self.noBMIndentifier, self.noBMIndentifier, varArgs)
                            command = self.getCommand(np, wl, params, self.noBMIndentifier, self.noBMIndentifier, 0, varArgs)
                            commandlines.append( (command, params) )
                            
                        else:
                            
                            allSingleCombs =  self.generateAllArgumentCombinations(self.variableSingleCoreArguments)
                            
                            for singleVarArgs in allSingleCombs:
                                for arg in varArgs:
                                    singleVarArgs.append(arg)
                                
                                singleParams = self.getParams(np, self.noWlIdentifier, wl, self.noBMIndentifier, singleVarArgs)
                                singleCommand = self.getCommand(np, self.noWlIdentifier, singleParams, wl, self.noBMIndentifier, 0, singleVarArgs)
                                commandlines.append( (singleCommand, singleParams) )
                                
                                bmname = self.getParam(singleParams, "bm")
                                if bmname not in self.singleCoreVarArgs:
                                    self.singleCoreVarArgs[bmname] = []
                                self.singleCoreVarArgs[bmname].append(singleVarArgs)    
                        
                        if doSingleProgramMode:
                            bms = workloads.getBms(wl,np)
                            sharedExpKey = self.getUniqueIdentifier(params)
                            assert sharedExpKey not in self.singleProgramModeParams
                            self.singleProgramModeParams[sharedExpKey] = {}
                            
                            for i in range(np):
                                self.singleProgramModeParams[sharedExpKey][i] = varArgs
                                aloneParams = self.getParams(np, wl, bms[i], i, varArgs)
                                aloneKey = self.getUniqueIdentifier(aloneParams)
                                self.singleProgramModeNotIssued[aloneKey] = True
                                
                else:
                    assert not doSingleProgramMode
                    
                    if "USE-SIMPOINT" in self.variableSimulatorArguments:
                        for simpoint in self.variableSimulatorArguments["USE-SIMPOINT"]:
                            paramCopy = copy.copy(self.baselineParameters)
                            paramCopy.append( ("USE-SIMPOINT", simpoint) )
                            
                            singleParams = self.getParams(np, self.noWlIdentifier, wl, self.noBMIndentifier, paramCopy)
                            singleCommand = self.getCommand(np, self.noWlIdentifier, singleParams, wl, self.noBMIndentifier, 0, paramCopy)
                            commandlines.append( (singleCommand, singleParams) )                    
                    else:
                        singleParams = self.getParams(np, self.noWlIdentifier, wl, self.noBMIndentifier, self.baselineParameters)
                        singleCommand = self.getCommand(np, self.noWlIdentifier, singleParams, wl, self.noBMIndentifier, 0, self.baselineParameters)
                        commandlines.append( (singleCommand, singleParams) )
        
        return commandlines
    
    def getPMInstSampCommandLines(self):
        commandlines = []
        
        allCombs = self.generateAllArgumentCombinations(self.variableSimulatorArguments)
        
        sortedNps = self.workloads.keys()
        sortedNps.sort()
        for np in sortedNps:
            for varArgs in allCombs:
                for wl in self.workloads[np]:
                    wlCPUID = 0
                    wlParams = self.getParams(np, wl, self.noBMIndentifier, self.noBMIndentifier, varArgs)
                    wlExpID = self.getFileIdentifier(wlParams)

                    for bm in workloads.getBms(wl, np, True):
                        
                        instSampFilePath = wlExpID+"/pm-sample-points-"+wl+"-"+str(wlCPUID)+"-"+bm+".txt"
                        if not os.path.exists(instSampFilePath):
                            print "Warning: Instruction sampling file not found, quitting private mode sample point generation"
                            print "         Checked path is "+instSampFilePath
                            return []
                        
                        instSampFile = open(instSampFilePath)
                        instSampPointStrings = instSampFile.readline().split(",")
                        instSampPoints = [int(p) for p in instSampPointStrings]
                        siminsts = max(instSampPoints)
                        
                        singleParams = self.getParams(np, wl, bm, wlCPUID, self.baselineParameters)
                        singleCommand = self.getCommand(np, self.noWlIdentifier, singleParams, bm, wlCPUID, siminsts, self.baselineParameters, "../"+instSampFilePath)
                        commandlines.append( (singleCommand, singleParams) ) 
                        
                        wlCPUID += 1

        return commandlines
    
    def getCommand(self, np, wl, params, bm, bmid, insts, varargs, pmInstSampPath=""):
        args = []        
        args = self.generateCommonCommands(args, np, wl, params, bm, bmid, insts, pmInstSampPath)
        
        for arg in self.fixedSimulatorArguments:
            if pmInstSampPath == "" and arg == "SIMINSTS":
                continue
            args.append(self.makeArgument(arg, self.fixedSimulatorArguments[arg]))
        
        if np == 1:
            for arg in self.fixedSingleCoreArguments:
                args.append(self.makeArgument(arg, self.fixedSingleCoreArguments[arg]))
        
        for arg, val in varargs:
            args.append(self.makeArgument(arg, val))
        
        
        command = self.binaryPath
        for a in args:
            command += " "+a
        command += " "+self.configPath+" &> simoutput.txt &"
        
        return command
    
    def getSPMCommand(self, wl, sharedParams, bmID, instCnt):
        spmSharedKey = self.getUniqueIdentifier(sharedParams)
        sharedNp = self.getParam(sharedParams, "np")
        
        aloneVarArgs = self.singleProgramModeParams[spmSharedKey][bmID]
        bmname = workloads.getBms(wl,sharedNp)[bmID]
        
        aloneParams = self.getParams(sharedNp, wl, bmname, bmID, aloneVarArgs)
        aloneID = self.getUniqueIdentifier(aloneParams)
        
        command = self.getCommand(sharedNp, wl, aloneParams, bmname, bmID, instCnt, aloneVarArgs)
        
        del self.singleProgramModeNotIssued[aloneID]
        
        if spmSharedKey not in self.singleProgramModeIssuedSharedIDs: 
            self.singleProgramModeIssuedSharedIDs[spmSharedKey] = True
        
        return command, aloneParams
    
    def getSPMParameters(self, sharedParams, wl, bmID):
        
        sharedNp = self.getParam(sharedParams, "np")
        
        if self.singleProgramModeParams == {}:
            bmname = workloads.getBms(wl,sharedNp,True)[bmID]
            sharedVarargs = self.getVariableParameters(sharedParams)
            
            if self.baselineParameters != None:
                aloneVarargList = self.baselineParameters
            else:
                aloneVarargList = None
                for varargList in self.singleCoreVarArgs[bmname]:
                    isEqual = True
                    for argname, argval in varargList:
                        if argname == "MEMORY-ADDRESS-PARTS":
                            continue
                        assert argname in sharedVarargs
                        if sharedVarargs[argname] != argval:
                            isEqual = False
                            
                    if isEqual:
                        assert aloneVarargList == None
                        aloneVarargList = varargList
                        
            outparams = self.getParams(1, self.noWlIdentifier, bmname, self.noBMIndentifier, aloneVarargList)
            
        else:
            bmname = workloads.getBms(wl,sharedNp)[bmID]
            spmSharedKey = self.getUniqueIdentifier(sharedParams)
            aloneVarArgs = self.singleProgramModeParams[spmSharedKey][bmID]
            outparams = self.getParams(sharedNp, wl, bmname, bmID, aloneVarArgs)
        
        return outparams
        
    
    def allSPMCommandsIssued(self):
        return self.singleProgramModeNotIssued != {}
    
    def SPMNotIssued(self, params):
        key = self.getUniqueIdentifier(params)
        return key not in self.singleProgramModeIssuedSharedIDs
    
    def issueFatalError(self, message):
        print "Fatal error in experiment config: "+message
        sys.exit()
        
