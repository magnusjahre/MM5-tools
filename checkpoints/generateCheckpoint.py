#!/usr/bin/python

from optparse import OptionParser
import Checkpoint

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
    print "createCheckpointsFromExperiment is not implemented, quitting"

def main():
    
    opts,args = parseAargs()
    
    print
    print "Automatic checkpoint generation for multiprogrammed workloads"
    print
    
    if opts.fromExp:
        createCheckpointsFromExperiment()
        sys.exit(0)
        
    print "Parameters"
    print "NP:                           "+str(opts.np)
    print "Workload:                     "+str(opts.workload)
    print "Checkpoint instruction count: "+str(opts.fwinsts)
    print "Simulated memory system:      "+str(opts.memsys)
    print
    
    chkptPath = Checkpoint.generateCheckpoint(opts.workload, opts.np, opts.fwinsts, opts.memsys)
    
    print
    print "Generated checkpoint at "+chkptPath
    print

if __name__ == '__main__':
    main()