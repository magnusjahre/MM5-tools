#!/usr/bin/python

import sys
from optparse import OptionParser
from util import fatal

def parseArgs():
    
    parser = OptionParser(usage="verifyITCA.py [options] trace-file")
    #parser.add_option("--threads", '-t', action="store", dest="threads", default=4, type="int", help="Number of worker threads")
    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Usage:"
        print parser.usage
        sys.exit()
        
    return opts, args

def setITCAVal(val):
    if val == "1":
        return True
    return False

def checkITCA(itcadata, coverage):
    itInstruction = setITCAVal(itcadata[0])
    ROBEmpty = setITCAVal(itcadata[1])
    intertaskTop = setITCAVal(itcadata[2])
    cpuStalled = setITCAVal(itcadata[3])
    allMSHRsInter = setITCAVal(itcadata[4])
    doNotAccount = setITCAVal(itcadata[5])
    
    numstr = itcadata[0] + itcadata[1] + itcadata[2] + itcadata[3] + itcadata[4]
    index = int(numstr, 2)
    coverage[index] = True
    
    port1 = itInstruction and ROBEmpty
    port2 = intertaskTop and cpuStalled
    verifyDoNotAccount = port1 or port2 or allMSHRsInter
    
    return doNotAccount == verifyDoNotAccount, coverage

def verifyITCA(tracefile):
    firstLine = True
    coverage = [False for i in range(32)]
    for l in tracefile:
        if firstLine:
            firstLine = False
            continue
        
        vals = l.strip().split(";")
        itcadata = vals[1:]
        result, coverage = checkITCA(itcadata, coverage) 
        if not result:
            print "ITCA error detected at cycle "+str(vals[0])
            print vals[1:]
            sys.exit()
            
    print "Verification complete, coverage:"
    for i in range(len(coverage)):
        print i, coverage[i]

def main():
    opts,args = parseArgs()
    
    try:
        tracefile = open(args[0])
    except:
        fatal("Cannot open tracefile "+str(args[0]))
        
    verifyITCA(tracefile)


if __name__ == '__main__':
    main()