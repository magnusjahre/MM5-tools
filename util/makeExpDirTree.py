#!/usr/bin/env python
# encoding: utf-8

import sys
import os

from util import fatal, warn
from optparse import OptionParser

def parseArgs():
    program_name = os.path.basename(sys.argv[0])
    program_usage = program_name+" [options] command-file"

    # setup option parser
    parser = OptionParser(usage=program_usage)
    #parser.add_option("-i", "--in", dest="infile", help="set input path [default: %default]", metavar="FILE")

    # process options
    opts, args = parser.parse_args()

    if len(args) != 1:
        print "Command line error, usage: "+program_usage
        sys.exit(-1)

    return opts,args

def readDirStructure(filename):
    structfile = open(filename)
    dirstruct = {}
    lineno = 1
    for l in structfile:
        try:
            cpuCnt, dirName = l.strip().split(",")
            cpuCnt = int(cpuCnt)
        except:
            fatal("Parse error @ line "+str(lineno)+": "+str(l))
        if cpuCnt in dirstruct:
            dirstruct[cpuCnt].append(dirName)
        else:
            dirstruct[cpuCnt] = [dirName]
        lineno += 1
        
    return dirstruct

def writeIsExpFile(cpuCnt, dirname):
    os.chdir(dirname)
    f = open(".isexperiment", "w")
    f.write(str(cpuCnt)+",True\n")
    f.flush()
    f.close()
    os.chdir("..")

def makeDirTree(dirStruct):
    
    for cpuCnt in dirStruct:
        cpuDirName = str(cpuCnt)+"core"
        if not os.path.exists(cpuDirName):
            print "Making directory "+cpuDirName
            os.mkdir(cpuDirName)
        os.chdir(cpuDirName)
        for dirname in dirStruct[cpuCnt]:
            if not os.path.exists(dirname):
                print "Making directory "+dirname
                os.mkdir(dirname)
                writeIsExpFile(cpuCnt, dirname)
            
        os.chdir("..")

def main():
    opts, args = parseArgs()
    
    print "Reading structure file..."
    dirStruct = readDirStructure(args[0])
    
    print "Making directory structure"
    makeDirTree(dirStruct) 


if __name__ == "__main__":
    sys.exit(main())