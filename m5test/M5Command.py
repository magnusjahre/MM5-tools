import subprocess
import sys
import re
import m5test

__metaclass__ = type

class M5Command():
    
    binary = "/home/jahre/workspace/m5sim-fairmha/m5/build/ALPHA_SE/m5.opt"
    configfile = "/home/jahre/workspace/m5sim-fairmha/m5/configs/CMP/run.py"
    
    successStringSim = 'all CPUs have reached their instruction limit'
    successStringCheckpoint = 'Reached checkpoint instruction'
    lostString = 'Sampler exit lost'
    
    def __init__(self):
        self.arguments = {}

    def setUpTest(self, bm, np, memsys, channels):
        self.setArgument("NP", np)
        self.setArgument("MEMORY-SYSTEM", memsys)
        self.setArgument("MEMORY-BUS-CHANNELS", channels)
        self.setArgument("BENCHMARK", bm)

        self.statsfilename = "m5stats.txt"
        self.setArgument("STATSFILE", self.statsfilename)
        
        self.correct_pattern_sim = re.compile(self.successStringSim)
        self.correct_pattern_checkpoint = re.compile(self.successStringCheckpoint)
        self.lost_req_pattern = re.compile(self.lostString)
        
        self.bmName = bm

    def clearArguments(self):
        self.arguments = {}

    def setExpectedComInsts(self, insts):
        self.expCommittedInsts = insts
        
    def setArgument(self, name, value):
        self.arguments[name] = value
        
    def getCommandline(self):
        commandstr = self.binary
        for arg in self.arguments:
            commandstr += " -E"+arg+"="+str(self.arguments[arg])
        commandstr += " "+self.configfile
        
        return commandstr
            
    def run(self, testnum, completedInstPat, doInstCheck = True):
        
        cmd = self.getCommandline()
        
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        out = stdout+"\n"+stderr
        
        simCorrect = self.correct_pattern_sim.search(out)
        checkpointCorrect = self.correct_pattern_checkpoint.search(out)
        lostReq = self.lost_req_pattern.search(out)
        
        if (simCorrect or checkpointCorrect) and (not lostReq):
            error = False
        else:
            error = True

        if doInstCheck:
            comInsts = m5test.findStatsPattern(completedInstPat, self.statsfilename)
            for simObj in comInsts:
                if int(comInsts[simObj]) < self.expCommittedInsts:
                    error = True
        
        
        if not error:
            print (str(testnum)+": "+str(self.bmName)).ljust(40)+"Test passed!".rjust(20)
        else:
            print (str(testnum)+": "+str(self.bmName)).ljust(40)+"Test failed!".rjust(20)
            
            file = open("test"+str(testnum)+".output", "w")
            if doInstCheck:
                file.write("Committed instructions\n\n")
                file.write(str(comInsts)+"\n\n")
            file.write("Command line\n\n")
            file.write(cmd+"\n\n")
            file.write("Program output\n\n")
            file.write(out)
            file.close()
            
        sys.stdout.flush()

        return not error