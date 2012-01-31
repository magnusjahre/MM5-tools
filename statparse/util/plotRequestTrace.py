#!/usr/bin/env python
import sys
import os

from optparse import OptionParser
from statparse.tracefile.tracefileData import TracefileData
from statparse.plotResults import plotBrokenBarchart

class Request:
    
    def __init__(self, row):
        self.curTick = row[0]
        self.address = row[1]
        self.issuedAt = row[2]
        self.completedAt = row[3]
        
        if row[4] == 1:
            self.sharedCacheMiss = True
        else:
            self.sharedCacheMiss = False
            
        if row[5] > 0:
            self.requestCausedStall = True    
        else:
            self.requestCausedStall = False
            
        self.requestCausedStallAt = row[5]
        self.requestStallResumedAt = row[6]
                       

def parseArgs():
    parser = OptionParser(usage="analyzeTrace.py [options] filename1")

    parser.add_option("-q", "--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("-f", "--plot-from", action="store", type="int", dest="plotFrom", default=0, help="plot from this clock cycle")
    parser.add_option("-t", "--plot-to", action="store", type="int", dest="plotTo", default=0, help="plot to this clock cycle")
    
    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Command line error"
        print "Usage: "+parser.usage
        sys.exit(-1)
    
    return opts,args

def getFreePosition(outstandingReqs, newReq):
    if outstandingReqs == [None]:
        return 0
    
    for i in range(len(outstandingReqs)):
        if outstandingReqs[i].completedAt < newReq.issuedAt:
            return i
            
    return len(outstandingReqs)

def getCoordinates(data):
    outdata = []
    for req in data:
        outdata.append( (req.issuedAt, req.completedAt - req.issuedAt) )
    
    return outdata        

def plot(stalls, data, colors):
    
    import matplotlib.pyplot as plt
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    ax.broken_barh(stalls, (0.5, 0.8), facecolors='black')
    yval = 1.5
    for i in range(len(data)):        
        ax.broken_barh(data[i], (yval, 0.8), facecolors=colors[i])
        yval += 1
    
    ax.grid(True)
    
    plt.show()

def main():

    opts,args = parseArgs()
    
    if not opts.quiet:
        print
        print "Running trace file analysis..."
    
    filename = args[0]
    if not os.path.exists(filename):
        print "Error: File "+str(filename)+" not found"
        return -1
        
    tracecontent = TracefileData(filename)
    tracecontent.readTracefile()

    requests = []
    upperbound = opts.plotTo
    if upperbound == 0:
        upperbound = tracecontent.getNumRows()+1
    
    for i in range(tracecontent.getNumRows()):
        row = tracecontent.getRow(i)
        if row[0] >= opts.plotFrom and row[0] <= upperbound:
            requests.append(Request(row))
    
    parareqs = [[]]
    outstandingReqs = [None]
    for req in requests:
        pos = getFreePosition(outstandingReqs, req)
        if pos >= len(parareqs):
            parareqs.append([])
            outstandingReqs.append(None)
        parareqs[pos].append(req)
        outstandingReqs[pos] = req
    
    stalls = []
    plotdata = []
    colors = []
    for d in parareqs:
        plotdata.append(getCoordinates(d))
        clist = []
        for r in d:
            if r.requestCausedStall:
                stalls.append( (r.requestCausedStallAt, r.requestStallResumedAt - r.requestCausedStallAt) )
                if r.sharedCacheMiss:
                    clist.append('red')
                else:
                    clist.append('navy')
            else:
                if r.sharedCacheMiss:
                    clist.append('tomato')
                else:
                    clist.append('mediumslateblue')
                    
        colors.append(clist)
    
    plot(stalls, plotdata, colors)
        
if __name__ == '__main__':
    main()