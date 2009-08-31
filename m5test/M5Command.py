import popen2
import sys
import re
import m5test

__metaclass__ = type

class M5Command():
    
    binary = "/home/jahre/workspace/m5sim-fairmha/m5/build/ALPHA_SE/m5.opt"
    configfile = "/home/jahre/workspace/m5sim-fairmha/m5/configs/CMP/run.py"
    
    successString = 'Simulation complete'
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
        
        self.correct_pattern = re.compile(self.successString)
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
            
    def run(self, testnum, completedInstPat):
        
        cmd = self.getCommandline()
        
        res = popen2.popen4(cmd)
        out = res[0].read()
        
        correct = self.correct_pattern.search(out)
        lostReq = self.lost_req_pattern.search(out)
        
        if correct and (not lostReq):
            error = False
        else:
            error = True

        comInsts = m5test.findStatsPattern(completedInstPat, self.statsfilename)
        for simObj in comInsts:
            if int(comInsts[simObj]) < self.expCommittedInsts:
                error = True
        
        
        if not error:
            print (str(testnum)+": "+str(self.bmName)).ljust(40)+"Test passed!".rjust(20)
        else:
            print (str(testnum)+": "+str(self.bmName)).ljust(40)+"Test failed!".rjust(20)
            
            file = open("test"+str(testnum)+".output", "w");
            file.write("Committed instructions\n\n")
            file.write(str(comInsts)+"\n\n")
            file.write("Command line\n\n")
            file.write(cmd+"\n\n")
            file.write("Program output\n\n")
            file.write(out)
            file.close()
            
        sys.stdout.flush()

        return not error
