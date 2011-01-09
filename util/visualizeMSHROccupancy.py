#!/usr/bin/python

import sys
import os

from optparse import OptionParser
from statparse.util import fatal
from statparse.plotResults import plotBrokenBarchart

class MSHROccupancy:
    
    def __init__(self, filename, numMshrs):
        self.data = [[] for i in range(numMshrs)]
        
        self.requests = 0
        
        if filename != "":
            file = open(filename)
            file.readline()
            
            for line in file:
                d = line.split(";")
                if(len(d) != 4):
                    fatal("Unknown file format")
                id = int(d[1])
                allocAt = int(d[2])
                duration = int(d[3])
                if id >= numMshrs:
                    fatal("Got MSHR with id "+str(id)+" but only "+str(numMshrs)+" indicated by --mshrs parameter")
                self.data[id].append( (allocAt, duration) )
                
                self.oldestCycle = int(d[0])
                self.requests += 1
    
    def addEntry(self, mshrID, allocAt, duration):
        self.requests += 1
        self.data[mshrID].append( (allocAt, duration) )
    
    def getOldestEntry(self):
        oldest = 100000000000
        oldestIndex = -1
        for i in range(len(self.data)):
            if self.data[i] != []:
                if self.data[i][0][0] < oldest:
                    oldest = self.data[i][0][0]
                    oldestIndex = i
                    
        assert oldestIndex != -1
        return self.data[oldestIndex].pop(0) 
    
    def isEmpty(self):
        for list in self.data:
            if list != []:
                return False
        return True
    
    def plot(self, title, filename):
        plotBrokenBarchart(self.data,
                           xlabel="Clock Cycles",
                           ylabel="MSHR ID",
                           title=title,
                           filename=filename)

def parseArgs():
    parser = OptionParser(usage="visualizeMSHROccupancy.py [options] filename")
    parser.add_option("--mshrs", action="store", dest="mshrs", default=16, type="int", help="The number of MSHRs used to generate the reduce file")
    parser.add_option("--title", action="store", dest="title", default="", type="string", help="The title to put in the graph")
    parser.add_option("--outfile", action="store", dest="outfile", default="", type="string", help="Write the plot to the file instead of showing it")

    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Command line error..."
        print "Usage : "+parser.usage
        sys.exit(-1)
    
    if not os.path.exists(args[0]):
        fatal("File "+args[0]+" does not exist")
    
    return opts, args

def main():
    opts, args = parseArgs()
    
    occupancy = MSHROccupancy(args[0], opts.mshrs)
    occupancy.plot(opts.title, opts.outfile)

if __name__ == '__main__':
    main()