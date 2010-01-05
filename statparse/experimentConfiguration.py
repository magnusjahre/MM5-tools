
import deterministic_fw_wls as workloads
from statparse import stringToType

__metaclass__ = type

singleWlID = "single"
NO_SIMPOINT_VAL = -1
NO_NP_VAL = -1
NO_BM = "*"
NO_WL = "*"

def generateExpID():
    if not "static" in dir(generateExpID):
        generateExpID.static = 0
    generateExpID.static += 1
    return generateExpID.static

def buildMatchAllConfig():
    return ExperimentConfiguration(-1, {}, "*", "*")

def parseParameterString(paramString, params = None):
    """ Turns a colon and comma divided string into a valid params dictionary
    
        Note: Simpoint values are passed with parameter USE-SIMPOINT and memsys
        with MEMORY-ADDRESS-PARTS 
    
        Arguments:
            paramString, string: key1+val1:key2+val2:...
            params, dictionary: optional dictionary to add paramters to
                        format: simulator option name -> value 
        Returns:
            dictionary: simulator option name -> value
            tuple: (np, benchmark, workload)
    """
    
    if params == None:
        params = {}
    
    np = NO_NP_VAL
    bm = NO_BM
    wl = NO_WL
    
    paramlist = paramString.split(":")
    for pstr in paramlist:
        try:
            key,value = pstr.split("+")
        except:
            raise Exception("Could not parse parameter string "+paramString)
        if key == "NP":
            np = stringToType(value)
            if np == 1:
                wl = singleWlID
        elif key == "BENCHMARK":
            if value.startswith("fair"):
                wl = value
            else:
                wl = singleWlID
                bm = bm
        else:
            if key in params:
                raise Exception("Multiple values for same parameter is not supported")
            
            params[key] = stringToType(value)
    
    
    return params, (np, bm, wl)

def isSPB(suspectedSPBConfig, MPBConfig):
    """ Returns true if suspectedSPBConfig is the SPB config for the MPBConfig"""
    
    matchConfig = buildMatchAllConfig()
    matchConfig.copy(MPBConfig)
    matchConfig.np = 1
    matchConfig.workload = singleWlID
    matchConfig.parameters = {}
    
    return suspectedSPBConfig.compareTo(matchConfig)
    
def findCPUID(wl, bmname, np):
    tmpbms = workloads.getBms(wl, np, True)
    id = 0
    for tmpbm in tmpbms:
        if tmpbm == bmname:
            return id
        id += 1
    raise Exception("Benchmark not "+str(bmname)+" found in provided workload "+str(wl)+" ("+str(tmpbms)+")")
    return -1

class ExperimentConfiguration:
    
    def __init__(self, np, params, bm, wl=singleWlID, expID = -1, simpoint = NO_SIMPOINT_VAL, memsys = -1):
        
        self.np = np
        self.benchmark = bm
        self.workload = wl
        self.simpoint = simpoint
        
        if expID == -1:
            self.experimentID = generateExpID()
        else:
            self.experimentID = expID
        
        self.memsys = memsys
        self.parameters = {}
        for p in params:
            if p == "MEMORY-ADDRESS-PARTS":
                assert np == 1
                self.memsys = int(params[p])
            elif p == "USE-SIMPOINT":
                self.simpoint = int(params[p]) 
            else:
                self.parameters[p] = params[p]
        
        if self.memsys == -1:
            self.memsys = np
    
    def copy(self, oldconfig):
        self.np = oldconfig.np
        self.benchmark = oldconfig.benchmark
        self.workload = oldconfig.workload
        self.simpoint = oldconfig.simpoint
        self.experimentID = oldconfig.experimentID
        self.memsys = oldconfig.memsys
        self.parameters = oldconfig.parameters
    
    def compareTo(self, otherConfig):
        
        isWl = True
        
        if otherConfig.np != NO_NP_VAL:
            if otherConfig.np != self.np:
                isWl = False
        
        if otherConfig.benchmark != NO_BM:
            if otherConfig.benchmark != self.benchmark:
                isWl = False
        
        if otherConfig.workload != NO_WL:
            if otherConfig.workload != self.workload:
                isWl = False
        
        if otherConfig.simpoint != NO_SIMPOINT_VAL:
            if otherConfig.simpoint != self.simpoint:
                isWl = False
        
        for p in otherConfig.parameters:
            assert p in self.parameters
                    
            if otherConfig.parameters[p] != self.parameters[p]:
                isWl = False
        
        return isWl
    
    def paramsAreEqual(self, otherParams):
        for p in self.parameters:
            if p not in otherParams:
                return False
            
            if self.parameters[p] != otherParams[p]:
                return False
            
        return True
    
    def getInitCall(self):
        initstr = "ExperimentConfiguration("
        initstr += str(self.np)+","
        initstr += str(self.parameters)+","
        initstr += "'"+str(self.benchmark)+"',"
        initstr += "'"+str(self.workload)+"',"
        initstr += str(self.experimentID)+","
        initstr += str(self.simpoint)+","
        initstr += str(self.memsys)+")"
        return initstr
    
    def __str__(self):
        initstr = str(self.np)+"-"
        initstr += str(self.workload)+"-"
        initstr += str(self.benchmark)
        if self.np == 1:
            initstr += "-"+str(self.memsys)
        
        if self.simpoint != NO_SIMPOINT_VAL:
            initstr += "-"+str(self.simpoint)
        
        for p in self.parameters:
            initstr += "-"+str(self.parameters[p])
        
        return initstr
    
    def getIDInWorkload(self):
        if self.np == 1:
            return 0
        
        assert self.workload != "*"
        assert self.workload != singleWlID
        assert self.np != -1
        bms = workloads.getBms(self.workload, self.np, True)
        
        retindex = -1
        for i in range(len(bms)):
            if bms[i] == self.benchmark:
                assert retindex == -1
                retindex = i
        
        return retindex
