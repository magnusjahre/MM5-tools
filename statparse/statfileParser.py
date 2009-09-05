
import deterministic_fw_wls as workloads
import re

__metaclass__ = type

singleWlID = "single"
distKeySuffix = ".dist"
detailedCPUName = "detailedCPU"

def generateExpID():
    if not "static" in dir(generateExpID):
        generateExpID.static = 0
    generateExpID.static += 1
    return generateExpID.static

class StatfileIndex():

    def __init__(self, modulename = ""):
        self.resultstore = {}
        self.configurations = []
        
        if modulename != "":
            storemod = __import__(modulename)
            self.resultstore = storemod.resultstore
            self.configurations = storemod.configurations
        
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
        curCPU = ""
        isLast = False
        for l in statfile:
            
            # remove non-stat lines
            if l.startswith("---------- Begin"):
                
                for config in self.configurations:
                    if config.experimentID == configIDs[0]:
                        curConf = config
                        break
                
                curCPU = detailedCPUName+str(curConf.getIDInWorkload())
                if len(configIDs) == 1:
                    isLast = True
                continue
            elif l.startswith("---------- End Simulation"):
                configIDs.pop(0)
                continue
            elif l.strip() == "":
                continue
            
            # handle distributions
            if inDistribution:
                if self._findLastKeyPart(l) == "end_dist":
                    inDistribution = False
                    if self._canAdd(l, curCPU):
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
                            
                continue
                
            elif self._findLastKeyPart(l) == "start_dist":
                inDistribution = True
                distribDict = {}
                continue
            
            # add stats for the current CPU
            if l.startswith(curCPU) or isLast:
                
                if not self._canAdd(l, curCPU):
                    continue
                
                self._storeStat(l, configIDs[0])
                
        
        statfile.close()
    
    def _canAdd(self, line, curCPU):
        if line.startswith(detailedCPUName):
            if not line.startswith(curCPU):
                return False
        return True
    
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
    
    def findConfiguration(self, searchConfig):
        matchingConfigs = []
        for config in self.configurations:
            if config.compareTo(searchConfig):
                matchingConfigs.append(config)
        return matchingConfigs
    
    def findDistribution(self, key, config):
        return self.findValue(key+distKeySuffix, config)
    
    def findValue(self, key, config):
        if key not in self.resultstore:
            return None
        
        if config.experimentID not in self.resultstore[key]:
            return None
            
        return self.resultstore[key][config.experimentID]
    
    def searchForValues(self, regexp, configs):
        keyPat= re.compile(regexp)
        
        matches = []
        for k in self.resultstore.keys():
            if keyPat.search(k):
                matches.append(k)
                
        result = {}
        for m in matches:
            result[m] = {}
            for c in configs:
                value = self.findValue(m, c)
                if value != None:
                    result[m][c] = value 
        
        return result
    
    def dumpIndex(self, modulename):
        
        filename = modulename+".py"
        
        outfile = open(filename, "w")
        
        print >> outfile, "from statparse.statfileParser import ExperimentConfiguration"
        
        print >> outfile, "resultstore = "+str(self.resultstore)
        
        if self.configurations == []:
            print >> outfile, "configurations = []"
        else:
            print >> outfile, "configurations = ["+self.configurations[0].getInitCall(),
            for c in self.configurations[1:]:
                print >> outfile, ", "+c.getInitCall(),
            print >> outfile, "]" 
        
        outfile.flush()
        outfile.close()
        
    
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
