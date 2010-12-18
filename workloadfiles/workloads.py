'''
Created on Dec 12, 2010

@author: jahre
'''

import pickle
import deterministic_fw_wls
import os

def makeTypeTitle(type, num):
    return "t-"+type+"-"+str(num)

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
        
        infile = open(self._findPickleFile("workloadfiles/typewls.pkl"))
        self.typedwls = pickle.load(infile)
        infile.close()
        
        self.fairwls = deterministic_fw_wls.workloads
        
        self.workloadnames = {}
        for np in self.typedwls:
            self.workloadnames[np] = []
            for type in self.typedwls[np]:
                for i in range(len(self.typedwls[np][type])):
                    self.workloadnames[np].append(makeTypeTitle(type, i))
            for wlname in deterministic_fw_wls.getWorkloads(np):
                self.workloadnames[np].append(wlname)

    def _findPickleFile(self, relpath):
        pypath = os.getenv("PYTHONPATH")
        if pypath == None:
            raise Exception("PYTHONPATH not found")
        
        pathentries = pypath.split(":")
        for e in pathentries:
            testpath = e+"/"+relpath
            if os.path.exists(testpath):
                return testpath
        
        raise Exception("Pickled workloadfile not found in PYTHONPATH")

    def getWorkloads(self, np):
        return self.workloadnames[np]

    def getBms(self, wl, np, appendZero = False):
        if wl.startswith("t-"):
            return self.getTypedBms(np, wl)
        return deterministic_fw_wls.getBms(wl, np, appendZero)
        
    def getTypedBms(self, np, name):
        try:
            prefix, type, num = name.split("-")
        except:
            raise Exception("Malformed typed benchmark name: "+str(name))
        
        return self.typedwls[np][type][int(num)].benchmarks
