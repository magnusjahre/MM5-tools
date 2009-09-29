#!/usr/bin/python
from checkpoints.checkpointConverter import CheckpointConverter
import shutil
import glob
import sys
import os

from optparse import OptionParser
import Checkpoint
import copyResFiles
import checkpoints

import simpoints3
import deterministic_fw_wls as workloads

def parseAargs():
    parser = OptionParser(usage="generateCheckpoint.py ")
    
    parser.add_option("--from-experiment", action="store_true", dest="fromExp", default="", help="Use workload table and pbsconfig.py to generate checkpoints")
    
    parser.add_option("--copy-checkpoint-files", action="store", dest="checkpointDestination", default="", help="Copy checkpoints and simulator files to directory")
    
    parser.add_option("--convert-checkpoint", action="store", dest="convertCheckpointFile", default="", help="Convert the provided checkpoint file from the old format to the new storage efficient format")
    
    parser.add_option("--np", action="store", dest="np", type="int", default=4, help="The number of CPUs to use in checkpoint")
    parser.add_option("--workload", action="store", dest="workload", default="fair01", help="Workload")
    parser.add_option("--fwinsts", action="store", dest="fwinsts", type="int", default=50000000, help="The number of instructions to use when generating the checkpoint")
    parser.add_option("--memsys", action="store", dest="memsys", default="RingBased", help="The memory system to use for simulations")
    
    opts, args = parser.parse_args()
    
    return opts, args

def createCheckpointsFromExperiment():
    
    for np, wl, mem, simpoint, fw in buildPossibleParams():
        if Checkpoint.prerequisiteFilesExist(wl, np, mem, simpoint):
            printParameters(np, wl, mem, simpoint, fw)
            path = Checkpoint.generateCheckpoint(wl, np, fw, mem, simpoint)
            print "Generated checkpoint at "+path
        else:
            print "Files needed for np "+str(np)+", workload "+wl+", memsys "+mem+" and simpoint "+str(simpoint)+" not found"
            print "Skipping..."
    return 0

def buildPossibleParams():
    
    nps = [4, 8, 16]
    memsys = ["CrossbarBased", "RingBased"]
    fw = -1
    
    params = []
    for np in nps:
        for wl in workloads.getWorkloads(np):
            for mem in memsys:
                for simpoint in range(simpoints3.maxk):
                    params.append([np, wl, mem, simpoint, fw])
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
    
    otherResFiles = ["res*txt", "config.ini", "config.py", "config.out"]
    
    if not os.path.exists(destination):
        os.mkdir(destination)
    
    pbsconfig = __import__("pbsconfig")  
    for cmd, params in pbsconfig.commandlines:
        expdir = pbsconfig.get_unique_id(params)
        
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
        simpoint = params["USE-SIMPOINT"]
        
        
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
        
        assert chkptDir in checkpointfiles
        
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
    
    simpoint = -1
    printParameters(opts.np, opts.workload, opts.memsys, simpoint, opts.fwinsts)
    
    chkptPath = Checkpoint.generateCheckpoint(opts.workload, opts.np, opts.fwinsts, opts.memsys, simpoint)
    
    print
    print "Generated checkpoint at "+chkptPath
    print

if __name__ == '__main__':
    main()