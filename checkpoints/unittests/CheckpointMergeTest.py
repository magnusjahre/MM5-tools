#!/usr/bin/python

import unittest
import os
import deterministic_fw_wls as workloads
from m5test.M5Command import M5Command
import checkpoints
from checkpoints.Checkpoint import Checkpoint

class CheckpointMergeTest(unittest.TestCase):

    def setUp(self):
        
        self.wlName = "fair01"
        self.np = 4
        self.memsys = "RingBased"
        
        self.testWorkload = workloads.getBms(self.wlName, self.np)
        fwInsts = 10000000
        fwInstInc = 5000000
        
        print "Generating checkpoints for fair01"
        
        for bm in self.testWorkload:
            
            chkPath = checkpoints.getCheckpointDirectory(1, self.memsys, bm+"0")
            if os.path.exists(chkPath):
                print "Checkpoint allready exists for "+bm+", skipping..."
                continue
            
            print "Generating checkpoint for "+bm+" with "+str(fwInsts)+" instructions in checkpoint"
            self.generateCheckpoint(bm+"0", fwInsts)
            fwInsts += fwInstInc

    def generateCheckpoint(self, bm, fwinsts):
        m5cmd = M5Command()
        m5cmd.setUpTest(bm, 1, "RingBased", 1)
        
        m5cmd.setArgument("MEMORY-ADDRESS-OFFSET", 0)
        m5cmd.setArgument("MEMORY-ADDRESS-PARTS", 4)
        m5cmd.setArgument("MEMORY-BUS-SCHEDULER", "RDFCFS") 
        m5cmd.setArgument("GENERATE-CHECKPOINT", "")
        m5cmd.setArgument("SIMINSTS", fwinsts)
        m5cmd.setExpectedComInsts(fwinsts)
        
        success = m5cmd.run(0, "simpleCPU.*num_insts.*")
        self.assert_(success)

    def tearDown(self):
        pass


    def testCheckpointMerge(self):
        
        wlCheckpoints = []
        for bm in self.testWorkload:
            checkPath = checkpoints.getCheckpointDirectory(1, self.memsys, bm+"0")
            checkFile = checkPath+"/m5.cpt" 
            
            print "Reading checkpoint from file "+checkFile
            
            newCheckpoint = Checkpoint()
            newCheckpoint.createFromFile(checkFile)
            
            wlCheckpoints.append(newCheckpoint)


if __name__ == "__main__":
    unittest.main()