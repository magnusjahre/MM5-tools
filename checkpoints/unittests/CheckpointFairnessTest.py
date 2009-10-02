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
import fairmha.interference.interferencemethods as intmethods
import fairmha.interference.evaluateSampleSizeAccuracy as evalSamples

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
        m5cmd.setArgument("INTERFERENCE-MANAGER-SAMPLE-SIZE", 64)
        m5cmd.setArgument("INTERFERENCE-MANAGER-RESET-INTERVAL", 64)
        m5cmd.setArgument("USE-AVERAGE-ALONE-LATENCIES", "F")
        m5cmd.setArgument("MEMORY-BUS-SCHEDULER", "RDFCFS")
        m5cmd.setArgument("MEMORY-BUS-PRIORITY-SCHEME", "FCFS")
        m5cmd.setArgument("MEMORY-BUS-PAGE-POLICY", "OpenPage")
        m5cmd.setArgument("WRITEBACK-OWNER-POLICY", "shadow-tags")
        m5cmd.setArgument("USE-PURE-HEAD-POINTER-MODEL", "T")
        m5cmd.setArgument("CONTROLLER-INTERFERENCE-BUFFER-SIZE", 64)
        m5cmd.setArgument("READY-FIRST-LIMIT-ALL-CPUS", 3)

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
        
        if np > 1:
            for filename in glob.glob("CPU*Trace.txt"):
                os.rename(filename, statfiledir+"/"+"shared-"+filename)
        else:
            for filename in glob.glob("CPU0*Trace.txt"):
                os.rename(filename, statfiledir+"/"+wlOrBm+"-"+filename)
        
        if np not in self.statfiles:
            self.statfiles[np] = {}
        self.statfiles[np][wlOrBm] = newStatfilename
        
    def cleanDirectories(self):
        if not os.path.exists(statfiledir):
            os.mkdir(statfiledir)
        
        traceDir = statfiledir+"/trace_estimate_tmp"
        if os.path.exists(traceDir):
            for f in glob.glob(traceDir+"/*"):
                print "removing "+f
                os.remove(f)
            print "removing "+traceDir
            os.rmdir(traceDir)
        
        for f in glob.glob(statfiledir+"/*"):
            print "removing "+f
            os.remove(f)
        
    def testCheckpointFairness(self):
        
        wlname = "fair01"
        np = 4
        memsys = "RingBased"
        fwinst = 10000000

        self.cleanDirectories()

        checkpoints.Checkpoint.generateCheckpoint(wlname, np, fwinst, memsys, -1)
        
        bms = workloads.getBms(wlname, np, True)
        siminsts = 1000000
        
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
        
        os.chdir(statfiledir)
        cpuID = 0
        results = {}
        for bm in bms:
            basename = wlname+"-"+bm+"-"+str(cpuID)
            results = intmethods.getTraceEstimateError("../shared-CPU"+str(cpuID)+"InterferenceTrace.txt",
                                                       "../"+bm+"-CPU0LatencyTrace.txt", 
                                                       [1],
                                                       "../shared-CPU"+str(cpuID)+"LatencyTrace.txt",
                                                       basename)
            statres.printSampleSizeResults(evalSamples.computeResultEstimators(results), 2)
            cpuID += 1
        os.chdir("..")

if __name__ == "__main__":
    unittest.main()