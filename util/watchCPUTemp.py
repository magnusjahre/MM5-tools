#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import sys
import time
from optparse import OptionParser

def parseArgs():
    
    parser = OptionParser(usage="watchCPUTemp.py [options]")
    parser.add_option("--file", '-f', action="store", dest="file", default="", type="string", help="Write measurements to a file")
    parser.add_option("--sleep", '-s', action="store", dest="sleep", default=1, type="int", help="Seconds between measurements")
    opts, args = parser.parse_args()
    
    if len(args) != 0:
        print "Usage:"
        print parser.usage
        sys.exit()
    
    return opts

def parseSensors(output):
    temps = []
    for l in output.split("\n"):
        if l.startswith("temp1:"):
            temp = l.split()[1]
            temp = temp.replace("°C", "")
            temp = temp.replace("+", "")
            temps.append(temp)
    return temps
            
            
def printOutput(temps, iteration, outfile):
    
    outstring = str(iteration)
    for t in temps:
        outstring += ";"+t
    
    if outfile != None:
        outfile.write(outstring+"\n")
        outfile.flush()
    print outstring

def main():
    
    opts = parseArgs()

    if opts.file != "":
        outfile = open(opts.file, "w")
    else:
        outfile = None

    print "Watch sensors running. Press ctrl-c to exit."
    num = 1
    while True:    
        proc = subprocess.Popen(["sensors"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        out,err = proc.communicate()        
        temps = parseSensors(out)
        printOutput(temps, num, outfile)
        num += 1
        time.sleep(opts.sleep)

if __name__ == '__main__':
    main()