#!/usr/bin/python

import unittest
from checkpoints.Checkpoint import Checkpoint
from checkpoints.IniFileSection import IniFileSection

__metaclass__ = type

class CheckpointTestCase(unittest.TestCase):

    def testIniFileSection(self):
        
        rootSec = IniFileSection()
        rootSec.setName("Root")
        firstChild = IniFileSection()
        firstChild.setName("Child 1")
        secondChild = IniFileSection()
        secondChild.setName("Child 2")

        rootSec.addChild(firstChild)
        rootSec.addChild(secondChild)
        
        self.assert_(not rootSec.isEmpty())
        self.assert_(firstChild.isEmpty())
        self.assert_(secondChild.isEmpty())
        
        firstChild.addDataElement("Testdata", "15")
        self.assert_(not firstChild.isEmpty())
        self.assert_(secondChild.isEmpty())
        
        secondChild.addDataElement("Testdata", "15")
        self.assert_(not secondChild.isEmpty())

    def testSectionOrder(self):
        
        path = "/home/jahre/workspace/m5sim-tools/checkpoints/unittests/"
        
        checkpoint1 = Checkpoint()
        checkpoint1.createFromFile(path+"vpr0-50000.cpt")

        checkpoint1.writeToFile("vpr0-50000.cpt.out")
        checkpoint2 = Checkpoint()
        checkpoint2.createFromFile("vpr0-50000.cpt.out")
        
        chk1Sections = checkpoint1.sections
        chk2Sections = checkpoint2.sections
        
        self.assert_(len(chk1Sections) == len(chk2Sections))
        self.traverseCheckpoints(chk1Sections, chk2Sections)
        
    def traverseCheckpoints(self, sec1, sec2):
        for name in sec1:
            self.assert_(name in sec2)
            for elem in sec1[name].dataElements:
                self.assert_(elem in sec2[name].dataElements)
                self.assertEquals(sec1[name].dataElements[elem], sec2[name].dataElements[elem])
            
            self.traverseCheckpoints(sec1[name].children, sec2[name].children)


if __name__ == "__main__":
    unittest.main()

    