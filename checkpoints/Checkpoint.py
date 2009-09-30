
import sys
import os
import shutil
import glob

import IniFile
import checkpoints
import deterministic_fw_wls as workloads
import struct

from m5test.M5Command import M5Command

__metaclass__ = type    

NUMBANKS = 4

def mergeSharedCache(np, cptPath, outfilename):
    
    cptfile = open(outfilename, "a") 
    
    for bankID in range(NUMBANKS):
        files = []
        filenames = []
        
        sectionName = "SharedCache"+str(bankID)
        outfile = open(cptPath+"/"+sectionName+"-content.bin", "wb")
        cptfile.write("\n["+sectionName+"]\n")
        cptfile.write("filename="+sectionName+"-content.bin\n")
        
        for cpuID in range(np):
            filename = cptPath+"/SharedCache"+str(bankID)+"-content.bin."+str(cpuID)
            files.append(open(filename, "rb"))
            filenames.append(filename)
        
        mergeFiles(outfile, files)
        
        outfile.close()
        for cpuID in range(np):
            files[cpuID].close()
            
        for filename in filenames:
            os.remove(filename)
            
    cptfile.close()

def mergeFiles(outfile, files):
    
    blockFormat = "=iQIiii"
    blockSize = struct.calcsize(blockFormat)
    
    numBlocks = -1
    for f in files:
        thisBlks = struct.unpack("i", f.read(struct.calcsize("i")))[0]
        if numBlocks == -1:
            numBlocks = thisBlks
            
        if numBlocks != thisBlks:
            raise Exception("cannot merge files with different block counts")
        
    assert numBlocks != -1
    
    outputBlocks = numBlocks*len(files)
    outfile.write(struct.pack("i", outputBlocks))
    
    for b in range(numBlocks):
        cpuID = 0
        for f in files:
            asid,tag,status,oid,poid,set = struct.unpack(blockFormat, f.read(blockSize))
            outfile.write(struct.pack(blockFormat, asid, tag, status, cpuID, poid, set))
            cpuID += 1

def prerequisiteFilesExist(workload, np, memsys, simpoint):
    curWorkload = workloads.getBms(workload, np, True)
    for bm in curWorkload:
        checkPath = checkpoints.getCheckpointDirectory(np, memsys, bm, simpoint)
        checkFile = checkPath+"/m5.cpt"
        if not os.path.exists(checkFile):
            return False
    return True

def moveBinaryFiles(chkPath):
    filenames = glob.glob("*0*.bin")
    for f in glob.glob("SharedCache*.bin"):
        if f not in filenames:
            filenames.append(f)
    for filename in filenames:
        os.rename(filename, chkPath+"/"+filename)

def generateCheckpoint(workload, np, fwInsts, memsys, simpoint):
    
    curWorkload = workloads.getBms(workload, np, True)
    
    if simpoint == -1:
        for bm in workloads.getBms(workload, np, True):        
            chkPath = checkpoints.getCheckpointDirectory(np, memsys, bm)
            if os.path.exists(chkPath):
                print "Checkpoint allready exists for "+bm+", skipping..."
                continue
            print "Generating checkpoint for "+bm+" with "+str(fwInsts)+" instructions in checkpoint"
            runCheckpointGeneration(bm, fwInsts, memsys, np)
            moveBinaryFiles(chkPath)
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
        checkPath = checkpoints.getCheckpointDirectory(np, memsys, bm, simpoint)
        checkFile = checkPath+"/m5.cpt"
        allfiles = os.listdir(checkPath)
        for file in allfiles:
            if file != "m5.cpt":
                newFilePath = "../"+checkPath+"/"+file
                if file.startswith("SharedCache"):
                    newname = file+"."+str(cpuID)
                else:
                    newname = file.replace("0", str(cpuID))
                outpath = outdir+"/"+newname
                if not os.path.exists(outpath):
                    os.symlink(newFilePath, outpath)
                else:
                    print "File "+outpath+" exists, skipping"
        
        print "Reading checkpoint from file "+checkFile
        newCheckpoint = Checkpoint()
        newCheckpoint.createFromFile(checkFile, outfilename, cpuID)
        wlCheckpoints.append(newCheckpoint)
        cpuID += 1

    print "Merging shared caches..."
    mergeSharedCache(np, outdir, outfilename)
    
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
        pass
    
    def createFromFile(self, filename, outfilename, newCoreID):
        IniFile.read(filename, outfilename, newCoreID)
        
        
