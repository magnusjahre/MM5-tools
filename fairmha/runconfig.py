#!/usr/bin/python    

import sys
import subprocess
import os
import platform
import re
from optparse import OptionParser
 
PBS_DIR_NAME = "pbsfiles"
PBS_PM_DIR_NAME = PBS_DIR_NAME+"-priv-mode"

class ComputerParams:
    
    # Use queue = None to not set queue name in PBS file
    #
    # Memory requirements is in MB and walltime in hours
    def __init__(self, opts):
        
        compname = platform.node()
        
        self.queue = opts.queue
        self.projectNum = None
        self.perProcMem = {1:1900, 2:1900, 4:1900, 8:2300, 16:4032}
        
        if re.search("stallo", compname):
            info("Stallo run detected...")
            self.ppn = {1:16, 2:16, 4:16, 8:14, 16:8}
            self.walltime = {1:10, 2:30, 4:60, 8:168, 16:168}
            self.projectNum = "nn4650k"
        
        elif re.search("rocks.hpc.ntnu.no", compname):
            info("Kongull run detected...")
            self.ppn = {1:12, 2:12, 4:12, 8:10, 16:6}
            self.walltime = {1:10, 2:30, 4:60, 8:168, 16:168}
            if opts.queue == "default":
                self.projectNum = "acc-idi"
            elif opts.queue == "optimist":
                self.projectNum = "freecycle"
            
        else:
            info("No HPC cluster detected, using fallback values...")
            self.ppn = {1:8, 2:8, 4:8, 8:8, 16:4}
            self.walltime = {1:10, 2:30, 4:60, 8:168, 16:168}
            
        if opts.walltime != 0:
            info("Setting all walltime limits to provided value "+str(opts.walltime))
            for key in self.walltime:
                self.walltime[key] = opts.walltime
                    
    
    def getHeader(self, np):
    
        lines = []
    
        lines.append("#!/bin/bash")
        lines.append("#PBS -N m5sim")
        lines.append("#PBS -lwalltime="+self.getWalltime(np)+":00:00")
        lines.append("#PBS -m a")
        if self.queue != None:
            lines.append("#PBS -q "+self.queue)
        lines.append("#PBS -j oe")
    
        lines.append("#PBS -lnodes=1:ppn="+self.getPPN(np)+",pvmem="+self.getPerProcMem(np)+"mb")
        
        if self.projectNum != None:
            lines.append("#PBS -A "+self.projectNum)

        lines.append("")
        lines.append("cd "+os.getcwd())
    
        header = ""
        for l in lines:
            header += l+"\n"
    
        return header+"\n"
    
    def getPPN(self, np):
        return str(self.ppn[np])
    
    def getWalltime(self, np):
        return str(self.walltime[np])
    
    def getPerProcMem(self, np):
        return str(self.perProcMem[np])

class M5Command:
    
    def __init__(self, cmd, id):
        self.cmd = cmd
        self.id = id

class BatchCommands:
    
    def __init__(self, compenv, opts):
        
        self.compenv = compenv
        self.opts = opts
        
        self.commands = []
        self.fileID = 0
        self.issuedCommands = 0
        self.currentNp = -1
        
    def addCommand(self, command, np, privModeExperiment):
        
        if self.currentNp == -1:
            self.currentNp = np
        elif self.currentNp != np:
            info("New CPU count ("+str(self.currentNp)+" vs. "+str(np)+"), flushing commands...")
            self.issueBatchJob(privModeExperiment)
            self.currentNp = np
        
        assert len(self.commands) < self.compenv.ppn[self.currentNp]
        self.commands.append(command)
        
        if len(self.commands) == self.compenv.ppn[self.currentNp]:
            self.issueBatchJob(privModeExperiment)
            assert len(self.commands) == 0 
        
    def issueBatchJob(self, privModeExperiment):
    
        if self.commands == []:
            return
    
        usedir = PBS_DIR_NAME
        if privModeExperiment:
            usedir = PBS_PM_DIR_NAME
    
        runfilepath = usedir+'/runfile'+str(self.fileID)+'.pbs'
    
        output = open(runfilepath,'w')
        output.write(self.compenv.getHeader(self.currentNp))
        
        for command in self.commands:
            print >> output, "rm -Rf "+command.id # take care of restarts
            print >> output, "mkdir "+command.id
            print >> output, "cd "+command.id
            print >> output, "echo > .rundir"
            print >> output, command.cmd + '\n\n'
            print >> output, "cd .."
        
            self.issuedCommands += 1
        
        print >> output, "wait"
        print >> output, ""
    
        self.commands = []
    
        output.close()
        
        info("Attempting to submit file "+runfilepath)
        
        if not self.opts.dryrun:
            subprocess.call(['qsub', runfilepath])
        else:
            info("Dry-run, skipping...")
        
        self.fileID += 1

def fatal(message):
    print "FATAL: "+message
    sys.exit()

def info(message):
    print "INFO: "+message

def parseParams():
    parser = OptionParser(usage="runconfig.py [options]")
    
    parser.add_option("--dry-run", action="store_true", dest="dryrun", default=False, help="Do not submit jobs to the cluster")
    parser.add_option("--inst-samp-priv-mode", action="store_true", dest="instSampPrivMode", default=False, help="Submit private mode jobs with sample points taken from a shared mode experiment")
    parser.add_option("--queue", action="store", dest="queue", default=None, help="PBS queue to submit jobs to")
    parser.add_option("--walltime", action="store", type="int", dest="walltime", default=0, help="PBS walltime limit in hours")
    opts, args = parser.parse_args()
    
    if len(args) != 0:
        fatal("runconfig.py takes no parameters")
    
    compenv = ComputerParams(opts)
    
    return opts, compenv

    
def main():
    
    opts, computerEnv = parseParams()

    if not os.path.exists("pbsconfig.py"):
        fatal("Cannot find file pbsconfig.py in current directory")

    pbsconfig = __import__("pbsconfig")

    try:
        if opts.instSampPrivMode:
            os.mkdir(PBS_PM_DIR_NAME)
        else:
            os.mkdir(PBS_DIR_NAME)
    except:
        fatal("Could not create directory for pbsfiles because it already exists")
    
    commandlines = pbsconfig.commandlines
    if opts.instSampPrivMode:
        commandlines = pbsconfig.privModeCommandlines
    
    batchCommands = BatchCommands(computerEnv, opts)
    for commandline, param in commandlines:
        command = M5Command(commandline,  pbsconfig.get_unique_id(param))
        batchCommands.addCommand(command, pbsconfig.get_np(param), opts.instSampPrivMode)        
    batchCommands.issueBatchJob(opts.instSampPrivMode)

    print "Submitted "+str(batchCommands.issuedCommands)+" experiments in "+str(batchCommands.fileID)+" files"
    

if __name__ == '__main__':
    main()
