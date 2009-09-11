#!/usr/bin/python
import sys
from optparse import OptionParser
import Checkpoint

import simpoints3
import deterministic_fw_wls as workloads

def parseAargs():
    parser = OptionParser(usage="generateCheckpoint.py ")
    
    parser.add_option("--from-experiment", action="store_true", dest="fromExp", default="", help="Use workload table and pbsconfig.py to generate checkpoints")
    
    parser.add_option("--np", action="store", dest="np", type="int", default=4, help="The number of CPUs to use in checkpoint")
    parser.add_option("--workload", action="store", dest="workload", default="fair01", help="Workload")
    parser.add_option("--fwinsts", action="store", dest="fwinsts", type="int", default=50000000, help="The number of instructions to use when generating the checkpoint")
    parser.add_option("--memsys", action="store", dest="memsys", default="RingBased", help="The memory system to use for simulations")
    
    opts, args = parser.parse_args()
    
    return opts, args

def createCheckpointsFromExperiment():
    
    nps = [4, 8, 16]
    memsys = ["CrossbarBased", "RingBased"]
    fw = -1
    
    for np in nps:
        for wl in workloads.getWorkloads(np):
            for mem in memsys:
                for simpoint in range(simpoints3.maxk):
                    
                    if Checkpoint.prerequisiteFilesExist(wl, np, mem, simpoint):
                        printParameters(np, wl, mem, simpoint, fw)
                        path = Checkpoint.generateCheckpoint(wl, np, fw, mem, simpoint)
                        print "Generated checkpoint at "+path
                    else:
                        print "Files needed for np "+str(np)+", workload "+wl+", memsys "+mem+" and simpoint "+str(simpoint)+" not found"
                        print "Skipping..."
    return 0

def printParameters(np, wl, memsys, simpoint, fw):
    print "Generating checkpoint with parameters:"
    print "NP:                           "+str(np)
    print "Workload:                     "+str(wl)
    print "Simulated memory system:      "+str(memsys)
    if fw != -1:
        print "Checkpoint instruction count: "+str(fw)
    if simpoint != -1:
        print "Simpoint number:              "+str(simpoint)
    print

def main():
    
    opts,args = parseAargs()
    
    print
    print "Automatic checkpoint generation for multiprogrammed workloads"
    print
    
    if opts.fromExp:
        sys.exit(createCheckpointsFromExperiment())
    
    simpoint = -1
    printParameters(opts.np, opts.workload, opts.memsys, simpoint, opts.fwinsts)
    
    chkptPath = Checkpoint.generateCheckpoint(opts.workload, opts.np, opts.fwinsts, opts.memsys, simpoint)
    
    print
    print "Generated checkpoint at "+chkptPath
    print

if __name__ == '__main__':
    main()