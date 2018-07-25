#!/usr/bin/env python   

import sys
import subprocess
import os
import platform
import re
import math
import random
from workloadfiles.workloads import Workloads
from optparse import OptionParser
 
PBS_DIR_NAME = "pbsfiles"

class ComputerParams:
    
    # Use queue = None to not set queue name in PBS file
    #
    # Memory requirements is in MB and walltime in hours
    def __init__(self, opts):
        
        compname = platform.node()
        
        self.queue = opts.queue
        self.projectNum = None
        self.perProcMem = {1:1900, 2:1900, 4:1900, 8:4000, 16:5592}
        
        if re.search("stallo", compname):
            info("Stallo run detected...")
            self.__processStallo()
            
        else:
            info("No HPC cluster detected, using Stallo values")
            self.__processStallo()
            
        if opts.walltime != 0:
            info("Setting all walltime limits to provided value "+str(opts.walltime))
            for key in self.walltime:
                self.walltime[key] = opts.walltime
            
        if opts.ppn != 0:
            memInMeg = int(math.floor(((32*(2**10))/opts.ppn)/100.0))*100
            info("Setting all ppn limits to provided value "+str(opts.ppn)+" and memory per process to "+str(memInMeg))
            for key in self.ppn:
                self.ppn[key] = opts.ppn
            for key in self.perProcMem:
                self.perProcMem[key] = memInMeg
    
    def __processStallo(self):
        # Single core is high due to CPL graph generation, can be lowered when this is disabled
        self.ppn = {1:16, 2:16, 4:16, 8:8, 16:6}
        self.walltime = {1:47, 2:100, 4:100, 8:150, 16:350}
        self.projectNum = "nn4650k"        
        
    def getQueue(self, np):
        if self.queue == None or np == 1:
            if self.walltime[np] < 48:
                return "normal"
            else:
                return "singlenode"
        return self.queue
    
    def getHeader(self, np):
    
        lines = []
    
        lines.append("#!/bin/bash")
        
        lines.append("#SBATCH --job-name=m5sim")
        
        days = self.walltime[np] / 24
        hrs = self.walltime[np] % 24
        lines.append("#SBATCH --time="+str(days)+"-"+str(hrs)+":00:00")
        
        lines.append("#SBATCH --partition="+self.getQueue(np))

        lines.append("#SBATCH --nodes=1")
        lines.append("#SBATCH --ntasks-per-node="+self.getPPN(np))
        lines.append("#SBATCH --mem-per-cpu="+self.getPerProcMem(np)+"MB")
        
        if self.projectNum != None:
            lines.append("#SBATCH -A "+self.projectNum)

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
    
    def __init__(self, cmd, ident, privateMode, np, wls, varparams):
        self.cmd = cmd
        self.id = ident
        self.privateMode = privateMode
        self.np = np
        self.workloads = wls
        
        self.jobID = ""
        self.dependsOn = []
        
        wlres = re.search("t-[hmlas]-[0-9]+", self.id)
        if wlres:
            self.workloadID = wlres.group(0)
        else:
            wlres = re.search("w-[a-zA-Z0-9-]+-b", self.id)
            self.workloadID = wlres.group(0)
            self.workloadID = self.workloadID.replace("w-", "")
            self.workloadID = self.workloadID.replace("-b", "")
        
        self.expParams = varparams
        
        self.bms = []
        if np > 1:
            self.bms = self.workloads.getBms(self.workloadID, self.np)
        
    def getWorkloadID(self):
        return self.workloadID
    
    def getExpParams(self):
        splitted = self.id.split("-")
        expParamList = splitted[7:]
        tmp = "-".join(expParamList)
        return tmp
    
    def getPMSamplePointFile(self, cpuID):
        return "pm-sample-points-"+self.workloadID+"-"+str(cpuID)+"-"+self.bms[cpuID]+".txt"
    
    def updateDependencies(self, sharedModeCommand):
        assert self.np == 1
        if self.workloadID == sharedModeCommand.workloadID:
            paramsEqual = True
            for k in self.expParams:
                if self.expParams[k] != sharedModeCommand.expParams[k]:
                    paramsEqual = False
            
            if paramsEqual and sharedModeCommand.jobID not in self.dependsOn:
                self.dependsOn.append(sharedModeCommand.jobID)
    
