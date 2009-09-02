
import sys
import os

import IniFile
import checkpoints
import deterministic_fw_wls as workloads

from CacheState import CacheState
from m5test.M5Command import M5Command

__metaclass__ = type    

def mergeSharedCache(checkpoints, outfilename):
    
    bankStates = {}
    
    for cp in checkpoints:
        for bank in cp.sharedCaches:
            if bank not in bankStates:
                bankStates[bank] = []
            bankStates[bank].append(cp.sharedCaches[bank])
    
    bankNames = bankStates.keys()
    bankNames.sort()
    newSharedCaches = {}
    for bankName in bankNames:
        mergedState = CacheState(bankName, -1)
        mergedState.merge(bankStates[bankName], len(checkpoints))
        newSharedCaches[bankName] = mergedState
        
    newCheckpoint = Checkpoint()
    newCheckpoint.sharedCaches = newSharedCaches
    newCheckpoint.writeToFile(outfilename)

def generateCheckpoint(workload, np, fwInsts, memsys, simpoint = -1):
    
    curWorkload = workloads.getBms(workload, np)
    
    if simpoint == -1:
        for bm in workloads.getBms(workload, np):
            bmname = bm+"0"            
            chkPath = checkpoints.getCheckpointDirectory(1, memsys, bmname)
            if os.path.exists(chkPath):
                print "Checkpoint allready exists for "+bmname+", skipping..."
                continue
            print "Generating checkpoint for "+bmname+" with "+str(fwInsts)+" instructions in checkpoint"
            runCheckpointGeneration(bmname, fwInsts, memsys, np)
    else:
        print "Simpoint ID "+str(simpoint)+" provided, assuming that single core checkpoints are provided in the current directory"
        
    outdir = checkpoints.getCheckpointDirectory(np, memsys, workload, simpoint)
    if not os.path.exists(outdir):
        os.mkdir(checkpoints.getCheckpointDirectory(np, memsys, workload, simpoint))
    outfilename = outdir+"/m5.cpt"
    
    checkpoints.prepareOutputFile(outfilename)
    
    wlCheckpoints = []
    cpuID = 0
    for bm in curWorkload:
        checkPath = checkpoints.getCheckpointDirectory(1, memsys, bm+"0", simpoint)
        checkFile = checkPath+"/m5.cpt" 
        print "Reading checkpoint from file "+checkFile
        newCheckpoint = Checkpoint()
        newCheckpoint.createFromFile(checkFile, outfilename, cpuID)
        wlCheckpoints.append(newCheckpoint)
        cpuID += 1

    print "Merging and dumping shared cache state"
    mergeSharedCache(wlCheckpoints, outfilename)
    
    return outfilename

def runCheckpointGeneration(bm, fwinsts, memsys, np):
    m5cmd = M5Command()
    m5cmd.setUpTest(bm, 1, memsys, 1)
    
    m5cmd.setArgument("MEMORY-ADDRESS-OFFSET", 0)
    m5cmd.setArgument("MEMORY-ADDRESS-PARTS", np)
    m5cmd.setArgument("MEMORY-BUS-SCHEDULER", "RDFCFS") 
    m5cmd.setArgument("GENERATE-CHECKPOINT", "")
    m5cmd.setArgument("SIMINSTS", fwinsts)
    m5cmd.setExpectedComInsts(fwinsts)
    
    success = m5cmd.run(0, "simpleCPU.*num_insts.*")
    if not success:
        print "Error: M5 did not complete successfully, checkpoint generation failed"
        sys.exit(-1)

class Checkpoint():

    def __init__(self):
        self.sharedCaches = None
    
    def createFromFile(self, filename, outfilename, newCoreID):
        self.sharedCaches = IniFile.read(filename, outfilename, newCoreID)
        
    def writeToFile(self, filename):
        IniFile.write(filename, self.sharedCaches)
        
        
