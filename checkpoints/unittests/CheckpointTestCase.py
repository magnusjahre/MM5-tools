#!/usr/bin/python

import unittest
from checkpoints.Checkpoint import Checkpoint
from checkpoints.IniFileSection import IniFileSection

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
        
        chk1Sections = checkpoint1.sections
        chk2Sections = checkpoint2.sections
        
        self.assert_(len(chk1Sections) == len(chk2Sections))
        
#        for i in range(len(chk1Sections)):
#            self.assert_(chk1Sections[i].name == chk2Sections[i].name)
#            self.assertEquals(chk)

if __name__ == "__main__":
    unittest.main()

    