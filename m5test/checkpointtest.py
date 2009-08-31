#!/usr/bin/python

import sys
import fairmha.experimentconfig as expconfig
from M5Command import M5Command

def setArguments(testconfig):
    testconfig.setArgument("MEMORY-ADDRESS-OFFSET", 0)
    testconfig.setArgument("MEMORY-ADDRESS-PARTS", 4)
    testconfig.setArgument("MEMORY-BUS-SCHEDULER", "RDFCFS")    
    return testconfig

def main():
    
    print "Running M5 Checkpoint test"

    np = 1
    fwinsts = 200*10**6
    siminsts = 10*10**6
    
    channels = 1
    
    memsys = ["RingBased", "CrossbarBased"]
    tmpconfig = expconfig.ExperimentConfiguration("", "", "")
    bms = tmpconfig.specBenchmarks

    testnum = 0
    successnum = 0
    
    print
    print "Generating checkpoints..."
    
    sys.stdout.flush()
    

    testconfig = M5Command()
    for m in memsys:
        for bm in bms:
     
            testconfig.setUpTest(bm, np, m, channels)
            testconfig = setArguments(testconfig)
            
            testconfig.setArgument("GENERATE-CHECKPOINT", "")
            testconfig.setArgument("SIMINSTS", fwinsts)
            testconfig.setExpectedComInsts(fwinsts)
            
            success = testconfig.run(testnum, "simpleCPU.*num_insts.*")
            testnum += 1
            if success:
                successnum += 1
    
    useCheckptConfig = M5Command()

    print
    print "Running from checkpoints..."
    for m in memsys:
        for bm in bms:

            useCheckptConfig.setUpTest(bm, np, m, channels)
            useCheckptConfig = setArguments(useCheckptConfig)
            
            useCheckptConfig.setArgument("USE-CHECKPOINT", ".")
            useCheckptConfig.setArgument("SIMINSTS", siminsts)
            useCheckptConfig.setExpectedComInsts(siminsts)

            success = useCheckptConfig.run(testnum, "detailedCPU.*COM:count.*")
            testnum += 1
            if success:
                successnum += 1

    print
    print "Completed "+str(successnum)+" out of "+str(testnum)+" tests successfully, "+str((float(successnum)/float(testnum))*100)+" % success"
    print


if __name__ == '__main__':
    main()
