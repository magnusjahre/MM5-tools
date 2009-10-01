#!/usr/bin/python
from statparse.statfileParser import StatfileIndex
from statparse.statResults import StatResults

import unittest
import checkpoints.Checkpoint
from m5test.M5Command import M5Command
import deterministic_fw_wls as workloads
import os
import glob
import shutil

statfiledir="fairstats"

class CheckpointFairnessTest(unittest.TestCase):
    
    def setUp(self):
        self.statfiles = {}
    
    def runM5(self, wlOrBm, np, siminsts, testnum, basenp = -1):
        m5cmd = M5Command()
        m5cmd.setUpTest(wlOrBm, np, "RingBased", 1)
        m5cmd.setArgument("MEMORY-BUS-SCHEDULER", "RDFCFS") 
        m5cmd.setArgument("USE-CHECKPOINT", ".")
        m5cmd.setArgument("SIMINSTS", siminsts)
        
        if np == 1:
            assert basenp != -1
            m5cmd.setArgument("MEMORY-ADDRESS-PARTS", basenp)
            m5cmd.setArgument("MEMORY-ADDRESS-OFFSET", 0)
            
        m5cmd.setExpectedComInsts(siminsts)
 
        m5cmd.run(testnum, "none", False)
        
        self.renameResultFiles(m5cmd.statsfilename, wlOrBm, np)
    
    def renameResultFiles(self, statfilename, wlOrBm, np):
        newStatfilename = statfiledir+"/"+wlOrBm+"-stats.txt"
        os.rename(statfilename, newStatfilename)
        shutil.copy("statsDumpOrder.txt", statfiledir)
        
        if np not in self.statfiles:
            self.statfiles[np] = {}
        self.statfiles[np][wlOrBm] = newStatfilename
        
    def testCheckpointFairness(self):
        
        if not os.path.exists(statfiledir):
            os.mkdir(statfiledir)
        for f in glob.glob(statfiledir+"/*"):
            print "removing "+f
            os.remove(f)
        
        wlname = "fair01"
        np = 4
        memsys = "RingBased"
        
        fwinst = 10000000

        checkpoints.Checkpoint.generateCheckpoint(wlname, np, fwinst, memsys, -1)
        
        bms = workloads.getBms(wlname, np, True)
        siminsts = 100000
        
        testnum = 1
        for bm in bms:
            self.runM5(bm, 1, siminsts, testnum, np)
            testnum += 1
        self.runM5(wlname, np, siminsts, testnum)
        
        index = StatfileIndex()
        for np in self.statfiles:
            for wlOrBM in self.statfiles[np]:
                index.addFile(self.statfiles[np][wlOrBM], "statsDumpOrder.txt", np, wlOrBM)

        statres = StatResults(index, None)
        statres.evaluateFairnessEstimateAccuracy(np, wlname, memsys)

if __name__ == "__main__":
    unittest.main()