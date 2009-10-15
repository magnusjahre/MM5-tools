
import experimentConfiguration

def filterResults(configRes, np, params, wl, bm, memsys):
    filteredConfigs = {}
    for c in configRes:
        if np == c.np and params == c.parameters and wl == c.workload and bm == c.benchmark and memsys == c.memsys:
            assert c not in filteredConfigs
            filteredConfigs[c] = configRes[c]
            
    return filteredConfigs

def findAllParams(matchingConfigs):
    allparams = []
    for config in matchingConfigs:
        inList = False
        for p in allparams:
            if config.paramsAreEqual(p):
                inList = True
        if not inList:
            allparams.append(config.parameters)
        
    return allparams
                    

def findAllWorkloads(matchingConfigs):
    def getKey(config):
        if config.workload == experimentConfiguration.singleWlID:
            return None
        return config.workload
    return _findAllFromConfig(getKey, matchingConfigs)

def findAllBenchmarks(matchingConfigs):
    def getKey(config):
        return config.benchmark
    return _findAllFromConfig(getKey, matchingConfigs)

def findAllNPs(matchingConfigs):
    def getKey(config):
        return config.np
    return _findAllFromConfig(getKey, matchingConfigs)

def findAllMemsysNPs(matchingConfigs):
    def getKey(config):
        return config.memsys
    return _findAllFromConfig(getKey, matchingConfigs)
    
def _findAllFromConfig(paramFunction, matchingConfigs):
    allkeys = {}
    for config in matchingConfigs:
        thisKey = paramFunction(config) 
        if thisKey not in allkeys and thisKey != None:
            allkeys[thisKey] = True
            
    keys = allkeys.keys()
    keys.sort()
    return keys
