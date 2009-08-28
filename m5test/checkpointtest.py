#!/usr/bin/python

import sys
import fairmha.experimentconfig as expconfig
import m5test

def addArguments(testconfig):
    testconfig.addArgument("MEMORY-ADDRESS-OFFSET", 0)
    testconfig.addArgument("MEMORY-ADDRESS-PARTS", 4)
    testconfig.addArgument("MEMORY-BUS-SCHEDULER", "RDFCFS")    
    return testconfig

def main():
    
    print "Running M5 Checkpoint test"

    np = 1
    fwinsts = 50*10**6
    siminsts = 3*10**6
    channels = 1
    
    memsys = ["RingBased", "CrossbarBased"]
    tmpconfig = expconfig.ExperimentConfiguration("", "", "")
    bms = tmpconfig.specBenchmarks
    
    testnum = 0
    
    print
    print "Generating checkpoints..."
    for m in memsys:
        for bm in bms:
            testconfig = m5test.M5Command(bm, np, m, channels)
            testconfig = addArguments(testconfig)
            
            testconfig.addArgument("GENERATE-CHECKPOINT", "")
            testconfig.addArgument("SIMINSTS", fwinsts)
            
            testconfig.run(testnum)
            testnum += 1

    print
    print "Running from checkpoints..."
    for m in memsys:
        for bm in bms:
            testconfig = m5test.M5Command(bm, np, m, channels)
            testconfig = addArguments(testconfig)
            
            testconfig.addArgument("USE-CHECKPOINT", ".")
            testconfig.addArgument("SIMINSTS", siminsts)
            
            testconfig.run(testnum)
            testnum += 1
    

if __name__ == '__main__':
    main()