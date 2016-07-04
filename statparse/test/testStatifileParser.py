#!/usr/bin/python

import unittest
import re

from statparse.statfileParser import StatfileIndex, privateStatNames
from statparse.statfileParser import ExperimentConfiguration

import deterministic_fw_wls as workloads
import m5test

class TestStatfileParser(unittest.TestCase):

    filepath = m5test.getWorkspaceRoot()+"/statparse/test/"
    statfile = filepath+"fair19-8-stats.txt"
    dumporderfile = filepath+"statsDumpOrder.txt"
    distributionfile = filepath+"distribution.txt"
    
    privateStatNames = ["detailedCPU", 
                        "L1dcaches", 
                        "L1icaches", 
                        "PointToPointLink",
                        "PrivateL2Cache"] 

    def testDumpOrderRead(self):
        index = StatfileIndex()
        order = index._findParseOrder(self.dumporderfile)
        self.assertEqual(order, [1,3,6,5,7,4,0,2])

    def testStatfileParser(self):
        
        np = 8
        wl = "fair19"
        params = {}
        
        index = StatfileIndex()
        index.addFile(self.statfile, self.dumporderfile, np, wl, params)
        
        order = index._findParseOrder(self.dumporderfile)
        
        statfile = open(self.statfile)
        
        startPat = re.compile("Begin Simulation Statistics")
        endPat = re.compile("End Simulation Statistics")
        distStartPat = re.compile("start_dist")
        distEndPat = re.compile("end_dist")
        whitespacePat = re.compile("^\s*$")
        ignorePattern = re.compile("\*\*Ignore")
        
        floatPat = re.compile("-?[0-9][0-9]*\.[0-9][0-9]*")
        intPat = re.compile("-?[0-9][0-9]*")
        keyPat = re.compile("[a-zA-Z:_[0-9][a-zA-Z:_[0-9]*\.[a-zA-Z:_[0-9][a-zA-Z:_[0-9]*")
        
        
        inDist = False
        currentConfig = None
        keyname = ""
        
        currentCPUPatterns = []
        
        bms = workloads.getBms(wl, np, True)
        
        for line in statfile:
            if whitespacePat.search(line):
                pass
            elif startPat.search(line):
                searchConfig = ExperimentConfiguration(np, params, bms[order[0]], wl=wl)
                matches = index.findConfiguration(searchConfig)
                self.assertNotEqual(matches, [])
                self.assertEqual(len(matches), 1)
                currentConfig = matches[0]
                
                cpuID = str(currentConfig.getIDInWorkload())
                currentCPUPatterns = [re.compile(stat+cpuID) for stat in privateStatNames]
                
            elif endPat.search(line):
                order.pop(0)
            
            elif inDist:
                if distEndPat.search(line):
                    inDist = False
                    continue
                
                if not self.putInIndex(keyname, currentCPUPatterns):
                    continue
                
                vals = line.split()
                
                curDist = index.findDistribution(keyname, currentConfig)
                self.assertNotEqual(curDist, None)
                
                if intPat.match(vals[0]):
                    self.assertEqual(curDist[int(vals[0])], int(vals[1]))
                else:
                    if keyPat.search(vals[0]):
                        dictKey = vals[0].split(".")[-1]
                        self.assertEqual(curDist[dictKey], int(vals[1]))
                    else:
                        keystr = vals[0]
                        for v in vals[1:]:
                            if intPat.search(v):
                                value = int(v)
                                break
                            keystr += " "+v
                        self.assertEqual(curDist[keystr], value)
                
            elif distStartPat.search(line):
                inDist = True
                keyvals = line.split()[0].split(".")
                keyname = keyvals[0]
                for k in keyvals[1:-1]:
                    keyname += "."+k
                
                if self.putInIndex(line, currentCPUPatterns):
                    self.assertNotEqual(index.findDistribution(keyname,currentConfig), None)    
                
            else:
                key, val = line.split()[0:2]
                
                if ignorePattern.search(line):
                    self.assertEqual(index.findValue(key, currentConfig), None)
                    continue
                
                inIndex = False
                if floatPat.search(val):
                    value = float(val)
                    inIndex = True
                elif intPat.search(val):
                    value = int(val)
                    inIndex = True
            
                if not self.putInIndex(key, currentCPUPatterns):
                    inIndex = False
                
                if inIndex:
                    indexValue = index.findValue(key, currentConfig)
                    self.assertEqual(value, indexValue)
                    
        statfile.close()

    def putInIndex(self, instr, curPats):
        allPrivPats = [re.compile(stat) for stat in self.privateStatNames]
        
        for i in range(len(allPrivPats)):
            if allPrivPats[i].search(instr):
                if not curPats[i].search(instr):
                    return False
        return True
        

    def testIndexDump(self):
        
        np = 8
        wl = "fair19"
        params = {}
        
        index = StatfileIndex()
        index.addFile(self.statfile, self.dumporderfile, np, wl, params)
        
        indexmodname = "testindex"
        
        index.dumpIndex(indexmodname)
        
        readIndex = StatfileIndex(indexmodname)
        
        
        for statkey in index.resultstore:
            self.assert_(statkey in readIndex.resultstore)
            
            data1 = index.resultstore[statkey]
            data2 = readIndex.resultstore[statkey]
            
            self.assertEqual(data1, data2)
            
    
if __name__ == "__main__":
    unittest.main()