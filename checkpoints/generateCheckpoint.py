#!/usr/bin/env python
from checkpoints.checkpointConverter import CheckpointConverter
import shutil
import glob
import sys
import os

from optparse import OptionParser
import Checkpoint
import copyResFiles
import checkpoints

import simpoints.simpoints as simpoints

import workloadfiles.workloads as wlmod
workloads = wlmod.Workloads()

from m5test.M5Command import M5Command

def parseAargs():
    parser = OptionParser(usage="generateCheckpoint.py ")
    
    parser.add_option("--from-experiment", action="store_true", dest="fromExp", default=False, help="Use workload table and pbsconfig.py to generate checkpoints")
    parser.add_option("--test-checkpoints", action="store_true", dest="test", default=False, help="Check that M5 starts with all generated simpoints")
    parser.add_option("--test-size", action="store", dest="siminsts", type="int", default=1000, help="The number of instructions to simulate for (DEFAULT 1000)")
    
    parser.add_option("--copy-checkpoint-files", action="store", dest="checkpointDestination", default="", help="Copy checkpoints and simulator files to directory")
    
    parser.add_option("--convert-checkpoint", action="store", dest="convertCheckpointFile", default="", help="Convert the provided checkpoint file from the old format to the new storage efficient format")
    
    parser.add_option("--np", action="store", dest="np", type="int", default=4, help="The number of CPUs to use in checkpoint")
    parser.add_option("--workload", action="store", dest="workload", default="fair01", help="Workload")
    parser.add_option("--fwinsts", action="store", dest="fwinsts", type="int", default=50000000, help="The number of instructions to use when generating the checkpoint")
    parser.add_option("--memsys", action="store", dest="memsys", default="RingBased", help="The memory system to use for simulations")
    
    opts, args = parser.parse_args()
    
    return opts, args

def createCheckpointsFromExperiment():
    
    print "Setting up private mode baselines"
    for np, wl, mem, simpoint, fw in buildPossibleParams():
        if np != 4:
            curWorkload = workloads.getBms(wl, np, True)
            for bm in curWorkload:
                actualPath = checkpoints.getCheckpointDirectory(4, mem, bm, simpoint)
                checkPath = checkpoints.getCheckpointDirectory(np, mem, bm, simpoint)
                checkFile = checkPath+"/m5.cpt"
                if not os.path.exists(checkFile):
                    print "Linking", actualPath, checkPath
                    os.symlink(actualPath, checkPath)
    
    print
    print "Generating multi-core checkpoints"
    for np, wl, mem, simpoint, fw in buildPossibleParams():
        if Checkpoint.prerequisiteFilesExist(wl, np, mem, simpoint):
            printParameters(np, wl, mem, simpoint, fw)
            path = Checkpoint.generateCheckpoint(wl, np, fw, mem, simpoint)
            print "Generated checkpoint at "+path
        else:
            print "Files needed for np "+str(np)+", workload "+wl+", memsys "+mem+" and simpoint "+str(simpoint)+" not found"
            print "Skipping..."
    return 0

def testCheckpoints(siminsts):
    
    testID = 0
    
    for b in wlmod.getAllBenchmarks():
        m5cmd = M5Command()
        m5cmd.setUpTest(b, 1, "RingBased", 1)
        m5cmd.setArgument("MEMORY-BUS-SCHEDULER", "RDFCFS") 
        m5cmd.setArgument("USE-CHECKPOINT", ".")
        m5cmd.setArgument("SIMINSTS", siminsts)
        m5cmd.setExpectedComInsts(siminsts)
        
        success = m5cmd.run(testID, "detailedCPU.*COM:count.*", False)
        
        if success:
            print b, "started successfully"
        else:
            print b, "FAILED!"
            
        testID += 1

def buildPossibleParams():
    
    # TODO: provide more robust implementation
    
    #nps = [4, 8, 16]
    #memsys = ["CrossbarBased", "RingBased"]
    nps = [2, 4, 8]
    memsys = ["RingBased"]
    fw = -1
    
    params = []
    for np in nps:
        for wl in workloads.getWorkloads(np, wlmod.TYPED_WL):
            for mem in memsys:
                #for simpoint in range(simpoints.maxk):
                #    params.append([np, wl, mem, simpoint, fw])
                params.append([np, wl, mem, -1, fw])
    return params

