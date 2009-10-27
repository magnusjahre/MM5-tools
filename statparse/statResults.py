from statparse import experimentConfiguration
from statparse.metrics import NoAggregation

import processResults
import printResults

import sys
import simpoints.simpoints as simpoints
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

    def __init__(self, index, searchConfig, aggregatePatterns, quiet, baseconfig = None, createNoPatResults = True):
        self.index = index
        self.searchConfig = searchConfig
        
        self.numSimpoints = simpoints.maxk
        
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

        self.aggregatePatterns = aggregatePatterns
        self.aggregatePatternsWarnIssued = False
        
        self.quiet = quiet
        self.baseconfig = baseconfig
        
        self.createNoPatResults = createNoPatResults

    def plainSearch(self, nomPat, denomPat = ""):
        self.matchingConfigs = self.index.findConfiguration(self.searchConfig)
        self.results = self.index.searchForValues(nomPat, self.matchingConfigs)
        if self.createNoPatResults:
            self.noPatResults = self._removePatternsFromResult(self.results)
        if denomPat != "":
            self.denominatorResults = self.index.searchForValues(denomPat, self.matchingConfigs)
            if self.createNoPatResults:
                self.noPatDenominatorResults = self._removePatternsFromResult(self.denominatorResults)

    def searchForPatterns(self, patterns):
        """ Searches for patters given in a list and returns a dictionary with the results
            If the the statistic names returned by two patterns overlap, an exception will be
            thrown.  
        
            Arguments:
            patterns, list: reg-exp patterns
        
            Returns:
            dictionary: statistic name -> configuration -> statistic value
        """
        results = {}
        
        allConfigs = self.index.findConfiguration(self.searchConfig)
        for p in patterns:
            if not self.quiet:
                print "Searching for pattern "+p
            tmpres = self.index.searchForValues(p, allConfigs)
            
            for statname in tmpres:
                
                if statname in results:
                    raise Exception("Statistic name "+str(statname)+" returned by multiple patterns")
                results[statname] = tmpres[statname]
        
        return results

    def printAllResults(self, decimalPlaces, outfile):
        printResults.simplePrint(self.results, decimalPlaces, outfile)
        if self.denominatorResults != {}:
            print >> outfile, ""
            printResults.simplePrint(self.denominatorResults, decimalPlaces, outfile)
    
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
                                printResults.numberToString(relErr, 2)])
            printResults.printData(outtext, leftJustify, sys.stdout)
        
    
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
            line.append(printResults.numberToString(errorAvg[1][k], decimalPlaces))
            line.append(printResults.numberToString(errorStdDev[1][k], decimalPlaces))
            line.append(printResults.numberToString(errorRMS[1][k], decimalPlaces))
            line.append(printResults.numberToString(relErrorAvg[1][k], decimalPlaces))
            line.append(printResults.numberToString(relErrorStdDev[1][k], decimalPlaces))
            line.append(printResults.numberToString(relErrorRMS[1][k], decimalPlaces))
            
            outtext.append(line)
        
        printResults.printData(outtext, leftJustify, sys.stdout)
    
    def printAggregateResults(self, decimals, outfile, wlMetric, expMetric, aggregateSimpoints):
        
        self.wlMetric = wlMetric
        self.expMetric = expMetric
        self.aggregateSimpoints = aggregateSimpoints
        
        allNPs = processResults.findAllNPs(self.matchingConfigs)
        allParams = processResults.findAllParams(self.matchingConfigs)
        allWls = processResults.findAllWorkloads(self.matchingConfigs)
        allBms = []
        
        assert(len(allNPs) > 0)
        
        aggregate = {}
        if allNPs == [1]:
            if not self.quiet:
                print "Entering single-core print mode"
            
            assert allWls == []
            allBms = processResults.findAllBenchmarks(self.matchingConfigs)
            allMemsysNPs = processResults.findAllMemsysNPs(self.matchingConfigs)
            for params in allParams:
                for bm in allBms:
                    for memsysNp in allMemsysNPs:
                        bmconfig = ExperimentConfiguration(1, params, bm, experimentConfiguration.singleWlID)
                        aggregate[bmconfig] = self._processSingleResults(bm, params, memsysNp)
                        
        else:
            if not self.quiet:
                print "Entering multi-core print mode"
            
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
            
        self._printAggregate(aggregate, allNPs, allWls, allParams, outfile, decimals, wlMetric.doTablePrint, allBms)
            
    def _printAggregate(self, aggregate, allNPs, allWls, allParams, outfile, decimals, printAllCPUs, allBms):
        
        sortedParams = printResults.createSortedParamList(allParams)
        
        outdata = []
        titleLine = [""]
        leftJust = [True]
        for p in sortedParams:
            titleLine.append(self._paramsToString(p))
            leftJust.append(False)
            
        outdata.append(titleLine)
        
        allNPs.sort()
        allWls.sort()
        allBms.sort()

        for np in allNPs:
            if np == 1:
                if allWls == []:
                    for bm in allBms:
                        outdata = self._addAggregatePrintElement(outdata, np, bm, sortedParams, aggregate, decimals, printAllCPUs)
                    
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
                            line.append(printResults.numberToString(aggregate[c][0], decimals))
                outdata.append(line)
                                    
        printResults.printData(outdata, leftJust, outfile)
    
    def _addAggregatePrintElement(self, outdata, np, wlOrBm, sortedParams, aggregate, decimals, printAllCPUs):
        
        if self.aggregateSimpoints:
            simpointrange = [0]
        else:
            simpointrange = [i for i in range(simpoints.maxk)]
            
        if printAllCPUs:
            cpus = [i for i in range(np)]
        else:
            cpus = [np]
            
        iterspace = []
        for s in simpointrange:
            for c in cpus:
                iterspace.append( (s,c) )

        for simpoint, cpuID in iterspace:
            
            title = str(np)+"-"+str(wlOrBm)
            
            if simpoint != experimentConfiguration.NO_SIMPOINT_VAL:
                title += "-sp"+str(simpoint)
            if cpuID != np and np != 1:
                tmpWl = workloads.getBms(wlOrBm, np, False)
                title += "-"+tmpWl[cpuID]

            line = [title]
            valuePresent = False
            for params in sortedParams:
                found = False
                for config in aggregate:
                    correctBM = False
                    if np > 1 and config.workload == wlOrBm:
                        correctBM = True
                    if np == 1 and config.benchmark == wlOrBm:
                        correctBM = True
                    
                    if config.np == np and correctBM and config.parameters == params:
                        assert not found
                        found = True
                        
                        if len(aggregate[config]) > simpoint:
                            valuePresent = True 
                            if cpuID != np:
                                line.append(printResults.numberToString(aggregate[config][simpoint][cpuID], decimals))
                            else:
                                line.append(printResults.numberToString(aggregate[config][simpoint], decimals))
            if valuePresent:
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
        
    def _processSingleResults(self, bm, params, memsysNp):
        nominatorRes = processResults.filterResults(self.noPatResults, 1, params, experimentConfiguration.singleWlID, bm, memsysNp)
        nominator = {}
        if self.aggregateSimpoints:
            nominator  = self._aggregateSimpoints(nominatorRes, nominator, bm)
        else:
            nominator = self._createSimpointDict(nominatorRes, nominator, bm)
        
        if self.denominatorResults != {}:
            denominatorRes = processResults.filterResults(self.noPatDenominatorResults, 1, params, experimentConfiguration.singleWlID, bm, memsysNp)
            denominator = {}
            if self.aggregateSimpoints:
                denominator  = self._aggregateSimpoints(denominatorRes, denominator, bm)
            else:
                denominator = self._createSimpointDict(denominatorRes, denominator, bm)
            
            value = self._computeRatio(nominator, denominator)
        else:
            value = nominator
        
        metric = NoAggregation(False)
        metric.setValues(value, {}, 1, bm)
        return metric.computeMetricValue()
        
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
    
    def _issueMultipatWarning(self, patterns, configs):
        
        if not self.quiet:
            patterns.sort()
            print "Warning: Aggregating results for statistics:"
            for p in patterns:
                print "- "+str(p)
            print
            
            nps = []
            usedSimpoints = []
            usedParams = {}
            for c in configs:
                if c.np not in nps:
                    nps.append(c.np)
                if c.simpoint not in usedSimpoints:
                    usedSimpoints.append(c.simpoint)
                    
                for p in c.parameters:
                    if p not in usedParams:
                        usedParams[p] = [c.parameters[p]]
                    else:
                        if c.parameters[p] not in usedParams[p]:
                            usedParams[p].append(c.parameters[p])
            
            nps.sort()
            usedSimpoints.sort()
            
            print "Aggregating configurations:"
            print "NP:         "+str(nps)
            print "Simpoints:  "+str(usedSimpoints)
            print "Parameters: "+str(usedParams)
            print
            
                            
        
        self.aggregatePatternsWarnIssued = True
    
    def _accumulate(self, original, new):
        
        if type(new) is dict:
            assert type(original) == dict
            for k in new:
                
                if k == "min_value":
                    if k in original:
                        original[k] = min(original[k], new[k])
                    else:
                        original[k] = new[k]
                    continue
                
                if k == "max_value":
                    if k in original: 
                        original[k] = max(original[k], new[k])
                    else:
                        original[k] = new[k]
                    continue
                
                if k not in original:
                    original[k] = 0
                original[k] += new[k]
        else:
            # assume scalar
            original += new
        
        return original
        
    
    def _removePatternsFromResult(self, results):
        configRes = {}
        
        for p in results:
            for c in results[p]:
                
                if self.aggregatePatterns:
                    if not self.aggregatePatternsWarnIssued:
                        self._issueMultipatWarning(results.keys(), results[p].keys())
                    
                    
                    if c not in configRes:
                        configRes[c] = results[p][c]
                    else:
                        configRes[c] = self._accumulate(configRes[c], results[p][c])
                else:
                    if c in configRes:
                        raise MultiplePatternError(results.keys(), results[p].keys())
                        
                    configRes[c] = results[p][c]
        return configRes
        
    def _computeWorkloadAggregate(self, results, np, params, wl):
        
        bms = workloads.getBms(wl, np, True)
        
        mpAggregate = {}
        spAggregate = {}
        for bm in bms:
            filteredRes = processResults.filterResults(results, np, params, wl, bm, np)
            
            if self.aggregateSimpoints:
                mpAggregate = self._aggregateSimpoints(filteredRes, mpAggregate, bm)
            else:
                mpAggregate = self._createSimpointDict(filteredRes, mpAggregate, bm)
            
            if self.wlMetric.spmNeeded:
                if self.baseconfig == None:
                    singleRes = processResults.filterResults(results, 1, params, experimentConfiguration.singleWlID, bm, np)
                else:
                    tmpconfig = experimentConfiguration.buildMatchAllConfig()
                    tmpconfig.copy(self.baseconfig)
                    tmpconfig.benchmark = bm
                    singleRes = processResults.filterResultsWithConfig(results, tmpconfig)
                
                if singleRes == {}:
                    raise Exception("Single program mode results needed for metric '"+str(self.wlMetric)+"' but cannot be found")
                
                if self.aggregateSimpoints:
                    spAggregate = self._aggregateSimpoints(singleRes, spAggregate, bm)
                else:
                    spAggregate = self._createSimpointDict(singleRes, spAggregate, bm)
        
        return mpAggregate, spAggregate
        
    def _aggregateSimpoints(self, filteredRes, aggregate, bm):
        
        simpointdata = simpoints.simpoints[bm]
        
        foundSimpoints = [False for i in range(simpoints.maxk)]
        tmpAggregate = 0
        for i in range(simpoints.maxk):
            for c in filteredRes:
                if c.simpoint == experimentConfiguration.NO_SIMPOINT_VAL:
                    raise Exception("Results must have simpoints when aggregate simpoints is used")
                if c.simpoint == i:
                    assert not foundSimpoints[i]
                    tmpAggregate += filteredRes[c] * simpointdata[i][simpoints.PROBKEY]
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
        
        if self.aggregatePatterns:
            aggDistrib = self._aggregateDistributions(self.noPatResults)
            self._printDistribution(aggDistrib, decimalPlaces, outfile)
            
        else:
            for statkey in self.results:
            
                print >> outfile, ""
                print >> outfile, "Aggregate distribution for pattern "+statkey
            
                aggDistrib = self._aggregateDistributions(self.results[statkey])
                self._printDistribution(aggDistrib, decimalPlaces, outfile)
                                
                
    
    def _aggregateDistributions(self, data):
        aggDistrib = {}                
        for config in data:
            curDistrib = data[config]
            
            for key in curDistrib:
                if key not in aggDistrib:
                    aggDistrib[key] = curDistrib[key]
                else:
                    aggDistrib[key] += curDistrib[key]
        return aggDistrib
                    
    def _printDistribution(self, aggDistrib, decimalPlaces, outfile):
        outtext = [["Key", "Value"]]
        leftJustify = [True, False]
        
        distKeys = aggDistrib.keys()
        distKeys.sort()
        for d in distKeys:
            line = [printResults.numberToString(d, decimalPlaces)]
            line.append(printResults.numberToString(aggDistrib[d], decimalPlaces))
            outtext.append(line)
        
        printResults.printData(outtext, leftJustify, outfile)    
    
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
