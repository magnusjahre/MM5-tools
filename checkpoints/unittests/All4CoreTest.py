#!/usr/bin/python

import unittest
import new

import checkpoints.Checkpoint
from m5test.M5Command import M5Command

class CheckpointTestCase(unittest.TestCase):
    
    testID = 1
    
    def testFair01(self):
        self.runWorkload('fair01')
        
    def testFair02(self):
        self.runWorkload('fair02')
        
    def testFair03(self):
        self.runWorkload('fair03')
        
    def testFair04(self):
        self.runWorkload('fair04')
        
    def testFair05(self):
        self.runWorkload('fair05')
        
    def testFair06(self):
        self.runWorkload('fair06')
        
    def testFair07(self):
        self.runWorkload('fair07')
        
    def testFair08(self):
        self.runWorkload('fair08')
        
    def testFair09(self):
        self.runWorkload('fair09')
        
    def testFair10(self):
        self.runWorkload('fair10')
        
    def testFair11(self):
        self.runWorkload('fair11')
        
    def testFair12(self):
        self.runWorkload('fair12')
        
    def testFair13(self):
        self.runWorkload('fair13')
        
    def testFair14(self):
        self.runWorkload('fair14')
        
    def testFair15(self):
        self.runWorkload('fair15')
        
    def testFair16(self):
        self.runWorkload('fair16')
        
    def testFair17(self):
        self.runWorkload('fair17')
    
    def testFair18(self):
        self.runWorkload('fair18')
    
    def testFair19(self):
        self.runWorkload('fair19')
    
    def testFair20(self):
        self.runWorkload('fair20')
    
    def testFair21(self):
        self.runWorkload('fair21')
    
    def testFair22(self):
        self.runWorkload('fair22')
    
    def testFair23(self):
        self.runWorkload('fair23')
    
    def testFair24(self):
        self.runWorkload('fair24')
    
    def testFair25(self):
        self.runWorkload('fair25')
    
    def testFair26(self):
        self.runWorkload('fair26')
    
    def testFair27(self):
        self.runWorkload('fair27')
    
    def testFair28(self):
        self.runWorkload('fair28')
    
    def testFair29(self):
        self.runWorkload('fair29')
    
    def testFair30(self):
        self.runWorkload('fair30')
    
    def testFair31(self):
        self.runWorkload('fair31')
    
    def testFair32(self):
        self.runWorkload('fair32')
    
    def testFair33(self):
        self.runWorkload('fair33')
    
    def testFair34(self):
        self.runWorkload('fair34')
    
    def testFair35(self):
        self.runWorkload('fair35')
    
    def testFair36(self):
        self.runWorkload('fair36')
    
    def testFair37(self):
        self.runWorkload('fair37')
    
    def testFair38(self):
        self.runWorkload('fair38')
    
    def testFair39(self):
        self.runWorkload('fair39')
        
    def testFair40(self):
        self.runWorkload('fair40')


    def runWorkload(self, wlname):
        self.assert_(True)
        
        fwinst = 50000000
        checkpoints.Checkpoint.generateCheckpoint(wlname, 4, fwinst, "RingBased")
        
        print "Running workload "+wlname+"..."
        
        siminsts = 1000000
        
        m5cmd = M5Command()
        m5cmd.setUpTest(wlname, 4, "RingBased", 1)
        m5cmd.setArgument("MEMORY-BUS-SCHEDULER", "RDFCFS") 
        m5cmd.setArgument("USE-CHECKPOINT", ".")
        m5cmd.setArgument("SIMINSTS", siminsts)
        m5cmd.setExpectedComInsts(siminsts)
        
        #TODO: insert committed inst check when stats parsing has been implemented
        success = m5cmd.run(self.testID, "detailedCPU.*COM:count.*", False)
        self.assert_(success)
        
        self.testID += 1

if __name__ == "__main__":
    unittest.main()