
import re
import popen2
import sys

class M5Command:
    
    binary = "/home/jahre/workspace/m5sim-fairmha/m5/build/ALPHA_SE/m5.opt"
    configfile = "/home/jahre/workspace/m5sim-fairmha/m5/configs/CMP/run.py"
    
    successString = 'Simulation complete'
    lostString = 'Sampler exit lost'
    
    arguments = {}
    
    def __init__(self, bm, np, memsys, channels):
        self.addArgument("NP", np)
        self.addArgument("MEMORY-SYSTEM", memsys)
        self.addArgument("MEMORY-BUS-CHANNELS", channels)
        self.addArgument("BENCHMARK", bm)
        
        self.addArgument("STATSFILE", "m5stats.txt")
        
        self.correct_pattern = re.compile(self.successString)
        self.lost_req_pattern = re.compile(self.lostString)
        
        self.bmName = bm
        
    def addArgument(self, name, value):
        self.arguments[name] = value
    
    def getCommandline(self):
        commandstr = self.binary
        for arg in self.arguments:
            commandstr += " -E"+arg+"="+str(self.arguments[arg])
        commandstr += " "+self.configfile
        
        return commandstr
            
    def run(self, testnum):
        
        cmd = self.getCommandline()
        
        res = popen2.popen4(cmd)
        out = res[0].read()
        
        correct = self.correct_pattern.search(out)
        lostReq = self.lost_req_pattern.search(out)
        
        if correct and (not lostReq):
            print (str(testnum)+": "+str(self.bmName)).ljust(40)+"Test passed!".rjust(20)
        else:
            print (str(testnum)+": "+str(self.bmName)).ljust(40)+"Test failed!".rjust(20)
            
            file = open("test"+str(testnum)+".output", "w");
            file.write("Command line\n\n")
            file.write(cmd+"\n\n")
            file.write("Program output\n\n")
            file.write(out)
            file.close()
            
        sys.stdout.flush()
        