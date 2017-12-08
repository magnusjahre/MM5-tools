#!/usr/bin/env python
# encoding: utf-8

import sys
import os

from util import fatal, warn
from optparse import OptionParser

def parseArgs():
    program_name = os.path.basename(sys.argv[0])
    program_usage = program_name+" [options] command-file-folder"

    # setup option parser
    parser = OptionParser(usage=program_usage)
    #parser.add_option("-i", "--in", dest="infile", help="set input path [default: %default]", metavar="FILE")

    # process options
    opts, args = parser.parse_args()

    if len(args) != 1:
        print "Command line error, usage: "+program_usage
        sys.exit(-1)

    return opts,args

class Experiment:
    
    def __init__(self, configfilename):
        self.configfilename = configfilename
        
        tmp = self.configfilename.split("-")
        if tmp[-1] == "pbsconfig.py":
            self.expname = "-".join(tmp[0:-1])
            
            self.configurations = {}
            self.fileContent = []
            self.readConfigurations(self.configfilename)
            self.valid = True
        else:
            print "-- Skipping file "+str(configfilename)
            self.valid = False
    
    def readConfigurations(self, cfgfilename):
        f = open(cfgfilename)
        lineNum = 0
        for l in f:
            if l.startswith("#INCLUDE"):
                tmp = l.split()
                assert len(tmp) == 2
                print "-- Recursively including file "+tmp[1]
                self.readConfigurations(tmp[1])
                continue
            elif l.startswith("#CONFIG"):
                tmp = l.split()
                assert tmp[1] not in self.configurations
                self.configurations[tmp[1]] = (tmp[2].split(","), lineNum)
                continue
            
            self.fileContent.append(l)
            lineNum += 1
    
    
    
    def writeConfigFile(self, inconfig):
        for cf in inconfig:
            assert cf in self.configurations
            params, linenum = self.configurations[cf]
            self.fileContent[linenum] = cf+" = "+inconfig[cf]+"\n"
            
        f = open("pbsconfig.py", "w")
        for l in self.fileContent:
            f.write(l)
        f.flush()
        f.close()
        

def buildExperimentdict(configdir):
    os.chdir(configdir)
    files = os.listdir(".")
    
    expdict = {}
    for f in files:
        print "Processing file "+f
        exp = Experiment(f)
        
        if exp.valid:
            assert "np" in exp.configurations
            nps, linenum = exp.configurations["np"]
            for np in nps:
                if np not in expdict:
                    expdict[np] = []
                    
                assert exp.expname not in expdict
                expdict[np].append(exp)
        
    os.chdir("..")
    return expdict

def writeIsExpFile(cpuCnt, dirname):
    f = open(".isexperiment", "w")
    f.write(str(cpuCnt)+",True\n")
    f.flush()
    f.close()

def makeDirTree(dirStruct):
    
    for cpuCnt in dirStruct:
        cpuDirName = str(cpuCnt)+"core"
        if not os.path.exists(cpuDirName):
            print "Making directory "+cpuDirName
            os.mkdir(cpuDirName)
        os.chdir(cpuDirName)
        for exp in dirStruct[cpuCnt]:
            if not os.path.exists(exp.expname):
                print "Making directory "+exp.expname
                os.mkdir(exp.expname)
                os.chdir(exp.expname)
                writeIsExpFile(cpuCnt, exp.expname)
                exp.writeConfigFile({"np": str(cpuCnt)})
                os.chdir("..")
                
        os.chdir("..")

def main():
    opts, args = parseArgs()
    
    print "Reading config directory"
    expdict = buildExperimentdict(args[0])
    
    print "Making directory structure"
    makeDirTree(expdict) 


if __name__ == "__main__":
    sys.exit(main())