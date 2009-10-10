from statparse import experimentConfiguration

import sys
import simpoints3
import deterministic_fw_wls as workloads

from experimentConfiguration import ExperimentConfiguration

__metaclass__ = type

class StatResults():

    intpatterns = {"IC Entry":       ".*sum_ic_entry_interference.*",
                   "IC Transfer":    ".*sum_ic_transfer_interference.*",
                   "IC Delivery":    ".*sum_ic_delivery_interference.*",
                   "Bus Entry":      ".*sum_bus_entry_interference.*",
                   "Bus Queue":      ".*sum_bus_queue_interference.*",
                   "Bus Service":    ".*sum_bus_service_interference.*",
                   "Cache Capacity": ".*sum_cache_capacity_interference.*",
                   "Total":          ".*sum_roundtrip_interference.*",
                   "Requests":       ".*num_roundtrip_responses.*"}

    latpatterns = {"IC Entry":     ".*sum_ic_entry_latency.*",
                   "IC Transfer":  ".*sum_ic_transfer_latency.*",
                   "IC Delivery":  ".*sum_ic_delivery_latency.*",
                   "Bus Entry":    ".*sum_bus_entry_latency.*",
                   "Bus Queue":    ".*sum_bus_queue_latency.*",
                   "Bus Service":  ".*sum_bus_service_latency.*",
                   "Total":        ".*sum_roundtrip_latency.*",
                   "Requests":     ".*num_roundtrip_responses.*"}

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
    
    def evaluateFairnessEstimateAccuracy(self, np, wlname, memsys):

        if memsys == "RingBased":
            prefix = "PrivateL2Cache"
        elif memsys == "CrossbarBased":
            prefix = "L1[di]caches"
        else:
            raise Exception("unknown memory system")

        results = {}

        cpuID = 0
        for bm in workloads.getBms(wlname, np, True):
            sSearchConf = ExperimentConfiguration(np, {}, bm, wlname)
            aloneSearchConf = ExperimentConfiguration(1, {}, bm)
            
            sconfs = self.index.findConfiguration(sSearchConf)
            aconfs = self.index.findConfiguration(aloneSearchConf)
            assert len(sconfs) == 1 and len(aconfs) == 1
            
            for latpatname in self.latpatterns:
                spattern = prefix+str(cpuID)+self.latpatterns[latpatname]
                apattern = prefix+"0"+self.latpatterns[latpatname]
                sres = self.index.searchForValues(spattern, sconfs)
                ares = self.index.searchForValues(apattern, aconfs)
                
                if sconfs[0] not in results:
                    results[sconfs[0]] = {}
                
                if latpatname not in results[sconfs[0]]:
                    results[sconfs[0]][latpatname] = {}
                    
                results[sconfs[0]][latpatname]["slat"] = self.index._retrieveValue(sres)
                results[sconfs[0]][latpatname]["alat"] = self.index._retrieveValue(ares)
            
            for ipatname in self.intpatterns:
                
                pattern = prefix+str(cpuID)+self.intpatterns[ipatname]
                sint = self.index.searchForValues(pattern, sconfs)
                
                if sconfs[0] not in results:
                    assert ipatname == "Cache Capacity"
                    results[sconfs[0]] = {}
                
                if ipatname not in results[sconfs[0]]:
                    assert ipatname == "Cache Capacity"
                    results[sconfs[0]][ipatname] = {}
                
                assert sconfs[0] in results
                assert ipatname in results[sconfs[0]]
                
                results[sconfs[0]][ipatname]["sint"] = self.index._retrieveValue(sint) 
            
            cpuID += 1
        
        for conf in results:
            print
            print "Interference results for configuration "+str(conf)
            print
            
            outtext = [["Interference Type",
                        "Shared Latency",
                        "Shared Interference",
                        "Estimate", 
                        "Alone Latency",
                        "Absolute Error (cc)",
                        "Relative Error (%)"]]
            leftJustify = [True, False, False, False, False, False, False] 
            
            latnames = results[conf].keys()
            latnames.sort()
            
            for latname in latnames:
                estimate = "N/A"
                error = "N/A"
                slat = "N/A"
                alat = "N/A"
                relErr = "N/A"
                
                if latname != "Cache Capacity":
                    slat = results[conf][latname]["slat"]
                    alat = results[conf][latname]["alat"]
                    estimate = slat - results[conf][latname]["sint"]
                    error =  alat - estimate
                    if slat > 0:
                        relErr = (float(error) / float(slat))*100
                    
                outtext.append([latname,
                                str(slat),
                                str(results[conf][latname]["sint"]),
                                str(estimate),
                                str(alat),
                                str(error),
                                self._numberToString(relErr, 2)])
            self._print(outtext, leftJustify, sys.stdout)
        
    
    def printSampleSizeResults(self, resulttuple, decimalPlaces):
        errorAvg, errorStdDev, errorRMS, relErrorAvg, relErrorStdDev, relErrorRMS = resulttuple
        
        outtext = [["Type", "Avg Error", "Std Dev", "RMS", "Relative Avg Error", "Relative Std Dev", "Relative RMS"]]
        leftJustify = [True, False, False, False, False, False, False]
        
        assert len(errorAvg.keys()) == 1
        assert 1 in errorAvg
        
        keys = errorAvg[1].keys()
        keys.sort()
        
        for k in keys:
            line = [k]
            line.append(self._numberToString(errorAvg[1][k], decimalPlaces))
            line.append(self._numberToString(errorStdDev[1][k], decimalPlaces))
            line.append(self._numberToString(errorRMS[1][k], decimalPlaces))
            line.append(self._numberToString(relErrorAvg[1][k], decimalPlaces))
            line.append(self._numberToString(relErrorStdDev[1][k], decimalPlaces))
            line.append(self._numberToString(relErrorRMS[1][k], decimalPlaces))
            
            outtext.append(line)
        
        self._print(outtext, leftJustify, sys.stdout)
       
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
                if np == 1:
                    # 1 CPU experiments are interference-free baseline
                    continue
                
                for params in allParams:
                    for wl in allWls:
                        wlConfig = ExperimentConfiguration(np, params, "*", wl)
                        assert wlConfig not in aggregate
                        aggregate[wlConfig] = self._aggregateWorkloadResults(np, params, wl)

            if self.expMetric != None:
                aggregate = self._aggregateExperimentResults(aggregate, allNPs, allWls, allParams)
            
        self._printAggregate(aggregate, allNPs, allWls, allParams, outfile, decimals, wlMetric.doTablePrint)
            
    def _printAggregate(self, aggregate, allNPs, allWls, allParams, outfile, decimals, printAllCPUs):
        
        sortedParams = self._createSortedParamList(allParams)
        
        outdata = []
        titleLine = [""]
        leftJust = [True]
        for p in sortedParams:
            titleLine.append(self._paramsToString(p))
            leftJust.append(False)
            
        outdata.append(titleLine)
        
        allNPs.sort()
        allWls.sort()

        for np in allNPs:
            if np == 1:
                continue
        
            if self.expMetric == None:
                for wl in allWls:
                    outdata = self._addAggregatePrintElement(outdata, np, wl, sortedParams, aggregate, decimals, printAllCPUs)
            else:
                line = ["Aggregate"]
                for p in sortedParams:
                    for c in aggregate:
                        if p == c.parameters:
                            assert len(aggregate[c]) == 1
                            line.append(self._numberToString(aggregate[c][0], decimals))
                outdata.append(line)
                                    
        self._print(outdata, leftJust, outfile)
    
    def _addAggregatePrintElement(self, outdata, np, wl, sortedParams, aggregate, decimals, printAllCPUs):
        
        if self.aggregateSimpoints:
            simpoints = [experimentConfiguration.NO_SIMPOINT_VAL]
        else:
            simpoints = [i for i in range(simpoints3.maxk)]
            
        if printAllCPUs:
            cpus = [i for i in range(np)]
        else:
            cpus = [np]
            
        iterspace = []
        for s in simpoints:
            for c in cpus:
                iterspace.append( (s,c) )

        for simpoint, cpuID in iterspace:
            
            title = str(np)+"-"+str(wl)
            
            if simpoint != experimentConfiguration.NO_SIMPOINT_VAL:
                title += "-sp"+str(simpoint)
            if cpuID != np:
                tmpWl = workloads.getBms(wl, np, False)
                title += "-"+tmpWl[cpuID]

            line = [title]
            for params in sortedParams:
                found = False
                for config in aggregate:
                    if config.np == np and config.workload == wl and config.parameters == params:
                        assert not found
                        found = True
                        
                        if cpuID != np:
                            line.append(self._numberToString(aggregate[config][simpoint][cpuID], decimals))
                        else:
                            line.append(self._numberToString(aggregate[config][simpoint], decimals))
            outdata.append(line)
        return outdata

    def _paramsToString(self, params):
        sortedKeys = params.keys()
        sortedKeys.sort()
        
        retstr = ""
        isFirst = True
        for k in sortedKeys:
            if isFirst:
                isFirst = False
            else:
                retstr += "-"
            
            retstr += str(k)[0:3]+"-"+str(params[k])
            
        
        return retstr
    
    def _createSortedParamList(self, allParams):
        
        if allParams == [{}]:
            return allParams
        
        paramVals = {}
        
        for params in allParams:
            for p in params:
                if p not in paramVals:
                    paramVals[p] = []
                    
                if params[p] not in paramVals[p]:
                    paramVals[p].append(params[p])
        
        numCombs = 0
        lengths = {}
        for p in paramVals:
            paramVals[p].sort()
            numCombs += len(paramVals[p])
            lengths[p] = len(paramVals[p])
         
        sortedKeys = paramVals.keys()
        sortedKeys.sort()
        
        periods = [numCombs / lengths[sortedKeys[0]]]
        for i in range(len(sortedKeys))[1:]:
            periods.append(periods[i-1]/lengths[sortedKeys[i]])
        
        sortedParamVals = []
        for i in range(numCombs):
            params = {}
            for j in range(len(sortedKeys)):
                pos = i / periods[j] % lengths[sortedKeys[j]]
                params[sortedKeys[j]] = paramVals[sortedKeys[j]][pos]
            sortedParamVals.append(params)
                
        return sortedParamVals
        
    def _aggregateWorkloadResults(self, np, params, wl):
        nomMpAggregate, nomSpAggregate = self._computeWorkloadAggregate(self.noPatResults, np, params, wl)
        
        if self.denominatorResults != {}:
            denomMpAggregate, denomSpAggregate = self._computeWorkloadAggregate(self.noPatDenominatorResults, np, params, wl)
            mpAgg = self._computeRatio(nomMpAggregate, denomMpAggregate)
            spAgg = self._computeRatio(nomSpAggregate, denomSpAggregate)
        else:
            mpAgg, spAgg = nomMpAggregate, nomSpAggregate
        
        self.wlMetric.setValues(mpAgg, spAgg, np, wl)
        metval = self.wlMetric.computeMetricValue()
        return metval
    
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
                if c in configRes:
                    raise MultiplePatternError(results.keys(), results[p].keys())
                    
                configRes[c] = results[p][c]
        return configRes
        
    def _computeWorkloadAggregate(self, results, np, params, wl):
        
        bms = workloads.getBms(wl, np, True)
        
        mpAggregate = {}
        spAggregate = {}
        for bm in bms:
            filteredRes = self._filterResults(results, np, params, wl, bm, np)
            
            if self.aggregateSimpoints:
                mpAggregate = self._aggregateSimpoints(filteredRes, mpAggregate, bm)
            else:
                mpAggregate = self._createSimpointDict(filteredRes, mpAggregate, bm)
            
            if self.wlMetric.spmNeeded:
                singleRes = self._filterResults(results, 1, params, experimentConfiguration.singleWlID, bm, np)
                
                if singleRes == {}:
                    raise Exception("Single program mode results needed for metric '"+str(self.wlMetric)+"' but cannot be found")
                
                if self.aggregateSimpoints:
                    spAggregate = self._aggregateSimpoints(singleRes, spAggregate, bm)
                else:
                    spAggregate = self._createSimpointDict(singleRes, spAggregate, bm)
        
        return mpAggregate, spAggregate
        
    def _aggregateSimpoints(self, filteredRes, aggregate, bm):
        
        simpointdata = simpoints3.simpoints[bm]
        
        foundSimpoints = [False for i in range(simpoints3.maxk)]
        tmpAggregate = 0
        for i in range(simpoints3.maxk):
            for c in filteredRes:
                if c.simpoint == experimentConfiguration.NO_SIMPOINT_VAL:
                    raise Exception("Results must have simpoints when aggregate simpoints is used")
                if c.simpoint == i:
                    assert not foundSimpoints[i]
                    tmpAggregate += filteredRes[c] * simpointdata[i][simpoints3.PROBKEY]
                    foundSimpoints[i] = True
                    
        success = True
        for found in foundSimpoints:
            if not found:
                success = False
        
        if success:
            if experimentConfiguration.NO_SIMPOINT_VAL not in aggregate:
                aggregate[experimentConfiguration.NO_SIMPOINT_VAL] = {}
                
            assert bm not in aggregate[experimentConfiguration.NO_SIMPOINT_VAL]
            aggregate[experimentConfiguration.NO_SIMPOINT_VAL][bm] = tmpAggregate
        
        return aggregate
    
    def _createSimpointDict(self, filteredRes, aggregate, subkey):
        for config in filteredRes:
            
            if config.simpoint not in aggregate:
                aggregate[config.simpoint] = {}
                
            assert subkey not in aggregate[config.simpoint]
            aggregate[config.simpoint][subkey] = filteredRes[config]
        return aggregate
    
    def _aggregateExperimentResults(self, aggregate, allNPs, allWls, allParams):
        newAggregate = {}
        
        for np in allNPs:
            
            if np == 1 and allNPs != [1]:
                continue
            
            for params in allParams:
                self.expMetric.clearValues()
                for wl in allWls:
                    wlConfig = ExperimentConfiguration(np, params, "*", wl)
                    for c in aggregate:
                        if c.compareTo(wlConfig):
                            if len(aggregate[c]) > 1 and aggregate[c][0] != self.expMetric.errStr:
                                raise Exception("Experiment aggregation does only make sense with both workload aggregation and simpoint aggregation")
                            self.expMetric.addValue(aggregate[c][0], np)
                
                aggConfig = ExperimentConfiguration(np, params, "*")            
                newAggregate[aggConfig] = self.expMetric.computeMetricValue()
        
        return newAggregate
    
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
 
 
    def _filterResults(self, configRes, np, params, wl, bm, memsys):
        filteredConfigs = {}
        for c in configRes:
            if np == c.np and params == c.parameters and wl == c.workload and bm == c.benchmark and memsys == c.memsys:
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
            if config.workload == experimentConfiguration.singleWlID:
                return None
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
            if thisKey not in allkeys and thisKey != None:
                allkeys[thisKey] = True
                
        keys = allkeys.keys()
        keys.sort()
        return keys

class MultiplePatternError(Exception):
    
    def __init__(self, patterns, expkeys): 
        self.patterns = patterns
        self.expkeys = expkeys
        
    def __str__(self):
        retstr = "The same experiment key was found in multiple patterns, unifying will lose information\n\n"
        retstr += "Your query matched the following statistics:\n"
        for p in self.patterns:
            retstr += "- "+str(p)+"\n"
        retstr += "\nThe following keys matched:\n"
        for p in self.expkeys:
            retstr += "- "+str(p)+"\n"
        return retstr
