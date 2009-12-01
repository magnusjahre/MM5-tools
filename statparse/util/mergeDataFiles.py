#!/usr/bin/env python
from statparse import printResults

import sys
import os
import re

from optparse import OptionParser

def fatal(message):
    print
    print "ERROR: "+message
    print
    sys.exit(-1)

def parsePrintSpec(opts):
    mergeSpec = []
    if opts.printSpec != "":
        vals = opts.printSpec.split(",")
        for v in vals:
            try:
                colID = int(v)
            except:
                fatal("Print spec parse error for string "+str(opts.printSpec))
            
            mergeSpec.append( colID )
    return mergeSpec

def parseArgs():
    parser = OptionParser(usage="mergeDataFiles.py [options] FILENAME [FILENAME ...]")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--data-separator", action="store", dest="dataSeparator", type="string", default="\s+", help="Separator for data lines text files")
    parser.add_option("--head-separator", action="store", dest="headSeparator", type="string", default="\s\s+", help="Separator for header lines text files")
    parser.add_option("--print-spec", action="store", dest="printSpec", type="string", default="", help="A comma separated list of one-indexed column IDs include in output (e.g. 2,3,1)")
    parser.add_option("--normalize-to", action="store", dest="normalizeTo", type="int", default=-1, help="Print values relative to this column")    

    opts, args = parser.parse_args()
    
    mergeSpec = parsePrintSpec(opts)
    
    if len(args) == 0:
        fatal("Commandline error\nUsage: "+parser.usage)
    
    return opts,args, mergeSpec
    
def readFiles(filenames, opts):
    
    data = []
    
    for filename in filenames:
        curFile = open(filename)
        
        first = True
        fileRows = []
        numVals = 0
        
        for line in curFile:
            if first:
                head = re.split(opts.headSeparator, line.strip())
                firstLength = len(head) 
                first = False
            else:
                values = re.split(opts.dataSeparator, line.strip())
                if numVals != 0:
                    assert len(values) == numVals
                numVals = len(values)
                fileRows.append(values)
                
        if not (firstLength == numVals or firstLength == numVals-1):
            fatal("Unknown header format in file "+filename+", possibly a parse error") 
        
        data.append( (head, fileRows, numVals) )
    
    return data

def mergeData(fileData, opts): 
    
    totalHeaders = [""]
    mergedData = {}
    
    maxVals = 0
    for headers, values, numVals in fileData:
        maxVals += numVals-1
         
        if len(headers) == numVals:
            headers = headers[1:]
        
        for h in headers:
            totalHeaders.append(h)
        
        for v in values:
            assert len(v) == numVals
            
            match = re.search("fair[0-9][0-9]", v[0])
            wl = match.group()
            
            if wl not in mergedData:
                mergedData[wl] = []
                
            for val in v[1:]:
                mergedData[wl].append(val)
    
    wls = mergedData.keys()
    wls.sort()
    
    mergedMatrix = []
    mergedMatrix.append(totalHeaders)
    
    for wl in wls:
        if len(mergedData[wl]) == maxVals:
            line = [wl]
            for v in mergedData[wl]:
                line.append(v)
                
            mergedMatrix.append(line) 
    
    return mergedMatrix

def processData(mergedData, mergeSpec, opts):
    
    if mergeSpec != []:
        newData = []
        for line in mergedData:
            newLine = [line[0]]
            for cID in mergeSpec:
                newLine.append(line[cID])
            newData.append(newLine)
        mergedData = newData
    
    numVals = len(mergedData[0])
    justify = [False for i in range(numVals)]
    justify[0] = True
    
    if opts.normalizeTo != -1:
        normalizedData = {}
        for i in range(1, len(mergedData)):
            normalizedData[i] = {}
            for j in range(1, len(mergedData[i])):
                try:
                    relVal = (float(mergedData[i][j]) / float(mergedData[i][opts.normalizeTo])) - 1
                except:
                    fatal("Normalization failed on line "+str(i)+", column "+str(j)+", trying to normalize to column "+str(opts.normalizeTo))
                normalizedData[i][j] = printResults.numberToString(relVal, opts.decimals)
        
        for i in normalizedData:
            for j in normalizedData[i]:
                mergedData[i][j] = normalizedData[i][j]
    
    
    return mergedData, justify

def main():

    opts,args, printSpec = parseArgs()
    
    for filename in args:
        if not os.path.exists(filename):
            fatal("File "+filename+" does not exist!")
    
    fileData = readFiles(args, opts)
    mergedData = mergeData(fileData, opts)
    processedData, justify = processData(mergedData, printSpec, opts)
    
    printResults.printData(processedData, justify, sys.stdout, opts.decimals)

if __name__ == '__main__':
    main()