def printParameters(np, wl, memsys, simpoint, fw):
    print "Generating checkpoint with parameters:"
    print "NP:                           "+str(np)
    print "Workload:                     "+str(wl)
    print "Simulated memory system:      "+str(memsys)
    if fw != -1:
        print "Checkpoint instruction count: "+str(fw)
    if simpoint != -1:
        print "Simpoint number:              "+str(simpoint)
    print

def copyCheckpointFiles(destination, opts):
    
    otherResFiles = ["res*txt", "config.ini", "config.py", "config.out", "simoutput.txt"]
    
    if not os.path.exists(destination):
        os.mkdir(destination)
    
    pbsconfig = __import__("pbsconfig")  
    for cmd, params in pbsconfig.commandlines:
        expdir = pbsconfig.get_unique_id(params)
        
        print "Processing directory "+expdir
        
        np = pbsconfig.get_np(params)
        assert np == 1
        bm = pbsconfig.get_benchmark(params)
        params = pbsconfig.get_variable_params(params)
        
        if  "MEMORY-SYSTEM" in params:
            memsys = params["MEMORY-SYSTEM"]
        else:
            print "No memory system in variable parameters, using value "+opts.memsys+" from commandline (or default RingBased)"
            memsys = opts.memsys
        
        
        parts = params["MEMORY-ADDRESS-PARTS"]
        
        if "USE-SIMPOINT" in params:
            simpoint = params["USE-SIMPOINT"]
        else:
            simpoint = -1
        
        
        resultfiles = []
        skipFiles = copyResFiles.resultfiles + otherResFiles
        os.chdir(expdir)
        for notCopyName in skipFiles:
            names = glob.glob(notCopyName)
            for name in names:
                resultfiles.append(name)
        os.chdir("..")
        
        
        chkptDir = checkpoints.getCheckpointDirectory(parts, memsys, bm, simpoint)
        checkpointfiles = []
        content = os.listdir(expdir)
        for filename in content:
            if filename not in resultfiles:
                checkpointfiles.append(filename)
        
        if chkptDir not in checkpointfiles:
            print "ERROR: experiment directory "+expdir+" does not contain a checkpoint, skipping"
        else:
            destinationPath = destination+"/"+chkptDir 
            if os.path.exists(destinationPath):
                print "Destination directory "+destinationPath+" exists, skipping"
            else:
                print "Copying from "+expdir+" to "+destinationPath
                os.mkdir(destinationPath)
                print "Copying checkpoint..."
                shutil.copy(expdir+"/"+chkptDir+"/m5.cpt", destinationPath)
                for file in checkpointfiles:
                    filepath = expdir+"/"+file
                    if file != chkptDir:
                        if not os.path.islink(filepath):
                            print "Copying file "+filepath
                            if os.path.isdir(filepath):
                                shutil.copytree(filepath, destinationPath+"/"+file)
                            else:
                                shutil.copy(filepath, destinationPath)
                        else:
                            print "Skipping symlink "+filepath
                    
        
    return 0

def convertCheckpointFile(filename):
    if "/" in filename:
        print "ERROR: This script must be run in the checkpoint directory for M5 to find the produced files"
        return -1
    
    converter = CheckpointConverter(filename)
    converter.convert()
    return 0

def main():
    
    opts,args = parseAargs()
    
    print
    print "Automatic checkpoint generation for multiprogrammed workloads"
    print
    
    if opts.checkpointDestination:
        sys.exit(copyCheckpointFiles(opts.checkpointDestination, opts))
    
    if opts.fromExp:
        sys.exit(createCheckpointsFromExperiment())
        
    if opts.convertCheckpointFile != "":
        sys.exit(convertCheckpointFile(opts.convertCheckpointFile))
    
    if opts.test:
        sys.exit(testCheckpoints(opts.siminsts))
    
    simpoint = -1
    printParameters(opts.np, opts.workload, opts.memsys, simpoint, opts.fwinsts)
    
    chkptPath = Checkpoint.generateCheckpoint(opts.workload, opts.np, opts.fwinsts, opts.memsys, simpoint)
    
    print
    print "Generated checkpoint at "+chkptPath
    print

if __name__ == '__main__':
    main()
