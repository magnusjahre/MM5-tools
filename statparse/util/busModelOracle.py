#!/usr/bin/python

import sys
import math

from optparse import OptionParser
from statparse.tracefile.tracefileData import TracefileData
from statparse.tracefile.errorStatistics import computeError, ErrorStatistics
from statparse.util import getSingleCoreResKey, getSimpleVarparamKey

ORACLE_MODELS = {"graph": "Graph",
                 "histogram": "Histogram"}

ORACLE_INVALID = 0
ORACLE_STATIC = 1
ORACLE_DYNAMIC = 2

def parseArgs():
    parser = OptionParser(usage="busModelOracle.py [options] filename model")

    parser.add_option("--relative", action="store_true", dest="relative", default=False, help="Use relative instead of absolute errors")
    
    opts, args = parser.parse_args()
    
    if len(args) != 2:
        print "Command line error"
        print "Usage: "+parser.usage
        sys.exit(-1)
    
    if args[1] not in ORACLE_MODELS:
        print "Model argument must be in "+str(ORACLE_MODELS)
        sys.exit(-1)
    
    return opts,args

class BusOracle:
    
    def __init__(self, relative):
        self.data = []
        self.values = []
        self.errstats = ErrorStatistics(relative)
        
    def sample(self, actual, oracleData, oracleValue):
        self.data.append(oracleData)
        self.values.append(oracleValue)
        self.errstats.sample(oracleData, actual)
        

def generateOracleData(actual, schemeData, relative):
    
    dynOracle = BusOracle(relative)
    
    for i in range(len(actual)):
        minerr = 1000000000000000.0
        minerrval = -1
        mindata = 0
        for k in schemeData:
            err = math.fabs(computeError(schemeData[k][i], actual[i], relative, -1))
            if err < minerr:
                minerr = err
                minerrval = k
                mindata = schemeData[k][i]
        assert minerrval != -1
        dynOracle.sample(actual[i], mindata, minerrval)
        
    return dynOracle

def getStaticOracleData(actual, schemeData, relative):
    statOracle = BusOracle(relative)
    
    minerr = 1000000000000000.0
    minkey = -1
    
    for k in schemeData:
        tmperr = ErrorStatistics(relative)
        
        for i in range(len(actual)):
            tmperr.sample(schemeData[k][i], actual[i])
        
        absmean = math.fabs(tmperr.getStatByName("mean"))
        if absmean < minerr:
            minerr = absmean
            minkey = k
            
    assert minkey != -1
    for i in range(len(actual)):
        statOracle.sample(actual[i], schemeData[minkey][i], minkey)
    
    return statOracle

def getExperimentData(oracletype, dirs, actualColumnName, getTracename, relative, model, params):
    print oracletype
    
    results = {}    
    aggregateErrors = {}
    
    for p in params:
        aggregateErrors[p] = ErrorStatistics(relative) 
    
    for bm, varparams, dirID in dirs:
        traceFileName = getTracename(dirID, 0, False)

        oracle = getOracle(oracletype, traceFileName, model, relative, actualColumnName)
        
        reskey = getSingleCoreResKey(bm)
        paramkey = getSimpleVarparamKey(varparams)
        
        aggregateErrors[paramkey].aggregate(oracle.errstats)
            
        if reskey not in results:
            results[reskey] = {}
            
        assert paramkey not in results[reskey]
        results[reskey][paramkey] = oracle.errstats
    
    return results, aggregateErrors
    
def getOracle(oracle, filename, model, relative, actualColName):
    tracecontent = TracefileData(filename)
    tracecontent.readTracefile()    
    
    colmap = tracecontent.findColumnIDs(ORACLE_MODELS[model], "-")
    actualcol = tracecontent.findColumnID(actualColName, -1)

    data = {}
    for k in sorted(colmap.keys()):
        assert k not in data
        data[k] = tracecontent.getColumn(colmap[k])
    
    actualdata = tracecontent.getColumn(actualcol)
    
    if oracle == ORACLE_DYNAMIC:
        return generateOracleData(actualdata, data, relative)  
    return getStaticOracleData(actualdata, data, relative)

def main():
    
    opts,args = parseArgs()    
    dynOracle = getOracle(ORACLE_DYNAMIC, args[0], args[1], opts.relative, "Actual Bus Queue Latency")
    staticOracle = getOracle(ORACLE_STATIC, args[0], args[1], opts.relative, "Actual Bus Queue Latency")
    
    print
    print "Static oracle statistics for file "+args[0]+" and "+args[1]+" model:"
    print
    print staticOracle.errstats
    
    print "Static oracle selections are:"
    for v in staticOracle.values:
        print v,
    print
    
    print
    print "Dynamic oracle statistics for file "+args[0]+" and "+args[1]+" model:"
    print
    print dynOracle.errstats
    
    print "Oracle selections are:"
    for v in dynOracle.values:
        print v,
    print

if __name__ == '__main__':
    main()