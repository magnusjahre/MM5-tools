#!/usr/bin/env python
import sys
import os
import glob
import re

from optparse import OptionParser
from statparse import printResults
from statparse.tracefile.tracefileData import TracefileData, parseColumnSpec
from statparse.util.mergeDataFiles import readFiles, mergeData, processData
import statparse.tracefile.tracefileData as tracefileModule
import traceback

def parseArgs():
    parser = OptionParser(usage="formatTrace.py [options] ")

    parser.add_option("-c", "--columns", action="store", dest="columns", default="", type="string", help="The column IDs to print (e.g 0, 1, 3-5)")
    parser.add_option("-n", "--names", action="store_true", dest="printNames", default=False, help="Print the names and numbers of each column")
    
    opts, args = parser.parse_args()
    
    return opts,args

def main():

    opts,args = parseArgs()
    
    rootPath = re.search('res-4-(.+?)-b-b', args[0])
    rootPath = rootPath.group(1)
    
    print rootPath
    
    filenames = ["res-4-" + rootPath + "-b-b-cpl/globalPolicyCommittedInsts0.txt", 
                 "res-4-" + rootPath + "-b-b-cpl/globalPolicyCommittedInsts1.txt", 
                 "res-4-" + rootPath + "-b-b-cpl/globalPolicyCommittedInsts2.txt", 
                 "res-4-" + rootPath + "-b-b-cpl/globalPolicyCommittedInsts3.txt"]
    
    tracecontents = []
    
    for index in range(len(filenames)):
        tracecontents.append(TracefileData(filenames[index]))
        tracecontents[index].readTracefile()
    
    for tracecontent in tracecontents:
        numCols = len(tracecontent.headers)
        if (numCols < 56):
            tracecontent.headers[numCols] = "Alone Empty ROB Stall Cycles"
            tracecontent.headers[numCols+1] = "Alone Write Stall Cycles"
            tracecontent.headers[numCols+2] = "Alone Private Blocked Stall Cycles"
        
    path0 = "res-4-" + rootPath + "-*-0-cpl/globalPolicyCommittedInsts0.txt"
    path1 = "res-4-" + rootPath + "-*-1-cpl/globalPolicyCommittedInsts0.txt"
    path2 = "res-4-" + rootPath + "-*-2-cpl/globalPolicyCommittedInsts0.txt"
    path3 = "res-4-" + rootPath + "-*-3-cpl/globalPolicyCommittedInsts0.txt"
    paths = [path0, path1, path2, path3]
    
    for i in range(len(paths)):
        for filename in glob.glob(paths[i]):
            aloneTraceContent = TracefileData(filename)
            aloneTraceContent.readTracefile()
            tracecontents[i].data[54] = aloneTraceContent.getColumn(10)
            tracecontents[i].data[55] = aloneTraceContent.getColumn(6)
            tracecontents[i].data[56] = aloneTraceContent.getColumn(7)
    
    for i in range(len(tracecontents)):
        filename = "res-4-" + rootPath + "-b-b-cpl/globalPolicyCommittedInsts" + str(i) + ".txt"
        seperator = ";"
        first = True
        outfile = open(filename, "w")
        for key in tracecontents[i].headers:
            if first:
                first = False
            else:
                outfile.write(seperator)
            outfile.write(tracecontents[i].headers[key])
        for j in range(tracecontents[i].getNumRows()):
            outfile.write("\n")
            first = True
            for element in tracecontents[i].getRow(j):
                if first:
                    first = False
                else:
                    outfile.write(seperator)
                outfile.write(str(element))
        outfile.close()
        
if __name__ == '__main__':
    main()