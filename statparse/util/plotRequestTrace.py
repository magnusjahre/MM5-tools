#!/usr/bin/env python
import sys
import os

from optparse import OptionParser
from statparse.tracefile.tracefileData import TracefileData
from statparse.plotResults import plotRawBarChart, plotHistogram

class Request:
    
    def __init__(self, row):
        self.curTick = row[0]
        self.id = int(row[1])
        self.address = row[2]
        self.issuedAt = row[3]
        self.completedAt = row[4]
        
        if row[5] == 1:
            self.sharedCacheMiss = True
        else:
            self.sharedCacheMiss = False
            
        if row[6] > 0:
            self.requestCausedStall = True    
        else:
            self.requestCausedStall = False
            
        self.requestCausedStallAt = row[6]
        self.requestStallResumedAt = row[7]
        
        self.dependsOn = None
        self.children = []
        
    def setDependsOn(self, req):
        self.dependsOn = req
        
    def addChild(self, req):
        self.children.append(req)
        
    def __str__(self):
        return str(self.id)+" (issued at "+str(self.issuedAt)+", completed at "+str(self.completedAt)+")"

def parseArgs():
    parser = OptionParser(usage="analyzeTrace.py [options] filename1")

    plotTypes = ["requests", "heightbar", "heighthistogram"]

    parser.add_option("-q", "--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("-f", "--plot-from", action="store", type="int", dest="plotFrom", default=0, help="plot from this request id")
    parser.add_option("-s", "--plot-size", action="store", type="int", dest="plotSize", default=0, help="plot this number of requests")
    parser.add_option("-t", "--plot-type", action="store", type="string", dest="plotType", default="", help="type of plot, one of "+str(plotTypes))
    parser.add_option("--avg-alone-lat", action="store", type="float", dest="avgAloneLat", default=0.0, help="average alone memory latency")
    
    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Command line error"
        print "Usage: "+parser.usage
        sys.exit(-1)
    
    
    if opts.plotType != "":
        if opts.plotType not in plotTypes:
            print "Plot type must be in "+str(plotTypes)
            sys.exit(-1)
    
    return opts,args

def getFreePosition(outstandingReqs, newReq):
    if outstandingReqs == [None]:
        return 0
    
    for i in range(len(outstandingReqs)):
        if outstandingReqs[i].completedAt < newReq.issuedAt:
            return i
            
    return len(outstandingReqs)

def makePlotData(parareqs):
    
    plotdata = []
    colors = []
    for d in parareqs:
        plotrow = []
        clist = []
        for req in d:
            if req.requestCausedStall:
                plotrow.append( (req.issuedAt, req.requestCausedStallAt - req.issuedAt) )
                if req.sharedCacheMiss:
                    clist.append('red')
                else:
                    clist.append('navy')
                
                assert req.requestStallResumedAt == req.completedAt+1
                plotrow.append( (req.requestCausedStallAt, req.requestStallResumedAt - req.requestCausedStallAt) )
                clist.append('black')
            else:
                plotrow.append( (req.issuedAt, req.completedAt - req.issuedAt) )
                if req.sharedCacheMiss:
                    clist.append('lightsalmon')
                else:
                    clist.append('mediumslateblue')
        
        plotdata.append(plotrow)      
        colors.append(clist)

    return plotdata, colors

def plot(data, colors):
    
    import matplotlib.pyplot as plt
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    yval = 0.5
    for i in range(len(data)):
        ax.broken_barh(data[i], (yval, 0.8), facecolors=colors[i])
        yval += 1
    
    ax.grid(True)
    
    ax.set_xlabel("Clock Cycles")
    
    plt.show()

def createHeightData(parareqs, requests):
    
    height = []
    for i in range(int(requests[0].issuedAt), int(requests[-1].completedAt)):
        tmppara = 0.0
        for r in requests:
            if i >= r.issuedAt and i <= r.completedAt:
                tmppara += 1
        height.append(tmppara)
    
    return height

def getStats(requests, parareqs, maxdepth, opts, stalls):
    
    totalLatency = 0.0
    totalStall = 0.0
    totalIssueToStall = 0.0
    numReqs = 0
    
    for r in requests:
        totalLatency += r.completedAt - r.issuedAt
        if r.requestCausedStall:
            totalStall += r.requestStallResumedAt - r.requestCausedStallAt
            totalIssueToStall += r.requestCausedStallAt - r.issuedAt
        numReqs += 1
    
    print
    print "Total latency:     ", totalLatency
    print "Average latency:   ", totalLatency /numReqs
    print "Total stall:       ", totalStall
    print "Stall per request: ", totalStall / numReqs
    print "T. issue to stall: ", totalIssueToStall
    print "Overlap:           ", totalStall / totalLatency
    print "Max. depth:        ", maxdepth
    print "Avg st. per level: ", sum(stalls) / len(stalls)
    
    if opts.avgAloneLat > 0:
        print "Alone stall est.   ", opts.avgAloneLat*maxdepth

def buildRequestGraph(requests):
    
    roots = []
    
    for i in range(len(requests)):
        minDistance = 10000000000
        minIndex = -1
        
        for j in range(len(requests)):
            if j >= i:
                break
            
            difference = requests[i].issuedAt - requests[j].completedAt
            if difference > 0 and difference < minDistance:
                minIndex = j
                minDistance = difference
        
        assert requests[i].dependsOn == None        
        if minIndex != -1:
            requests[i].setDependsOn(requests[minIndex])
            requests[minIndex].addChild(requests[i])
        else:
            roots.append(requests[i]) 
    
    return roots

def makeDepencencyDot(roots):
    
    maxdepths = []
    
    dotfile = open("dependencies.dot", "w")
    dotfile.write("digraph G{\n")
    for r in roots:
        maxdepths.append(traverseDependencies(r, dotfile, 0))
    dotfile.write("}\n")
    dotfile.flush()
    dotfile.close()
    
    return max(maxdepths)
    
def traverseDependencies(node, dotfile, depth):
    depth += 1
    depths = []
    for c in node.children:
        if node.requestCausedStall:
            dotfile.write(str(node.id)+" [color=red]")
        dotfile.write(str(node.id)+" -> "+str(c.id)+" [label="+str(int(c.issuedAt-node.completedAt))+"]\n")
        depths.append(traverseDependencies(c, dotfile, depth))
    
    if node.children == []:
        return depth
    return max(depths)

def treeStalls(roots, maxdepth):
    buffer = [0 for i in range(maxdepth)]
    
    for r in roots:
        findStallPerTreeLevel(r, 0, buffer)
        
    return buffer
    

def findStallPerTreeLevel(node, depth, buffer):
    if node.requestCausedStall:
        buffer[depth] += node.requestStallResumedAt - node.requestCausedStallAt
    
    for c in node.children:
        findStallPerTreeLevel(c, depth+1, buffer)

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
    upperbound = opts.plotSize
    if upperbound == 0:
        upperbound = tracecontent.getNumRows()+1
    cnt = 0
    for i in range(tracecontent.getNumRows()):
        row = tracecontent.getRow(i)
        if row[1] >= opts.plotFrom and cnt < upperbound:
            requests.append(Request(row))
            cnt += 1
    
    parareqs = [[]]
    outstandingReqs = [None]
    for req in requests:
        pos = getFreePosition(outstandingReqs, req)
        if pos >= len(parareqs):
            parareqs.append([])
            outstandingReqs.append(None)
        parareqs[pos].append(req)
        outstandingReqs[pos] = req
    
    
    roots = buildRequestGraph(requests)
    maxdepth = makeDepencencyDot(roots)
    stalls = treeStalls(roots, maxdepth)
    getStats(requests, parareqs, maxdepth, opts, stalls)
    
    if opts.plotType != "":
        if opts.plotType == "requests":
            plotdata, colors = makePlotData(parareqs)
            plot(plotdata, colors)
        elif opts.plotType == "heightbar":
            heightdata = createHeightData(parareqs, requests)
            plotRawBarChart(heightdata)
        elif opts.plotType == "heighthistogram":
            heightdata = createHeightData(parareqs, requests)
            plotHistogram(heightdata)
        else:
            print "Unknown plot type"
        
        
if __name__ == '__main__':
    main()