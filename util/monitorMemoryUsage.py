#!/usr/bin/env python

import sys
import subprocess
from datetime import datetime
from optparse import OptionParser
from time import sleep

def parseArgs():
    parser = OptionParser(usage="monitorMemoryUsage.py [options] pid")

    parser.add_option("--sleep-for", action="store", dest="sleepFor", default=10, help="Sleep for this amount of seconds between samples (Default: 10)")
    parser.add_option("--col-width", action="store", dest="colWidth", default=15, help="Column width in output file (Default: 15)")
    parser.add_option("--outfile", action="store", dest="outfile", default="memory-trace.txt", help="Name of output file (Default: memory-trace.txt)")
    
    opts, args = parser.parse_args()

    if len(args) != 1:
        print
        print "Commandline error:"
        print parser.usage
        print 
        sys.exit(0)
        
    return args[0], opts

def getProcessData(pid):
    try:
        data = subprocess.check_output(["ps", "-o", "pid,vsz,%cpu", pid])
    except:
        print "Unknown PID, application likely finished..."
        sys.exit()
    lines = data.split("\n")
    processData = lines[1].split()
    
    vmem = int(processData[1])
    cpuPerc = float(processData[2])
    
    return vmem/(2**10), cpuPerc

def main():
    pid, opts = parseArgs()
    
    print
    print "Tracing the memory and CPU usage of process "+str(pid)+" to file "+opts.outfile
    print
    
    of = open(opts.outfile, "w")

    header = "Date".ljust(opts.colWidth)
    header += "Time".ljust(opts.colWidth)
    header += "VMEM (MB)".rjust(opts.colWidth)
    header += "CPU (%)".rjust(opts.colWidth)
    of.write(header+"\n")
    of.flush()
    
    while True:
        now = datetime.now()
        megs,cpu = getProcessData(pid)
        
        outline = str(now.date()).ljust(opts.colWidth)
        outline += str(now.time()).ljust(opts.colWidth)
        outline += str(megs).rjust(opts.colWidth)
        outline += str(cpu).rjust(opts.colWidth)
        
        of.write(outline+"\n")
        of.flush()
        
        sleep(opts.sleepFor)
        

if __name__ == '__main__':
    main()
