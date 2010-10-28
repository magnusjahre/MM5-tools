#!/usr/bin/python    

import sys
import popen2
import os
import pbsconfig
import platform
import re
from optparse import OptionParser

PROJECT_NUM = "nn4650k"
PBS_DIR_NAME = "pbsfiles"

class ComputerParams:

    def __init__(self):
        
        compname = platform.node()
        
        if re.search("stallo", compname):
            info("Stallo run detected...")
            self.ppn = {1:8, 4:8, 8:8, 16:4}                    # processes per node
            self.walltime = {1:10, 4:60, 8:168, 16:168}         # in hours
        
        elif re.search("kongull", compname):
            info("Kongull run detected...")
            self.ppn = {1:12, 4:12, 8:12, 16:6}                    # processes per node
            self.walltime = {1:10, 4:60, 8:168, 16:168}         # in hours
            
        else:
            info("No HPC cluster detected, using fallback values...")
            self.ppn = {1:8, 4:8, 8:8, 16:4}                    # processes per node
            self.walltime = {1:10, 4:60, 8:168, 16:168}         # in hours
        
        self.perProcMem = {1:2, 4:2, 8:2, 16:4}             # in GB
    
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
        
    def addCommand(self, command, np):
        
        if self.currentNp == -1:
            self.currentNp = np
        elif self.currentNp != np:
            info("New CPU count ("+str(self.currentNp)+" vs. "+str(np)+"), flushing commands...")
            self.issueBatchJob()
            self.currentNp = np
        
        assert len(self.commands) < self.compenv.ppn[self.currentNp]
        self.commands.append(command)
        
        if len(self.commands) == self.compenv.ppn[self.currentNp]:
            self.issueBatchJob()
            assert len(self.commands) == 0 
        

    def _getHeader(self):
    
        lines = []
    
        lines.append("#!/bin/bash")
        lines.append("#PBS -N m5sim")
        lines.append("#PBS -lwalltime="+self.compenv.getWalltime(self.currentNp)+":00:00")
        lines.append("#PBS -m a")
        #lines.append("#PBS -q default")
        lines.append("#PBS -j oe")
    
        lines.append("#PBS -lnodes=1:ppn="+self.compenv.getPPN(self.currentNp)+",pvmem="+self.compenv.getPerProcMem(self.currentNp)+"gb,pmem="+self.compenv.getPerProcMem(self.currentNp)+"gb")
        lines.append("#PBS -A "+str(PROJECT_NUM))
    
        header = ""
        for l in lines:
            header += l+"\n"
    
        return header+"\n"

    def issueBatchJob(self):
    
        if self.commands == []:
            return
    
        output = open(pbsconfig.experimentpath+'/'+PBS_DIR_NAME+'/runfile'+str(self.fileID)+'.pbs','w')
        output.write(self._getHeader())
        
        print >> output, "cd /local/work"
        print >> output, "mkdir jahre"
        print >> output, "cd jahre"
        
        for command in self.commands:
    
            print >> output, "mkdir "+command.id
            print >> output, "cd "+command.id
            print >> output, 'echo '+command.cmd+'\n\n'
            print >> output, command.cmd + '\n\n'
            
            print >> output, "cd .."
        
            self.issuedCommands += 1
        
        print >> output, "wait"
        print >> output, ""
    
        for command in self.commands:
            print >> output, 'cp '+command.id+'/*.txt '+command.id+'/*.bb '+pbsconfig.experimentpath+'/'+command.id
            print >> output, 'rm -Rf '+command.id+'\n'
    
        self.commands = []
    
        # Finish file
        output.close()
        
        info("Attempting to submit file "+PBS_DIR_NAME+'/runfile'+str(self.fileID)+'.pbs')
        
        if not self.opts.dryrun:
            results = popen2.popen3('qsub '+pbsconfig.experimentpath+'/'+PBS_DIR_NAME+'/runfile'+str(self.fileID)+'.pbs')
            print results[0].read()
            print results[2].read()
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
    opts, args = parser.parse_args()
    
    if len(args) != 0:
        fatal("runconfig.py takes no parameters")
    
    compenv = ComputerParams()
    
    return opts, compenv

    
def main():
    
    opts, computerEnv = parseParams()

    try:    
        os.mkdir(pbsconfig.experimentpath+"/"+PBS_DIR_NAME)
    except:
        fatal("Directory "+PBS_DIR_NAME+" exists, cannot continue")
    
    batchCommands = BatchCommands(computerEnv, opts)
    for commandline, param in pbsconfig.commandlines:
        command = M5Command(commandline,  pbsconfig.get_unique_id(param))
        batchCommands.addCommand(command, pbsconfig.get_np(param))        
    batchCommands.issueBatchJob()

    print "Submitted "+str(batchCommands.issuedCommands)+" experiments in "+str(batchCommands.fileID)+" files"
    

if __name__ == '__main__':
    main()