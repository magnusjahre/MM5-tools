
import sys
import deterministic_fw_wls as workloads

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
    
    workloads = {}
    
    typeToParamPos = {"np": 0,
                      "wl": 1,
                      "bm": 2,
                      "bmnum": 3,
                      "varargStart": 4}
    
    varArgNames = {}
    singleVarArgNames = {}
    
    specnames = ['gzip', 'vpr', 'gcc', 'mcf', 'crafty', 'parser', 'eon', 'perlbmk', 'gap', 'bzip', 'twolf', 'wupwise', 'swim', 'mgrid', 'applu', 'galgel', 'art', 'equake', 'facerec', 'ammp', 'lucas', 'fma3d', 'sixtrack' ,'apsi', 'mesa', 'vortex1']
    specBenchmarks = [] 
    
    def __init__(self, _root, _binaryPath, _configPath):
        self.binaryPath = _root +"/"+_binaryPath
        self.configPath = _root +"/"+_configPath
        self.simticks = -1
        for b in self.specnames:
            self.specBenchmarks.append(b+"0")
        
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
    
    def registerWorkload(self, np, firstnum, lastnum):
        
        assert np not in self.workloads
        self.workloads[np] = []
        
        for i in range(firstnum, lastnum+1):
            if i < 10:
                self.workloads[np].append("fair0"+str(i))
            else:
                self.workloads[np].append("fair"+str(i))
                
    def registerWorkloadRange(self, np, ids):
        assert np not in self.workloads
        assert 1 not in self.workloads
        self.workloads[np] = []
        
        for i in ids:
            if i < 10:
                self.workloads[np].append("fair0"+str(i))
            else:
                self.workloads[np].append("fair"+str(i))
        
    def registerBenchmarks(self, memAddrParts):
        self.registerBenchmarksByName(self.specBenchmarks, memAddrParts)
    
    def registerBenchmarksByName(self, bmnames, memAddrParts):
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
    
    def generateCommonCommands(self, args, np, workload, params, bm, bmid, siminsts):
        
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
            args.append(self.makeArgument("BENCHMARK", bm+"0"))
            args.append(self.makeArgument("SIMINSTS", str(siminsts)))
            args.append(self.makeArgument("MEMORY-ADDRESS-OFFSET", str(bmid)))
            args.append(self.makeArgument("MEMORY-ADDRESS-PARTS", str(np)))
            
        args.append(self.makeArgument("STATSFILE", self.getFileIdentifier(params))+".txt")
        return args
    
    def getCommandlines(self, doSingleProgramMode=True):
        
        commandlines = []
        
        allCombs = self.generateAllArgumentCombinations(self.variableSimulatorArguments)
        
        sortedNps = self.workloads.keys()
        sortedNps.sort()
        for np in sortedNps:
            for wl in self.workloads[np]:
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
        
        return commandlines
    
    def getCommand(self, np, wl, params, bm, bmid, insts, varargs):
        args = []        
        args = self.generateCommonCommands(args, np, wl, params, bm, bmid, insts)
        
        for arg in self.fixedSimulatorArguments:
            args.append(self.makeArgument(arg, self.fixedSimulatorArguments[arg]))
        
        if np == 1:
            for arg in self.fixedSingleCoreArguments:
                args.append(self.makeArgument(arg, self.fixedSingleCoreArguments[arg]))
        
        for arg, val in varargs:
            args.append(self.makeArgument(arg, val))
        
        
        command = self.binaryPath
        for a in args:
            command += " "+a
        command += " "+self.configPath+" &"
        
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
        bmname = workloads.getBms(wl,sharedNp)[bmID]
        spmSharedKey = self.getUniqueIdentifier(sharedParams)
        
        aloneVarArgs = self.singleProgramModeParams[spmSharedKey][bmID]
        
        return self.getParams(sharedNp, wl, bmname, bmID, aloneVarArgs)
        
    
    def allSPMCommandsIssued(self):
        return self.singleProgramModeNotIssued != {}
    
    def SPMNotIssued(self, params):
        key = self.getUniqueIdentifier(params)
        return key not in self.singleProgramModeIssuedSharedIDs
    
    def issueFatalError(self, message):
        print "Fatal error in experiment config: "+message
        sys.exit()
        
