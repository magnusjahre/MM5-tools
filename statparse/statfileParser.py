
import re
import deterministic_fw_wls as workloads
import cPickle

from statparse.experimentConfiguration import ExperimentConfiguration

__metaclass__ = type

distKeySuffix = ".dist"

privateStatNames = ["detailedCPU", 
                    "L1dcaches", 
                    "L1icaches", 
                    "PointToPointLink",
                    "PrivateL2Cache"] 

PICKLERPROT = 2

class StatfileIndex():

    def __init__(self, modulename = ""):
        self.resultstore = {}
        self.configurations = []
        
        if modulename != "":
            infile = open(modulename+".pkl", "rb")
            self.resultstore = cPickle.load(infile)
            self.configurations = cPickle.load(infile)
            infile.close()
            
        self.privateStatPatterns = [re.compile(stat) for stat in privateStatNames]
        
    def addstat(self, statkey, configid, value):
        if statkey not in self.resultstore:
            self.resultstore[statkey] = {}
        
        assert configid not in self.resultstore[statkey]
        self.resultstore[statkey][configid] = value

    def addFile(self, statsfilename, orderfilename, np, wlOrBm, params = {}):
        
        if np > 1:
            wls = workloads.getBms(wlOrBm, np, True)
            order = self._findParseOrder(orderfilename)
            if len(order) != np:
                raise Exception("Malformed statistics dump order file for workload "+str(wlOrBm))
            
            configIDs = []
            for cpuid in order: 
                expConf = ExperimentConfiguration(np, params, wls[cpuid], wlOrBm)
                
                self.configurations.append(expConf)
                configIDs.append(expConf.experimentID)
                
            self._parseFile(statsfilename, configIDs)
        
        else:
            expConf = ExperimentConfiguration(np, params, wlOrBm)
            self.configurations.append(expConf)
            self._parseFile(statsfilename, [expConf.experimentID])
    
    def _retrieveValue(self, searchRes):
        assert len(searchRes.keys()) == 1
        tmp = searchRes[searchRes.keys()[0]]
        assert len(tmp.keys()) == 1
        return tmp[tmp.keys()[0]]
    
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
        currentPrivateStatPatterns = []
        distribDict = {}
        
        for l in statfile:
            
            # remove non-stat lines
            if l.startswith("---------- Begin"):
                
                for config in self.configurations:
                    if config.experimentID == configIDs[0]:
                        curConf = config
                        break
                
                curCPUID = curConf.getIDInWorkload()
                currentPrivateStatPatterns = [re.compile(stat+str(curCPUID)) for stat in privateStatNames]
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
                    if self._canAdd(l, currentPrivateStatPatterns):
                        self.addstat(self._findKeyWithoutLast(l)+distKeySuffix, configIDs[0], distribDict)
                else:
                    
                    vals = l.split()
                    if self._isInt(vals[0]):
                        assert self._isInt(vals[1])
                        distribDict[int(vals[0])] = int(vals[1])
                    else:
                        if self._isKey(vals[0]):
                            if self._isFloat(vals[1]):
                                distribDict[self._findLastKeyPart(l)] = float(vals[1])
                            else:
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
                        
            if not self._canAdd(l, currentPrivateStatPatterns):
                continue
                
            self._storeStat(l, configIDs[0])
                
        
        statfile.close()
    
    def _canAdd(self, line, currentPrivStatPats):
        
        for i in range(len(self.privateStatPatterns)):
            if self.privateStatPatterns[i].search(line):
                if not currentPrivStatPats[i].search(line):
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
        
        filename = modulename+".pkl"
        outfile = open(filename, "wb")
        
        cPickle.dump(self.resultstore, outfile, PICKLERPROT)
        cPickle.dump(self.configurations, outfile, PICKLERPROT)
        
        outfile.flush()
        outfile.close()
        
            