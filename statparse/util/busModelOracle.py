#!/usr/bin/python

import sys
import math

from optparse import OptionParser
from statparse.tracefile.tracefileData import TracefileData
from statparse.tracefile.errorStatistics import computeError, ErrorStatistics

ORACLE_MODELS = {"graph": "Graph",
                 "histogram": "Histogram"}

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

class DynamicBusOracle:
    
    def __init__(self, relative):
        self.data = []
        self.values = []
        self.errstats = ErrorStatistics(relative)
        
    def sample(self, actual, oracleData, oracleValue):
        self.data.append(oracleData)
        self.values.append(oracleValue)
        self.errstats.sample(oracleData, actual)
        

def generateOracleData(actual, schemeData, relative):
    
    dynOracle = DynamicBusOracle(relative)
    
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
    
def getDynamicOracle(filename, model, opts):
    tracecontent = TracefileData(filename)
    tracecontent.readTracefile()    
    
    colmap = tracecontent.findColumnIDs(ORACLE_MODELS[model], "-")
    actualcol = tracecontent.findColumnID("Actual Bus Queue Latency", -1)

    data = {}
    for k in sorted(colmap.keys()):
        assert k not in data
        data[k] = tracecontent.getColumn(colmap[k])
    
    actualdata = tracecontent.getColumn(actualcol)
    
    return generateOracleData(actualdata, data, opts.relative)    

def main():
    
    opts,args = parseArgs()    
    dynOracle = getDynamicOracle(args[0], args[1], opts)
    
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