class BatchCommands:
    
    def __init__(self, compenv, opts, pbsconfig):
        
        self.compenv = compenv
        self.opts = opts
        self.pbsconfig = pbsconfig
        
        self.workloads = Workloads()
        self.sharedCommands = []
        self.privateCommands = []
        
        self.batchCommandList = []
        self.fileID = 0
        self.issuedCommands = 0
        
    def initializeCommands(self, sharedModeCommands, privateModeCommands):
        nps = []
        for cmd, param in sharedModeCommands:
            np = self.pbsconfig.get_np(param)
            self.sharedCommands.append(M5Command(cmd, self.pbsconfig.get_unique_id(param), True, np, self.workloads, self.pbsconfig.get_variable_params(param)))
            if np not in nps:
                nps.append(np)
                                    
        if len(nps) != 1:
            fatal("Experiments can only contain one shared mode core count")
        
        for cmd, param in privateModeCommands:
            self.privateCommands.append(M5Command(cmd, self.pbsconfig.get_unique_id(param), False, 1, self.workloads, self.pbsconfig.get_variable_params(param)))

    def submitJobs(self):
        
        info("PROCESSING SHARED MODE COMMANDS")
        for cmd in self.sharedCommands:
            self.addCommand(cmd)           
        self.issueBatchJob()
        
        info("PROCESSING PRIVATE MODE COMMANDS")
        for pmcmd in self.privateCommands:
            for smcmd in self.sharedCommands:
                pmcmd.updateDependencies(smcmd)
        
        for cmd in self.privateCommands:
            self.addCommand(cmd)
        self.issueBatchJob()
    
    def addCommand(self, command):
        
        assert len(self.batchCommandList) < self.compenv.ppn[command.np]
        self.batchCommandList.append(command)
        
        if len(self.batchCommandList) == self.compenv.ppn[command.np]:
            self.issueBatchJob()
            assert len(self.batchCommandList) == 0 
        
    def issueBatchJob(self):
    
        if self.batchCommandList == []:
            return
    
        usedir = PBS_DIR_NAME
    
        runfilepath = usedir+'/runfile'+str(self.fileID)+'.sh'
    
        expnp = self.batchCommandList[0].np
    
        output = open(runfilepath,'w')
        output.write(self.compenv.getHeader(expnp))
        
        for command in self.batchCommandList:
            print >> output, "rm -Rf "+command.id # take care of restarts
            print >> output, "mkdir "+command.id
            print >> output, "cd "+command.id
            print >> output, "echo > .rundir"
            print >> output, command.cmd + '\n\n'
            print >> output, "cd .."
        
            self.issuedCommands += 1
        
        print >> output, "wait"
        print >> output, ""
    
        if expnp > 1:
            for command in self.batchCommandList:
                print >> output, "cd "+command.id
                for i in range(expnp):
                    print >> output, "genPMSamplePointFiles.py --np "+str(expnp)+" --outfile "+command.getPMSamplePointFile(i)+" globalPolicyCommittedInsts"+str(i)+".txt"
                print >> output, "cd .."
    
        output.close()
        
        jobDependencies = []
        if expnp == 1:
            for cmd in self.batchCommandList:
                for dep in cmd.dependsOn:
                    if dep not in jobDependencies:
                        jobDependencies.append(dep)
            info("Job depends on job(s) "+",".join(jobDependencies))           
        
        jobID = str(random.randint(1,10**6))
        if not self.opts.dryrun:
            sbatchargs = ['sbatch']
            if jobDependencies != []:
                sbatchargs.append("-d")
                depstr = "afterany"
                for depJobID in jobDependencies:
                    depstr += ":"+depJobID
                sbatchargs.append(depstr)
            
            sbatchargs.append(runfilepath)
            
            info("Executing command '"+" ".join(sbatchargs)+"'")
            output = subprocess.check_output(sbatchargs)
            info("Output from sbatch is '"+output.strip()+"'")
            
            jobIDRes = re.search("[0-9]+", output)
            jobID = jobIDRes.group(0)
            info("Detected job ID "+jobID)
        else:
            info("Dry-run, skipping file "+runfilepath)
            
        try:
            int(jobID)
        except:
            fatal("Job ID parse error for "+str(jobID))
            
        for j in self.batchCommandList:
            j.jobID = jobID
        
        self.batchCommandList = []
        self.fileID += 1

def fatal(message):
    print "FATAL: "+message
    sys.exit()

def info(message):
    print "INFO: "+message

def parseParams():
    parser = OptionParser(usage="runconfig.py [options]")

    parser.add_option("--dry-run", action="store_true", dest="dryrun", default=False, help="Do not submit jobs to the cluster")
    parser.add_option("--queue", action="store", dest="queue", default=None, help="PBS queue to submit jobs to")
    parser.add_option("--walltime", action="store", type="int", dest="walltime", default=0, help="PBS walltime limit in hours")
    parser.add_option("--ppn", action="store", type="int", dest="ppn", default=0, help="Processes per node to use")
    
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
        os.mkdir(PBS_DIR_NAME)
    except:
        fatal("Could not create directory for "+PBS_DIR_NAME+" because it already exists")
    
    batchCommands = BatchCommands(computerEnv, opts, pbsconfig)
    batchCommands.initializeCommands(pbsconfig.commandlines, pbsconfig.privModeCommandlines)
    batchCommands.submitJobs()

    print "Submitted "+str(batchCommands.issuedCommands)+" experiments in "+str(batchCommands.fileID)+" files"
    

if __name__ == '__main__':
    main()
