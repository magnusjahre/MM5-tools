#!/usr/bin/python

import unittest
import os
import deterministic_fw_wls as workloads
import checkpoints
import checkpoints.Checkpoint
from checkpoints.Checkpoint import Checkpoint
from m5test.M5Command import M5Command

class CheckpointMergeTest(unittest.TestCase):

    def testCheckpointMerge(self):
        
        wlName = "fair01"
        np = 4
        memsys = "RingBased"
        fwInsts = 10000000
        siminsts = 1000000

        checkpoints.Checkpoint.generateCheckpoint(wlName, np, fwInsts, memsys)

        print "Running workload "+wlName+" for "+str(siminsts)+" instructions..."
        
        m5cmd = M5Command()
        m5cmd.setUpTest(wlName, 4, "RingBased", 1)
        m5cmd.setArgument("MEMORY-BUS-SCHEDULER", "RDFCFS") 
        m5cmd.setArgument("USE-CHECKPOINT", ".")
        m5cmd.setArgument("SIMINSTS", siminsts)
        m5cmd.setExpectedComInsts(siminsts)
        
        #TODO: insert committed inst check when stats parsing has been implemented
        success = m5cmd.run(0, "detailedCPU.*COM:count.*", False)
        self.assert_(success)

if __name__ == "__main__":
    unittest.main()
