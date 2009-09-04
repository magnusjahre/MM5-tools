
import deterministic_fw_wls as workloads

__metaclass__ = type

singleWlID = "single"
distKeySuffix = ".dist"

def generateExpID():
    if not "static" in dir(generateExpID):
        generateExpID.static = 0
    generateExpID.static += 1
    return generateExpID.static

class StatfileIndex():

    def __init__(self):
        self.resultstore = {}
        self.configurations = []
        
    def addstat(self, statkey, configid, value):
        if statkey not in self.resultstore:
            self.resultstore[statkey] = {}
        
        assert configid not in self.resultstore[statkey]
        self.resultstore[statkey][configid] = value

    def addFile(self, statsfilename, orderfilename, np, workload, params = {}):
        
        if np > 1:
            wls = workloads.getBms(workload, np)
            order = self._findParseOrder(orderfilename)
            configIDs = []
            for cpuid in order:
                expConf = ExperimentConfiguration(np, params, wls[cpuid], workload)
                self.configurations.append(expConf)
                configIDs.append(expConf.experimentID)
                
            self._parseFile(statsfilename, configIDs)
        
        else:
            expConf = ExperimentConfiguration(np, params, workload)
            self.configurations.append(expConf)
            self._parseFile(statsfilename, [expConf.experimentID])
    
    def _findParseOrder(self, orderfilename):
        order = []
        orderfile = open(orderfilename)
        
        for line in orderfile:
            cpuid = int(line.split(";")[2])
            order.append(cpuid)
        
        orderfile.close()
        return order
    
    def _parseFile(self, filename, configIDs):
        statfile = open(filename)
        
        inDistribution = False
        for l in statfile:
            if l.startswith("---------- Begin"):
                continue
            elif l.startswith("---------- End Simulation"):
                configIDs.pop(0)
            elif l.strip() == "":
                continue
            elif inDistribution:
                if self._findLastKeyPart(l) == "end_dist":
                    inDistribution = False
                    self.addstat(self._findKeyWithoutLast(l)+distKeySuffix, configIDs[0], distribDict)
                else:
                    
                    vals = l.split()
                    if self._isInt(vals[0]):
                        assert self._isInt(vals[1])
                        distribDict[int(vals[0])] = int(vals[1])
                    else:
                        if self._isKey(vals[0]):
                            distribDict[self._findLastKeyPart(l)] = int(vals[1])
                        else:
                            name = vals[0]
                            for i in range(len(vals))[1:]:
                                if self._isInt(vals[i]):
                                    break
                                name += " "+vals[i]

                            distribDict[name] = int(vals[i])
                
            elif self._findLastKeyPart(l) == "start_dist":
                inDistribution = True
                distribDict = {}
            else:
                self._storeStat(l, configIDs[0])
                
        
        statfile.close()
        
    def _findLastKeyPart(self, line):
        return line.split()[0].split(".")[-1]
    
    def _findKeyWithoutLast(self, line):
        key = line.split()[0]
        keyparts = key.split(".")
        retkey = keyparts[0]
        for k in keyparts[1:-1]:
            retkey += "."+k 
        
        return retkey
        
    def _storeStat(self, line, configID):
        
        statkey, val = line.split()[0:2]
        
        if self._isInt(val):
            value = int(val)
        elif self._isFloat(val):
            value = float(val)
        else:
            # value is not int or float, not a valid statistic
            return
            
        self.addstat(statkey, configID, value) 
    
    def _isInt(self, valStr):
        try:
            int(valStr)
            return True
        except ValueError:
            return False
        
    def _isFloat(self, valStr):
        try:
            float(valStr)
            return True
        except ValueError:
            return False
        
    def _isKey(self, inStr):
        if inStr.find(".") != -1:
            return True
        return False
    
    def findConfiguration(self, np, params, bm, wl=singleWlID):
        for config in self.configurations:
            if config.isConfig(np, params, bm, wl):
                return config
        return None
    
    def findDistribution(self, key, config):
        return self.findValue(key+distKeySuffix, config)
    
    def findValue(self, key, config):
        if key not in self.resultstore:
            return None
        
        if config.experimentID not in self.resultstore[key]:
            return None
            
        return self.resultstore[key][config.experimentID]
    
class ExperimentConfiguration:
    
    def __init__(self, np, params, bm, wl=singleWlID):
        
        self.np = np
        self.benchmark = bm
        self.workload = wl
        
        self.experimentID = generateExpID()
        
        self.parameters = {}
        for p in params:
            self.parameters[p] = params[p]
            
    def isConfig(self, np, params, bm, wl):
        
        isWl = True
        
        if np != self.np:
            isWl = False
        if bm != self.benchmark:
            isWl = False
        if wl != self.workload:
            isWl = False
            
        for p in params:
            if p not in self.parameters:
                isWl = False
                continue
            
            if params[p] != self.parameters[p]:
                isWl = False
        
        return isWl