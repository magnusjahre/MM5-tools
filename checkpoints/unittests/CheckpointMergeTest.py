#!/usr/bin/python

import unittest
import os
import deterministic_fw_wls as workloads
from m5test.M5Command import M5Command
import checkpoints
import checkpoints.Checkpoint
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
        cpuID = 0
        
        outdir = checkpoints.getCheckpointDirectory(4, self.memsys, self.wlName)
        if not os.path.exists(outdir):
            os.mkdir(checkpoints.getCheckpointDirectory(4, self.memsys, self.wlName))
        outfilename = outdir+"/m5.cpt"
        
        checkpoints.prepareOutputFile(outfilename)
        
        for bm in self.testWorkload:
            checkPath = checkpoints.getCheckpointDirectory(1, self.memsys, bm+"0")
            checkFile = checkPath+"/m5.cpt" 
            
            print "Reading checkpoint from file "+checkFile
            
            newCheckpoint = Checkpoint()
            newCheckpoint.createFromFile(checkFile, outfilename, cpuID)
            
            wlCheckpoints.append(newCheckpoint)
            
            cpuID += 1

        print "Merging and dumping shared cache state"
        checkpoints.Checkpoint.mergeSharedCache(wlCheckpoints, outfilename)

        siminsts = 1000000
        
        print "Running workload "+self.wlName+" for "+str(siminsts)+" instructions..."
        
        m5cmd = M5Command()
        m5cmd.setUpTest(self.wlName, 4, "RingBased", 1)
        m5cmd.setArgument("MEMORY-BUS-SCHEDULER", "RDFCFS") 
        m5cmd.setArgument("USE-CHECKPOINT", ".")
        m5cmd.setArgument("SIMINSTS", siminsts)
        m5cmd.setExpectedComInsts(siminsts)
        
        #TODO: insert committed inst check when stats parsing has been implemented
        success = m5cmd.run(0, "detailedCPU.*COM:count.*", False)
        self.assert_(success)

if __name__ == "__main__":
    unittest.main()
