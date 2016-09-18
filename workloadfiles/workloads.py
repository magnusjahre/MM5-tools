'''
Created on Dec 12, 2010

@author: jahre
'''

import pickle
import deterministic_fw_wls
import os

# mcf0 removed due to very long simulation time
specnames = ['gzip0', 'vpr0', 'gcc0', 'crafty0', 'parser0', 'eon0', 'perlbmk0', 'gap0', 'bzip0', 'twolf0', 'wupwise0', 'swim0', 'mgrid0', 'applu0', 'galgel0', 'art0', 'equake0', 'facerec0', 'ammp0', 'lucas0', 'fma3d0', 'sixtrack0' ,'apsi0', 'mesa0', 'vortex10']
spec2006names = ['s6-bzip2', 's6-gcc', 's6-mcf', 's6-gobmk', 's6-hmmer', 's6-sjeng', 's6-libquantum', 's6-h264ref', 's6-omnetpp', 's6-astar', 's6-bwaves', 's6-gamess', 's6-milc', 's6-zeusmp', 's6-gromacs', 's6-cactusADM', 's6-leslie3d', 's6-namd', 's6-dealII', 's6-soplex', 's6-povray', 's6-calculix', 's6-gemsFDTD', 's6-tonto', 's6-lbm', 's6-sphinx3', 's6-wrf']

ALL = 0
FAIR_WL = 1
TYPED_WL = 2

typedWorkloadIdentifiers = ["h", "m", "l"]

def makeTypeTitle(type, num):
    return "t-"+type+"-"+str(num)

def getTypeIDFromTitle(title):
    try:
        return title.split("-")[1]
    except:
        raise Exception("Typed workload parse error on workload "+str(title))


def isWorkloadType(wltitle, typeletter):
    if typeletter == None:
        return True
    
    if typeletter not in typedWorkloadIdentifiers:
        raise Exception("No workload type identifier "+str(typeletter)+". Candidates are "+str(typedWorkloadIdentifiers))
    
    wltype = getTypeIDFromTitle(wltitle)
    if wltype == typeletter:
        return True
    else:
        return False

def parseTypeString(typestr):
    if typestr == "all":
        return ALL
    if typestr == "fair":
        return FAIR_WL
    if typestr == "typed":
        return TYPED_WL
    
    raise Exception("Unknown workload type "+typestr+", candidates are all, fair and typed")

def getAllBenchmarks():
    bms = []
    for b in spec2006names:
        bms.append(b)
    for b in specnames:
        bms.append(b)
    return bms

class Workload:
    
    def __init__(self):
        self.benchmarks = []
    
    def addBenchmark(self, bm):
        self.benchmarks.append(bm)
        
    def containsBenchmark(self, bm):
        if bm in self.benchmarks:
            return True
        return False
    
    def countBenchmark(self, bm):
        cnt = 0
        for b in self.benchmarks:
            if b == bm:
                cnt += 1
        return cnt
    
    def getNumBms(self):
        return len(self.benchmarks)

    def __str__(self):
        out = ""
        for b in self.benchmarks:
            out += " "+b
        return out

class UnknownWorkloadException(Exception):
    
    def __init__(self, message):
        self.message = message
        
    def __str__(self):
        return self.message    
     

class Workloads:

    def __init__(self):
        
        infile = open(self._findPickleFile("workloadfiles/typewls.pkl"))
        self.typedwls = pickle.load(infile)
        infile.close()
        
        self.fairwls = deterministic_fw_wls.workloads
        
        self.workloadnames = {}
        self.randomwlnames = {}
        self.typedwlnames = {}
        for np in self.typedwls:
            self.workloadnames[np] = []
            self.randomwlnames[np] = []
            self.typedwlnames[np] = []
            
            for type in self.typedwls[np]:
                for i in range(len(self.typedwls[np][type])):
                    self.workloadnames[np].append(makeTypeTitle(type, i))
                    self.typedwlnames[np].append(makeTypeTitle(type, i))
            if np in deterministic_fw_wls.workloads:
                for wlname in deterministic_fw_wls.getWorkloads(np):
                    self.workloadnames[np].append(wlname)
                    self.randomwlnames[np].append(wlname)
                
        self.workloadwidth = 10
        self.benchmarkwidth = 15 

    def setColumnWidth(self, wlwidth, bmwidth):
        self.workloadwidth = wlwidth
        self.benchmarkwidth = bmwidth

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

    def getWorkloads(self, np, type = ALL):
        if type == ALL:
            return self.workloadnames[np]
        elif type == TYPED_WL:
            return self.typedwlnames[np]
        elif type == FAIR_WL:
            return self.randomwlnames[np]
        
        raise Exception("Unknown workload type in workloads.getWorkloads()")

    def getBms(self, wl, np, appendZero = False):
        if wl.startswith("t-"):
            return self.getTypedBms(np, wl)
        elif wl.startswith("fair"):
            return deterministic_fw_wls.getBms(wl, np, appendZero)
        
        raise UnknownWorkloadException("Unknown workload "+wl)
        
    def getTypedBms(self, np, name):
        try:
            prefix, type, num = name.split("-")
        except:
            raise Exception("Malformed typed benchmark name: "+str(name))
        
        return self.typedwls[np][type][int(num)].benchmarks

    def printBms(self, wl, np):
        bms = self.getBms(wl, np) 
        print wl.ljust(self.workloadwidth),
        for b in bms:
            print b.ljust(self.benchmarkwidth),
        print

    def printWorkloads(self, np, type = ALL):
        print "Workload".ljust(self.workloadwidth),
        for p in range(np):
            print ("CPU "+str(p)).ljust(self.benchmarkwidth),
        print
            
        printnames = self.workloadnames[np]
        if type == FAIR_WL:
            printnames = self.randomwlnames[np]
        elif type == TYPED_WL:
            printnames = self.typedwlnames[np]
            
        for w in printnames:
            self.printBms(w, np)
        
    def getWorkloadsByType(self, np, wltype):
        if wltype not in self.typedwls[np]:
            raise Exception("Workload subtype "+str(wltype)+" does not exist, candidates are "+str(self.typedwls[np].keys()))
        
        names = []
        for i in range(len(self.typedwls[np][wltype])):
            names.append(makeTypeTitle(wltype, i))
        
        return names
