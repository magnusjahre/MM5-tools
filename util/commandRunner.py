#!/usr/bin/python

import threading
import sys
import subprocess
import time

class ThreadedCommand(threading.Thread):
    
    def __init__(self, localID, command, cmdRunner):
        threading.Thread.__init__(self)
        self.localID = localID
        self.command = command
        self.cmdRunner = cmdRunner
        
    def run(self):
        self.cmdRunner.protectedPrint("Thread "+str(self.localID)+": Running command "+(" ".join(self.command)))
        subprocess.call(self.command)
        self.cmdRunner.protectedPrint("Thread "+str(self.localID)+" terminating")


class CommandRunner():
    
    def __init__(self):
        self.printLock = threading.Lock()

    def protectedPrint(self, text):
        self.printLock.acquire()
        print text
        sys.stdout.flush()
        self.printLock.release()

    def runCommands(self, numThreads, commands, waitTime):
        
        threadCounter = 0
        while commands != []:
            numActive = threading.activeCount()
            if numActive > numThreads:
                self.protectedPrint("Number of active threads is "+str(numActive)+", sleeping")
                time.sleep(waitTime)
            else:
                cmd = commands.pop(0)
                thread = ThreadedCommand(threadCounter, cmd, self)
                thread.start()
                threadCounter += 1
        
    def test(self):
        cmd = ["date"]
        commands = []
        for i in range(50):
            commands.append(cmd)
        
        self.runCommands(10, commands, 1)
    
if __name__ == '__main__':
    cmdRunner = CommandRunner()
    cmdRunner.test()
