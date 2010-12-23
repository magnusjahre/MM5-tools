#!/usr/bin/python

from optparse import OptionParser
from workloadfiles.workloads import parseTypeString
from workloadfiles.workloads import Workloads
from workloadfiles.workloads import UnknownWorkloadException
import optcomplete
import sys

def parseArgs():
    parser = OptionParser(usage="getWorkload.py [options] np [workload-name]")

    parser.add_option("--type", action="store", dest="type", default="all", help="Only print workloads of the specified type")
    
    optcomplete.autocomplete(parser)
    opts, args = parser.parse_args()
    
    if len(args) > 2 or len(args) < 1:
        print "Command line error."
        print "Usage: "+parser.usage
        sys.exit(-1)
    
    return opts, args

def main():
    opts, args = parseArgs()
    
    np = int(args[0])
    workloads = Workloads()
    
    if len(args) == 2:
        try:
            workloads.printBms(args[1], np)
        except UnknownWorkloadException as e:
            print e.message
            sys.exit(-1)
    else:
        try:
            type = parseTypeString(opts.type)
        except Exception as e:
            print e.args[0]
            sys.exit(-1)
            
        workloads.printWorkloads(np, type)

if __name__ == '__main__':
    main()