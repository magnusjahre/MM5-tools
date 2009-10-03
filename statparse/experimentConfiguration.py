
import deterministic_fw_wls as workloads

__metaclass__ = type

singleWlID = "single"
NO_SIMPOINT_VAL = -1

def generateExpID():
    if not "static" in dir(generateExpID):
        generateExpID.static = 0
    generateExpID.static += 1
    return generateExpID.static
    
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
    
    def compareTo(self, otherConfig):
        
        isWl = True
        
        if otherConfig.np != -1:
            if otherConfig.np != self.np:
                isWl = False
        
        if otherConfig.benchmark != "*":
            if otherConfig.benchmark != self.benchmark:
                isWl = False
        
        if otherConfig.workload != "*":
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
