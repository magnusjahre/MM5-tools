'''
Created on Jun 15, 2012

@author: jahre
'''
import unittest
import statparse.util.plotRequestTrace as prt
from statparse.util.plotRequestTrace import Request
from statparse.util.plotRequestTrace import Compute


class Test(unittest.TestCase):

    def setUpReqs(self, durations):
        reqs = []
        cnt = 0
        for start, end in durations:
            newreq = Request([])
            newreq.setTestState(start, end, cnt)
            reqs.append(newreq)
            cnt += 1
        return reqs

    def setUpCompute(self, durations):
        coms = []
        cnt = 0
        for start, end in durations:
            coms.append(Compute(start, end, "comp"+str(cnt)))
            cnt += 1
        return coms        

    def testOverlapStart(self):        
        reqs = self.setUpReqs([(15,25)])
        coms = self.setUpCompute([(0,10), (20,30)])
        overlap = prt.findOverlap(reqs, coms)
        self.assertEqual(overlap, 5, "Partial start overlap should be 5")
        
    def testOverlapEnd(self):        
        reqs = self.setUpReqs([(5,15), (21,35)])
        coms = self.setUpCompute([(0,10), (20,30)])
        overlap = prt.findOverlap(reqs, coms)
        self.assertEqual(overlap, 5+9, "Partial start overlap should be 14")
        
    def testCompleteOverlap(self):        
        reqs = self.setUpReqs([(15,35)])
        coms = self.setUpCompute([(0,10), (20,30)])
        overlap = prt.findOverlap(reqs, coms)
        self.assertEqual(overlap, 10, "Partial start overlap should be 10")

    def testParaOverlapSimple(self):        
        reqs = self.setUpReqs([(15,25), (20, 30)])
        coms = self.setUpCompute([(0,10), (20,30)])
        overlap = prt.findOverlap(reqs, coms)
        self.assertEqual(overlap, 10, "Partial start overlap should be 10")
        
    def testParaOverlapPipeline(self):
        duration = []
        for i in range(5, 30, 2):
            duration.append( (i, i+4))
            
        reqs = self.setUpReqs(duration)
        coms = self.setUpCompute([(0,10), (20,30)])
        overlap = prt.findOverlap(reqs, coms)
        self.assertEqual(overlap, 15, "Partial start overlap should be 15")
        
    def testPartialOverlapWithPara(self):
        reqs = self.setUpReqs([(15,22), (18, 23), (24, 28), (25, 27), (29, 31)])
        coms = self.setUpCompute([(0,10), (20,30)])
        overlap = prt.findOverlap(reqs, coms)
        self.assertEqual(overlap, 8, "Partial start overlap should be 15")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testOverlap']
    unittest.main()