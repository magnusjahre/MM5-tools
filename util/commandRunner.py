#!/usr/bin/python

import threading
import sys
from subprocess import Popen, PIPE
import time
import os
import re
from optparse import OptionParser
from util import fatal

class ThreadedCommand(threading.Thread):
    
    def __init__(self, localID, command, cmdRunner):
        threading.Thread.__init__(self)
        self.localID = localID
        self.cmdRunner = cmdRunner
        
        try:
            self.directory = command["directory"]
            self.existsname = command["existsname"]
            self.command = command["command"]
        except:
            fatal("ThreadedCommand: Command element parse error")
        
    def run(self):
        self.cmdRunner.protectedPrint("Thread "+str(self.localID)+": Running command "+(" ".join(self.command))+" in directory "+self.directory)
        if self.cmdRunner.dryRun:
            self.cmdRunner.protectedPrint("Thread "+str(self.localID)+": dry run option set, skipping")
        else:
            if os.path.exists(os.path.join(self.directory,self.existsname)):
                self.cmdRunner.protectedPrint("Thread "+str(self.localID)+": File "+self.existsname+" exists, skipping")
            else:
                p = Popen(self.command, cwd=self.directory, stdout=PIPE, stderr=PIPE)
                stdout, stderr = p.communicate()
                
                if self.cmdRunner.checkOutput:
                    self.checkOutput(stderr)
                else:
                    self.cmdRunner.protectedPrint("Thread "+str(self.localID)+" stdout: "+stdout)
                    self.cmdRunner.protectedPrint("Thread "+str(self.localID)+" stderr: "+stderr)
        
        self.cmdRunner.protectedPrint("Thread "+str(self.localID)+" terminating")
        self.cmdRunner.updateThreadCnt(False)

    def checkOutput(self, stderr):
        
        result = re.search("Terminating simulation -- all CPUs have reached their instruction limit", stderr)
        resstr = "Test failed"
        if result:
            resstr = "Test passed"
        self.cmdRunner.protectedPrint("Thread "+str(self.localID)+" result: "+resstr)
        
        os.chdir(self.directory)
        f = open("testresult.txt", "w")
        f.write(resstr)
        f.flush()
        f.close()
        os.chdir("..")

class CommandRunner():
    
    def __init__(self, numThreads, waitTime, dryRun, checkOutput):
        self.printLock = threading.Lock()
        self.threadCntLock = threading.Lock()
        self.numThreads = numThreads
        self.numWorkers = 0
        self.waitTime = waitTime
        self.dryRun = dryRun
        self.checkOutput = checkOutput

    def protectedPrint(self, text):
        self.printLock.acquire()
        print text
        sys.stdout.flush()
        self.printLock.release()

    def updateThreadCnt(self, inc):
        self.threadCntLock.acquire()
        if inc:
            self.numWorkers += 1
        else:
            self.numWorkers -= 1
        self.threadCntLock.release()

    def runCommands(self, commands):
        
        threadCounter = 0
        while commands != []:
            if self.numWorkers >= self.numThreads:
                self.protectedPrint("Number of working threads is "+str(self.numWorkers)+", sleeping")
                time.sleep(self.waitTime)
            else:
                cmd = commands.pop(0)
                thread = ThreadedCommand(threadCounter, cmd, self)            
                thread.start()
                self.updateThreadCnt(True)
                threadCounter += 1
                
        while self.numWorkers > 0:
            self.protectedPrint("Waiting for workers to finish, number of active worker threads is "+str(self.numWorkers)+", sleeping")
            time.sleep(self.waitTime)

        self.protectedPrint("Done!")

def parseArgs():
    
    parser = OptionParser(usage="commandRunner.py [options] command-file")
    parser.add_option("--threads", '-t', action="store", dest="threads", default=4, type="int", help="Number of worker threads")
    parser.add_option("--sleep", '-s', action="store", dest="sleep", default=5, type="int", help="Number of seconds main thread sleeps for when the maximum number of threads are running")
    parser.add_option("--dry-run", action="store_true", dest="dryRun", default=False, help="Don't run the commands")
    parser.add_option("--check-output", action="store_true", dest="checkOutput", default=False, help="Check for successful simulator completion")
    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Usage:"
        print parser.usage
        sys.exit()
    
    try:
        if not os.path.exists(args[0]):
            fatal("Cannot find file "+args[0]+" in current directory")

        if not args[0].endswith(".py"):
            fatal("File "+args[0]+" does not end with .py")

        pymodule = args[0].replace(".py", "")
        
    except:
        print "Cannot process file "+str(args[0])
        sys.exit()
    
    try:
        commandmodule = __import__(pymodule)
        commands = commandmodule.commands
    except:
        print "Cannot parse module "+str(args[0])+". Does it containt a list named 'commands'?"
        sys.exit()
    
    return commands, opts

def main():
    commands, opts = parseArgs()
    
    print "CommandRunner started with "+str(len(commands))+" potential commands"
    
    cmdRunner = CommandRunner(opts.threads, opts.sleep, opts.dryRun, opts.checkOutput)
    cmdRunner.runCommands(commands)
    
if __name__ == '__main__':
    main()
