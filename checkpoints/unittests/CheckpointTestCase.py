#!/usr/bin/python

import unittest
from checkpoints.Checkpoint import Checkpoint

from guppy import hpy
import gc

__metaclass__ = type

class CheckpointTestCase(unittest.TestCase):

    def testSectionOrder(self):
        
        path = "/home/jahre/workspace/m5sim-tools/checkpoints/unittests/"
        
        h = hpy()
        h.setrelheap()
        
        outfilename = "vpr0-50000.cpt.out"
        
        checkpoint1 = Checkpoint()
        checkpoint1.prepareOutputFile(outfilename)
        checkpoint1.createFromFile(path+"vpr0-50000.cpt", outfilename , 3)

        
        heap = h.heap()
        print heap        
        
        checkpoint1.writeToFile(outfilename)
        checkpoint2 = Checkpoint()
        checkpoint2.createFromFile(outfilename, "vpr0-50000.cpt.mock", 3)
        
        chk1CacheState = checkpoint1.sharedCaches
        chk2CacheState = checkpoint2.sharedCaches
        
        self.assert_(len(chk1CacheState) == len(chk2CacheState))
        
        for bankName in chk1CacheState:
            self.assert_(bankName in chk2CacheState)
            
            chk1Content = chk1CacheState[bankName].content
            chk2Content = chk2CacheState[bankName].content
            
            for i in chk1Content:
                for p in chk1Content[i]:
                    self.assertEqual(chk1Content[i][p], chk2Content[i][p])
                

if __name__ == "__main__":
    unittest.main()

    