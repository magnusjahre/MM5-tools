
import sys
import simpoints3
import deterministic_fw_wls as workloads

from experimentConfiguration import ExperimentConfiguration

__metaclass__ = type

class StatSearch():

    def __init__(self, index, searchConfig):
        self.index = index
        self.searchConfig = searchConfig
        
        self.numSimpoints = simpoints3.maxk
        
        # search members
        self.results = {}
        self.noPatResults = {}
        self.denominatorResults = {}
        self.noPatDenominatorResults = {}
        self.matchingConfigs = []
        
        # members used for result aggregation
        self.wlMetric = None
        self.expMetric = None
        self.useSimpoints = False
        self.relToColumn = -1

    def plainSearch(self, nomPat, denomPat = ""):
        self.matchingConfigs = self.index.findConfiguration(self.searchConfig)
        self.results = self.index.searchForValues(nomPat, self.matchingConfigs)
        self.noPatResults = self._removePatternsFromResult(self.results)
        if denomPat != "":
            self.denominatorResults = self.index.searchForValues(denomPat, self.matchingConfigs)
            self.noPatDenominatorResults = self._removePatternsFromResult(self.denominatorResults)

    def printAllResults(self, decimalPlaces, outfile):
        self._simplePrint(self.results, decimalPlaces, outfile)
        if self.denominatorResults != {}:
            print >> outfile, ""
            self._simplePrint(self.denominatorResults, decimalPlaces, outfile)
        
    def _simplePrint(self, results, decimalPlaces, outfile):
        statkeys = results.keys()
        statkeys.sort()
    
        outtext = [["Stats key", "Configuration", "Value"]]
        leftJustify = [True, True, False]
    
        for statkey in statkeys:
            for config in results[statkey]:
                line = []
                line.append(statkey)
                line.append(str(config))
                line.append(self._numberToString(results[statkey][config], decimalPlaces))
                outtext.append(line) 
                
        self._print(outtext, leftJustify, outfile)
    
    def printAggregateResults(self, decimals, outfile, wlMetric, expMetric, aggregateSimpoints, relToColumn):
        
        self.wlMetric = wlMetric
        self.expMetric = expMetric
        self.aggregateSimpoints = aggregateSimpoints
        self.relToColumn = relToColumn
        
        allNPs = self._findAllNPs()
        allParams = self._findAllParams()
        allWls = self._findAllWorkloads()
        
        assert(len(allNPs) > 0)
        
        aggregate = {}
        if allNPs == [1]:
            assert allWls == []
            raise Exception("Single CPU experiment aggregation not implemented")
        else:
            for np in allNPs:
                for params in allParams:
                    for wl in allWls:
                        wlConfig = ExperimentConfiguration(np, params, "*", wl)
                        aggregate[wlConfig] = self._aggregateWorkloadResults(np, params, wl)
                                    
            if self.expMetric != None:
                self._aggregateExperimentResults()
    
        print >> outfile, "Temporary print for aggregate"
        for config in aggregate:
            print >> outfile, str(config), aggregate[config]
    
    def _aggregateWorkloadResults(self, np, params, wl):
        nomMpAggregate, nomSpAggregate = self._computeWorkloadAggregate(self.noPatResults, np, params, wl)
        
        if self.denominatorResults != {}:
            denomMpAggregate, denomSpAggregate = self._computeWorkloadAggregate(self.noPatDenominatorResults, np, params, wl)
            mpAgg = self._computeRatio(nomMpAggregate, denomMpAggregate)
            spAgg = self._computeRatio(nomSpAggregate, denomSpAggregate)
        else:
            mpAgg, spAgg = nomMpAggregate, nomSpAggregate

        self.wlMetric.setValues(mpAgg, spAgg)
        return self.wlMetric.computeMetricValue()
    
    def _computeRatio(self, nominator, denominator):
        ratio = {}
        for simpoint in nominator:
            ratio[simpoint] = {}
            assert simpoint in denominator
            for bm in nominator[simpoint]:
                assert bm in denominator[simpoint]
                ratio[simpoint][bm] = float(nominator[simpoint][bm]) / float(denominator[simpoint][bm])
        return ratio
    
    def _removePatternsFromResult(self, results):
        configRes = {}
        for p in results:
            for c in results[p]:
                assert c not in configRes
                configRes[c] = results[p][c]
        return configRes
        
    def _computeWorkloadAggregate(self, results, np, params, wl):
        
        bms = workloads.getBms(wl, np)
        
        mpAggregate = {}
        spAggregate = {}
        for bm in bms:
            filteredRes = self._filterResults(results, np, params, wl, bm)
            
            if self.aggregateSimpoints:
                mpAggregate = self._aggregateSimpoints(filteredRes)
            else:
                mpAggregate = self._createSimpointDict(filteredRes, mpAggregate, bm)
                
            if self.wlMetric.spmNeeded:
                singleRes = self._filterResults(results, 1, params, wl, bm)
                if singleRes == {}:
                    raise Exception("Single program mode results needed for metric '"+str(self.wlMetric)+"' but cannot be found")
                
                if self.aggregateSimpoints:
                    spAggregate = self._aggregateSimpoints(singleRes)
                else:
                    mpAggregate = self._createSimpointDict(filteredRes, spAggregate, bm) 
        
        return mpAggregate, spAggregate
        
    def _aggregateSimpoints(self, filteredRes):
        raise Exception("Simpoint aggregation not implemented")   
    
    def _createSimpointDict(self, filteredRes, aggregate, subkey):
        for config in filteredRes:
            if config.simpoint not in aggregate:
                aggregate[config.simpoint] = {}
            assert subkey not in aggregate[config.simpoint]
            aggregate[config.simpoint][subkey] = filteredRes[config]
        return aggregate
    
    def _aggregateExperimentResults(self):
        raise Exception("Experiment aggregation not implemented")
    
    def printAggregateDistribution(self, decimalPlaces, outfile):
        
        for statkey in self.results:
        
            print >> outfile, ""
            print >> outfile, "Aggregate distribution for pattern "+statkey
        
            aggDistrib = {}
            for config in self.results[statkey]:
                curDistrib = self.results[statkey][config]
                
                for key in curDistrib:
                    if key not in aggDistrib:
                        aggDistrib[key] = curDistrib[key]
                    else:
                        aggDistrib[key] += curDistrib[key]
                            
            outtext = [["Key", "Value"]]
            leftJustify = [True, False]
            
            
            
            distKeys = aggDistrib.keys()
            distKeys.sort()
            for d in distKeys:
                line = [self._numberToString(d, decimalPlaces)]
                line.append(self._numberToString(aggDistrib[d], decimalPlaces))
                outtext.append(line)
            
            self._print(outtext, leftJustify, outfile)
    
    def printDistributionsToFile(self, outfile):
        if outfile == sys.stdout:
            outfile = open("distributions.py", "w")
        
        outdict = {}
        for statkey in self.results:
            
            outdict[statkey] = {}
            for config in self.results[statkey]:
                distrib = self.results[statkey][config]
                configKey = config.toString()
                outdict[statkey][configKey] = distrib
             
        print >> outfile, ""
        print >> outfile, "distributions = "+str(outdict)
        
        outfile.flush()
        outfile.close()
    
    def _numberToString(self, number, decimalPlaces):
        if type(number) == type(int()):
            return str(number)
        elif type(number) == type(float()):
            return ("%."+str(decimalPlaces)+"f") % number
        elif type(number) == type(dict()):
            return "Distribution"
        elif type(number) == type(str()):
            return number
        
        raise TypeError("number is not int or float")
    
    def _print(self, textarray, leftJust, outfile):
        if textarray == []:
            raise ValueError("array cannot be empty")
        if textarray[0] == []:
            raise ValueError("array cannot be empty")
        if len(textarray[0]) != len(leftJust):
            raise ValueError("justification array must be the same with as the rows")
        
        padding = 2
        
        colwidths = [0 for i in range(len(textarray[0]))]
        
        for i in range(len(textarray)):
            for j in range(len(textarray[i])):
                if type(textarray[i][j]) != type(str()):
                    raise TypeError("all printed elements must be strings")
                
                if len(textarray[i][j]) + padding > colwidths[j]:
                    colwidths[j] = len(textarray[i][j]) + padding
        
        
        for i in range(len(textarray)):
            for j in range(len(textarray[i])):
                if leftJust[j]:
                    print >> outfile, textarray[i][j].ljust(colwidths[j]),
                else:
                    print >> outfile, textarray[i][j].rjust(colwidths[j]),
            print >> outfile, ""
 
 
    def _filterResults(self, configRes, np, params, wl, bm):
        filteredConfigs = {}
        for c in configRes:
            if np == c.np and params == c.parameters and wl == c.workload and bm == c.benchmark:
                assert c not in filteredConfigs
                filteredConfigs[c] = configRes[c]
                
        return filteredConfigs
 
    def _findAllParams(self):
        allparams = []
        for config in self.matchingConfigs:
            inList = False
            for p in allparams:
                if config.paramsAreEqual(p):
                    inList = True
            if not inList:
                allparams.append(config.parameters)
            
        return allparams
                        
    
    def _findAllWorkloads(self):
        def getKey(config):
            return config.workload
        return self._findAllFromConfig(getKey)
    
    def _findAllNPs(self):
        def getKey(config):
            return config.np
        return self._findAllFromConfig(getKey)
        
    def _findAllFromConfig(self, paramFunction):
        allkeys = {}
        for config in self.matchingConfigs:
            thisKey = paramFunction(config) 
            if thisKey not in allkeys:
                allkeys[thisKey] = True
                
        keys = allkeys.keys()
        keys.sort()
        return keys
        