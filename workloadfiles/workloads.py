'''
Created on Dec 12, 2010

@author: jahre
'''

import pickle
import deterministic_fw_wls

class Workload:
    
    def __init__(self):
        self.benchmarks = []
    
    def addBenchmark(self, bm):
        self.benchmarks.append(bm)
        
    def containsBenchmark(self, bm):
        if bm in self.benchmarks:
            return True
        return False
    
    def getNumBms(self):
        return len(self.benchmarks)

    def __str__(self):
        out = ""
        for b in self.benchmarks:
            out += " "+b
        return out

class Workloads:

    FAIR_WL = 0
    TYPED_WL = 1

    def __init__(self):
        
        #FIXME: get path in better way
        infile = open("/home/jahre/workspace/m5sim-tools/workloadfiles/typewls.pkl")
        self.typedwls = pickle.load(infile)
        infile.close()
        
        self.fairwls = deterministic_fw_wls.workloads

    def getWorkload(self, name, np):    
        raise Exception("getWorkload() not implemented")
    
    def getWorkloads(self, np):
        raise Exception("getWorkloads() not implemented")

    def getBms(self, wl, np, appendZero = False):
        raise Exception("getBms() not implemented")
        