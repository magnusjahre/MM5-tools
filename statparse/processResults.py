
import experimentConfiguration

def filterResults(configRes, np, params, wl, bm, memsys):
    filteredConfigs = {}
    for c in configRes:
        if np == c.np and params == c.parameters and wl == c.workload and bm == c.benchmark and memsys == c.memsys:
            assert c not in filteredConfigs
            filteredConfigs[c] = configRes[c]
            
    return filteredConfigs

def filterResultsWithConfig(configRes, filterConfig):
    """ Removes the configuration that do not match filterConfig from configRes
    
        Arguments:
            configRes, dictionary: experiment configuration -> value
            filterConfig, ExperimentConfiguration object
            
        Returns:
            dictionary, ExperimentConfiguration -> value
    """
    filteredConfigs = {}
    for c in configRes:
        if c.compareTo(filterConfig):
            assert c not in filteredConfigs
            filteredConfigs[c] = configRes[c]
            
    return filteredConfigs
    

def filterConfigurations(allConfigs, filterConfig):
    """ Returns the list of configurations in allConfigs that matches the filterConfig"""
    retconfigs = []
    for c in allConfigs:
        if c.compareTo(filterConfig):
            assert c not in retconfigs
            retconfigs.append(c)
    return retconfigs
            

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

def addAllUnitNames(patternResults, quiet, np):
    """ Copies SPB patterns such that they are guarranteed to match their corresponding 
    MPM pattern names   
    
    Arguments:
        patternResults, dictionary: statistic name -> configuration -> statistic value
        quiet, bool: do not print output
        np, int: the number of processors
    
    Returns:
        dictionary: statistic name -> configuration -> statistic value
    """
    
    newPatterns = {}
    for pattern in patternResults:
        for config in patternResults[pattern]:
            if config.np == 1:
                
                splitted = pattern.split(".")
                curName = splitted[0]
                suffix = splitted[1:]
                if "0" in curName:
                    
                    newNames = []
                    for i in range(np):
                        newNames.append(curName.replace("0", str(i)))
                    
                    for newName in newNames:
                        newpat = newName
                        for s in suffix:
                            newpat += "."+s
                            
                        if newpat not in newPatterns:
                            newPatterns[newpat] = {}
                        
                        assert config not in newPatterns[newpat]
                        newPatterns[newpat][config] = patternResults[pattern][config]
                        
                    
    
    for p in newPatterns:
        if p not in patternResults:
            raise Exception("created new pattern that was not present in the original results")
        
        for c in newPatterns[p]:
            if c not in patternResults[p]:
                patternResults[p][c] = newPatterns[p][c]
                
    return patternResults
    


def matchSPBsToMPB(patternResults, quiet, np):
    """ Matches Multiprogram mode results with their Single Program Mode 
        counterparts. Only MPB results with np processors will be included 
    
    Arguments:
        patternResults, dictionary: statistic name -> configuration -> statistic value
    
    Returns:
        dictionary: MPB configuration -> statistic name -> "MPB" or "SPB" -> value
    """
    
    if not isinstance(np, int):
        raise Exception("Provided processor count np must be an integer")
    
    oneCoreFilterConfig = experimentConfiguration.buildMatchAllConfig()
    oneCoreFilterConfig.np = 1
    
    if not quiet:
        print "Matching Multiprogram Mode results with Single Program Mode results" 
    
    results = {}
    for statname in patternResults:
    
        if not quiet:
            print "Matching for statistic name "+statname
        
        oneCPUConfigs = filterConfigurations(patternResults[statname].keys(), oneCoreFilterConfig)
        
        for config in patternResults[statname]:
            if config.np != np:
                continue
            
            found = False
            for oneCPUConfig in oneCPUConfigs:
                if experimentConfiguration.isSPB(oneCPUConfig, config):
                    assert not found
                    results = _addConfigToMPBResults(results, config, statname, patternResults, oneCPUConfig)
                    found = True
            
            if not found:
                results = _addConfigToMPBResults(results, config, statname, patternResults)

    return results

def _addConfigToMPBResults(results, config, statname, patternResults, aloneConfig = None):
    if config not in results:
        results[config] = {}
    if statname not in results[config]:
        results[config][statname] = {}
    
    results[config][statname]["MPB"] = patternResults[statname][config]
    if aloneConfig != None:
        results[config][statname]["SPB"] = patternResults[statname][aloneConfig]
    else:
        results[config][statname]["SPB"] = {}
    
    return results