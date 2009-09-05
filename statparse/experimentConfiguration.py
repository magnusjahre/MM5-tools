
import deterministic_fw_wls as workloads

__metaclass__ = type

singleWlID = "single"

def generateExpID():
    if not "static" in dir(generateExpID):
        generateExpID.static = 0
    generateExpID.static += 1
    return generateExpID.static

    
class ExperimentConfiguration:
    
    def __init__(self, np, params, bm, wl=singleWlID, expID = -1):
        
        self.np = np
        self.benchmark = bm
        self.workload = wl
        
        if expID == -1:
            self.experimentID = generateExpID()
        else:
            self.experimentID = expID
        
        self.parameters = {}
        for p in params:
            self.parameters[p] = params[p]
    
    
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
        
        for p in otherConfig.parameters:
            assert p in self.parameters
                    
            if otherConfig.parameters[p] != self.parameters[p]:
                isWl = False
        
        return isWl
    
    def getInitCall(self):
        initstr = "ExperimentConfiguration("
        initstr += str(self.np)+","
        initstr += str(self.parameters)+","
        initstr += "'"+str(self.benchmark)+"',"
        initstr += "'"+str(self.workload)+"',"
        initstr += str(self.experimentID)+")"
        return initstr
    
    def toString(self):
        return "ExperimentConfig.toString()"
    
    def getIDInWorkload(self):
        assert self.workload != "*"
        assert self.workload != singleWlID
        assert self.np != -1
        bms = workloads.getBms(self.workload, self.np)
        
        retindex = -1
        for i in range(len(bms)):
            if bms[i] == self.benchmark:
                assert retindex == -1
                retindex = i
        
        return retindex

