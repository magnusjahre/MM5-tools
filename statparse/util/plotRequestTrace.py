#!/usr/bin/env python
import sys
import os

from optparse import OptionParser
from statparse.tracefile.tracefileData import TracefileData
from statparse.plotResults import plotRawBarChart, plotHistogram

class Node():
    
    def __init__(self):
        self.dependsOn = None
        self.children = []
        self.issuedAt = 0
        self.completedAt = 0
        self.visited = False
        self.reachable = False

    def setDependsOn(self, req):
        self.dependsOn = req
        
    def addChild(self, req):
        self.children.append(req)

class Request(Node):
       
    def __init__(self, row):
        Node.__init__(self)
        if row != []:
            self._parseRow(row)
            
    def setTestState(self, isat, compat, ident):
        self.issuedAt = isat
        self.completedAt = compat
        self.id = ident
     
    def _parseRow(self, row):
        self.curTick = row[0]
        self.id = int(row[1])
        self.address = row[2]
        self.issuedAt = row[3]
        self.completedAt = row[4]
        
        if row[5] == 1:
            self.sharedCacheMiss = True
        else:
            self.sharedCacheMiss = False
        
        if row[6] == 1:
            self.privModeSharedCacheMiss = True
        else:
            self.privModeSharedCacheMiss = False
            
        if row[7] > 0:
            self.requestCausedStall = True    
        else:
            self.requestCausedStall = False
            
        self.requestCausedStallAt = row[7]
        self.requestStallResumedAt = row[8]
        
    def getName(self):
        return "request"+str(self.id) 
        
    def distanceToParentCompute(self, compute):
        distance = self.issuedAt - compute.issuedAt
        if distance <= 0:
            return sys.maxint
        return distance
    
    def distanceToChildCompute(self, compute):
        distance = compute.completedAt - self.completedAt
        if distance <= 0:
            return sys.maxint
        return distance
        
    def __str__(self):
        return str(self.id)+" (issued at "+str(self.issuedAt)+", completed at "+str(self.completedAt)+")"
    
class Compute(Node):
    
    def __init__(self, compFrom, compTo, ident):
        Node.__init__(self)
        assert compFrom <= compTo
        self.issuedAt = compFrom
        self.completedAt = compTo
        
        self.nodename = "compute"+str(ident)
        
    def duration(self):
        return self.completedAt - self.issuedAt
    
    def getName(self):
        return str(self.nodename)
    
    def __str__(self):
        return self.getName()+" (from "+str(self.issuedAt)+" to "+str(self.completedAt)+")"


class BurstLevelStats:
    
    def __init__(self, depth):
        self.startedAt = sys.maxint
        self.finishedAt = 0
        self.numReqs = 0 
        self.depth = depth
        
    def addReq(self, start, end):
        if start < self.startedAt:
            self.startedAt = start
        if end > self.finishedAt:
            self.finishedAt = end
        self.numReqs += 1
        
    def lat(self):
        return self.finishedAt - self.startedAt
        
    def __str__(self):
        return "Burst "+str(self.depth)+", from "+str(self.startedAt)+" to "+str(self.finishedAt)+" ("+str(self.lat())+"), "+str(self.numReqs)+" reqs"

class BurstProcessor:
    
    def __init__(self, maxdepth):
        self.burstDataList = [BurstLevelStats(i) for i in range(maxdepth)]
        self.sumBurstCompOverlap = 0

    def findBurstLatency(self, roots):
        for r in roots:
            self._findBurstLatencyPerLevel(r, 0)

    def _findBurstLatencyPerLevel(self, node, depth):
        node.visited = True
        for c in node.children:
            if not c.visited:
                if c.__class__.__name__ == "Request":
                    # Requests that have the same commit period as parent and child 
                    # are completely hidden
                    if node not in c.children:
                        self.burstDataList[depth].addReq(c.issuedAt, c.completedAt)
                    self._findBurstLatencyPerLevel(c, depth+1)
                else:
                    self._findBurstLatencyPerLevel(c, depth)

def parseArgs():
    parser = OptionParser(usage="analyzeTrace.py [options] filename1")

    plotTypes = ["requests", "heightbar", "heighthistogram"]

    parser.add_option("-q", "--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("-f", "--plot-from", action="store", type="int", dest="plotFrom", default=0, help="plot from this request id")
    parser.add_option("-s", "--plot-size", action="store", type="int", dest="plotSize", default=0, help="plot this number of requests")
    parser.add_option("-t", "--plot-type", action="store", type="string", dest="plotType", default="", help="type of plot, one of "+str(plotTypes))
    parser.add_option("--max-recursion-maxdepth", action="store", type="int", dest="recursionDepth", default=0, help="Set the maximum recursion maxdepth")
    parser.add_option("--print-bp", action="store_true", dest="printBurstStats", default=False, help="Print statistics about each burst (verbose)")
    parser.add_option("--cpt-edge-trace", action="store", dest="cptEdgeTrace", default="", help="Read Critical Path Table edge data from this file")
    
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

def getStats(requests, parareqs, maxdepth, opts, burstdata):
    
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
    print "Num reqs:          ", len(requests)
    print "Max. maxdepth:        ", maxdepth
        
    computeBurstStats(burstdata, totalLatency /numReqs, opts, totalStall, maxdepth)
    

def findCompute(requests):
    stallreqs = []
    computeNodes = []
    for r in requests:
        if r.requestCausedStall:
            stallreqs.append(r)
    
    computeNodes.append(Compute(0, stallreqs[0].requestCausedStallAt, "Init"))
    for i in range(1, len(stallreqs)):
        computeNodes.append(Compute(stallreqs[i-1].requestStallResumedAt, stallreqs[i].requestCausedStallAt-1, stallreqs[i-1].id))
    #del stallreqs[-1]
     
    return computeNodes


def buildCombinedGraph(reqs, commits):
    for r in reqs:  
        minDistance = sys.maxint
        minParent = None
        for c in commits:
            if r.distanceToParentCompute(c) < minDistance:                
                minDistance = r.distanceToParentCompute(c) 
                minParent = c
        
        if minParent != None:
            minParent.addChild(r)
        
        minDistance = sys.maxint
        minChild = None

        for c in commits:
            if r.distanceToChildCompute(c) < minDistance:
                minDistance = r.distanceToChildCompute(c) 
                minChild = c
        
        if minChild != None:
            r.addChild(minChild)
        
    return [commits[0]]
                
                

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
    if node.__class__.__name__ == "Request":
        dotfile.write(node.getName()+" [label="+str(int(node.address))+"]")
        depth += 1
    depths = []
  
    node.visited = True
    
    for c in node.children:
        if c.__class__.__name__ == "Request":
            dotfile.write(str(node.getName())+" -> "+str(c.getName())+" [label=\""+str(int(c.issuedAt-node.issuedAt))+"\"]\n")
        else:
            dotfile.write(str(c.getName())+" [shape=box, label=\""+c.getName()+"\\n"+str(int(c.completedAt-c.issuedAt))+"\", style=filled, color=grey]\n")
            dotfile.write(str(node.getName())+" -> "+c.getName()+"\n")
        if not c.visited:
            depths.append(traverseDependencies(c, dotfile, depth))
    
    if depths == []:
        return depth
    return max(depths)

def computeBurstStats(burstdata, avglat, opts, totalStall, cpl):
    burstlatsum = 0
    overlapsum = 0
    numReqs = 0
    for bd in burstdata.burstDataList:
        if bd.startedAt < bd.finishedAt:
            if opts.printBurstStats:
                print str(bd)
            burstlatsum += bd.lat()
            numReqs += bd.numReqs
    
    for i in range(1,len(burstdata.burstDataList)):
        if burstdata.burstDataList[i].startedAt < burstdata.burstDataList[i].finishedAt and burstdata.burstDataList[i-1].startedAt < burstdata.burstDataList[i-1].finishedAt:
            overlap = burstdata.burstDataList[i-1].finishedAt - burstdata.burstDataList[i].startedAt
            if overlap > 0:
                overlapsum += overlap
                
    modelStallEst = burstlatsum-overlapsum-burstdata.sumBurstCompOverlap
                
    print
    print "Avg burst latency:      "+str(burstlatsum/cpl)
    print "Sum burst latency:      "+str(burstlatsum)
    print "Sum interburst overlap: "+str(overlapsum)
    print "Sum comp burst overlap: "+str(burstdata.sumBurstCompOverlap)
    print "Model stall estimate:   "+str(modelStallEst)
    print "Model stall error:      "+str(((modelStallEst-totalStall)/totalStall)*100)+" %"
    print "Requests in burstlist:  "+str(numReqs) # the roots are missing, so this is not the exact number of reqs

def mergeNodes(compnodes, requests):
    
    for i in range(1, len(requests)):
        assert requests[i-1].completedAt <= requests[i].completedAt
    
    for i in range(1, len(compnodes)):    
        assert compnodes[i-1].completedAt <= compnodes[i].completedAt 
    
    allnodes = []
    while not (compnodes == [] and requests == []):
        if compnodes != [] and requests != []:
            if compnodes[0].completedAt <= requests[0].completedAt:
                allnodes.append(compnodes.pop(0))
            else:
                allnodes.append(requests.pop(0))
                
        if compnodes == [] and requests != []:
            allnodes.append(requests.pop(0))
        
        if requests == [] and compnodes != []:
            allnodes.append(compnodes.pop(0))
    
    for i in range(1, len(allnodes)):
        assert allnodes[i-1].completedAt <= allnodes[i].completedAt 
    
    return allnodes

def verifyReachability(roots, reqs, comp):
    for r in roots:
        doVerifyTraverse(r)
    
    passed = True
    for r in reqs:
        if not r.reachable:
            print "Not reachable: "+str(r)
            passed = False
            
    for c in comp:
        if not c.reachable:
            print "Not reachable: "+str(c)
            passed = False
            
    if not passed:
        print "WARNING: Reachability analysis failed"
    clearVisited(reqs, comp)

def doVerifyTraverse(node):
    node.visited = True
    node.reachable = True
    for c in node.children:
        if not c.visited:
            doVerifyTraverse(c)

def clearVisited(reqs, coms):
    for r in reqs:
        r.visited = False
    for c in coms:
        c.visited = False

def findOverlap(reqs, coms):
    overlap = 0
    for c in coms:
        coverage = []
        for r in reqs:
            if r.completedAt < c.issuedAt or r.issuedAt > c.completedAt:
                # Not overlapping continue
                continue
            
            start = r.issuedAt
            if r.issuedAt < c.issuedAt:
                start = c.issuedAt
                
            end = r.completedAt
            if end > c.completedAt:
                end = c.completedAt
            
            coverage.append( (start, end) )
            
        curComOverlap = 0
        for i in range(int(c.issuedAt), int(c.completedAt)):
            isOverlapped = False
            for cs, ce in coverage:
                if i >= cs and i < ce:
                    isOverlapped = True
                    break
            if isOverlapped:
                curComOverlap += 1
                    
        overlap += curComOverlap
    
    return float(overlap)

def buildGraphData(opts, filename):
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
    
    compnodes = findCompute(requests)
        
    roots = buildCombinedGraph(requests, compnodes)
    verifyReachability(roots, requests, compnodes)
    maxdepth = makeDepencencyDot(roots)
    clearVisited(requests, compnodes)
    
    burstData = BurstProcessor(maxdepth)
    burstData.findBurstLatency(roots)
    burstData.sumBurstCompOverlap = findOverlap(requests, compnodes)
    
    getStats(requests, parareqs, maxdepth, opts, burstData)
    
    clearVisited(requests, compnodes)
    
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
            
    assert len(roots) == 1
    return roots[0]

class CPTNode:
    COMPUTE = 0
    REQUEST = 1
    
    def __init__(self, id, type):
        self.id = int(id)
        self.type = int(type)
        self.children = []
        self.parents = []
        self.visited = False
        self.missing = False
        self.incomingEdges = 0
        self.maxdepth = 0
        
    def addChild(self, node):
        self.children.append(node)
    
    def addParent(self, node):
        self.parents.append(node)
    
    def getName(self):
        if self.type == self.REQUEST:
            return "request"+str(self.id)
        return "comp"+str(self.id)

def checkForNodes(computeNodes, requestNodes, computeId, requestId):
    if computeId not in computeNodes:
        computeNodes[computeId] = CPTNode(computeId, CPTNode.COMPUTE)
                
    if requestId not in requestNodes:
        requestNodes[requestId] = CPTNode(requestId, CPTNode.REQUEST)

def buildCPTGraph(tracecontent):
    computeNodes = {}
    requestNodes = {}
    
    for i in range(tracecontent.getNumRows()):
        row = tracecontent.getRow(i)
        
        if row[3] == CPTNode.REQUEST:
            requestId = row[1]
            computeId = row[2]
            
            checkForNodes(computeNodes, requestNodes, computeId, requestId)
            requestNodes[requestId].addChild(computeNodes[computeId])
            
        else:
            assert row[3] == CPTNode.COMPUTE
            computeId = row[1]
            requestId = row[2]
            
            checkForNodes(computeNodes, requestNodes, computeId, requestId)
            
            computeNodes[computeId].addChild(requestNodes[requestId])
    
    return computeNodes, requestNodes

def clearCPTVisited(nodes):
    for id in nodes:
        nodes[id].visited = False

def populateCPTParentCount(root, cn, rn):
    
    workqueue = [root]
    while workqueue != []:
        node = workqueue.pop(0)
        if node.visited:
            continue
        
        node.visited = True
        for c in node.children:
            c.incomingEdges += 1
            if not c.visited:
                workqueue.append(c)
    
    for c in rn:
        assert rn[c].incomingEdges == 1
        assert rn[c].incomingEdges == len(rn[c].parents)
        
    for c in cn:
        assert cn[c].incomingEdges == len(cn[c].parents)
    
    clearCPTVisited(cn)
    clearCPTVisited(rn)

def populateCPTParents(computeNodes, requestNodes):
    root = computeNodes[findCPTRootKey(computeNodes)]
    workqueue = [root]
    
    while workqueue != []:
        node = workqueue.pop(0)
        if node.visited:
            continue
        
        node.visited = True
        for c in node.children:
            c.addParent(node)
            if not c.visited:
                workqueue.append(c)
    
    clearCPTVisited(computeNodes)    
    clearCPTVisited(requestNodes)

def removeCycles(cn, rn):
    for compID in cn:
        comp = cn[compID]
        for req in comp.children:
            if comp in req.children:
                req.children.remove(comp)
                comp.parents.remove(req)

def populateMaximumDepths(computeNodes, requestNodes):

    root = computeNodes[findCPTRootKey(computeNodes)]
    removeCycles(computeNodes, requestNodes)
    populateCPTParentCount(root, computeNodes, requestNodes)
    
    workqueue = [root]
    toposort = []
    
    while workqueue != []:
        node = workqueue.pop(0)
        node.visited = True
        toposort.append(node)
        
        for c in node.children:
            c.incomingEdges = c.incomingEdges - 1
            if not c.visited and c.incomingEdges == 0:
                workqueue.append(c)
    
    for n in toposort:
        parentMaxdepth = 0
        for p in n.parents:
            if p.maxdepth > parentMaxdepth:
                parentMaxdepth = p.maxdepth
        if n.type == CPTNode.REQUEST:
            n.maxdepth = parentMaxdepth+1
        else:
            n.maxdepth = parentMaxdepth
            
    for id in computeNodes:
        if not computeNodes[id].visited:
            print "Not visited", computeNodes[id].id
        assert computeNodes[id].visited        
        
    for addr in requestNodes:
        assert requestNodes[addr].visited
    
    clearCPTVisited(computeNodes)    
    clearCPTVisited(requestNodes)

def findCPTRootKey(computeNodes):
    keys = computeNodes.keys()
    keys.sort()
    return keys[0]

def writeCPTDotNode(node, dotfile):
    
    if node.type == CPTNode.REQUEST:
        dotfile.write(node.getName()+" [label=\""+str(int(node.id))+"\\nMaxD: "+str(node.maxdepth)+"\"")
        if node.missing:
            dotfile.write(", color=red")
        dotfile.write("]\n")

    else:
        assert node.type == CPTNode.COMPUTE
        dotfile.write(node.getName()+" [shape=box, label=\""+str(node.id)+"\\nMaxD: "+str(node.maxdepth)+"\", style=filled, ")
        if node.missing:
            dotfile.write("color=red")
        else:
            dotfile.write("color=grey")
        dotfile.write("]\n")
    
    node.visited = True
    
    for c in node.children:
        dotfile.write(str(node.getName())+" -> "+c.getName()+"\n")
        if not c.visited:
            writeCPTDotNode(c, dotfile)

def writeCPTDot(computeNodes, requestNodes):
    dotfile = open("cpt-dependencies.dot", "w")
    dotfile.write("digraph G{\n")
    writeCPTDotNode(computeNodes[findCPTRootKey(computeNodes)], dotfile)
    dotfile.write("}\n")
    dotfile.flush()
    dotfile.close()
    
    clearCPTVisited(computeNodes)    
    clearCPTVisited(requestNodes)

def processCPTData(opts):
    tracecontent = TracefileData(opts.cptEdgeTrace)
    tracecontent.readTracefile()
    
    computeNodes, requestNodes = buildCPTGraph(tracecontent)
    populateCPTParents(computeNodes, requestNodes)
    populateMaximumDepths(computeNodes, requestNodes)
    
    return computeNodes, requestNodes

def traverseGraphToAnnotate(graphNode, cptNode):
    if graphNode.visited:
        cptNode.missing = True
    
    graphNode.visited = True
    cptNode.visited = True
    
    if graphNode.__class__.__name__ == "Request":
        assert len(graphNode.children) <= 1
        assert len(cptNode.children) <= 1
        
        if len(graphNode.children) != len(cptNode.children):
            if(len(cptNode.children) == 1):
                cptNode.children[0].missing = True
        
        elif len(graphNode.children) == 1:
            if not graphNode.children[0].visited:
                traverseGraphToAnnotate(graphNode.children[0], cptNode.children[0]) 
    else:
        seen = {}
        for c in cptNode.children:
            seen[c.id] = False
        
        for c in graphNode.children:
            seen[c.address] = True
                
        for c in cptNode.children:
            if not seen[c.id]:
                c.missing = True
    
        for gc in graphNode.children:
            found = False
            for cc in cptNode.children:
                if gc.address == cc.id:
                    assert found == False
                    traverseGraphToAnnotate(gc, cc)
                    found = True

def annotateCPT(graphroot, cptroot):
    traverseGraphToAnnotate(graphroot, cptroot)

def main():

    opts,args = parseArgs()
    
    if not opts.quiet:
        print
        print "Running trace file analysis..."
    
    filename = args[0]
    if not os.path.exists(filename):
        print "Error: File "+str(filename)+" not found"
        return -1
    
    if opts.recursionDepth > 0:
        print "Info: setting maximum recursion maxdepth to "+str(opts.recursionDepth)
        sys.setrecursionlimit(opts.recursionDepth)
    
    graphroot = buildGraphData(opts, filename)
    if opts.cptEdgeTrace != "":
        cptComputeNodes, cptRequestNodes = processCPTData(opts)
        annotateCPT(graphroot, cptComputeNodes[findCPTRootKey(cptComputeNodes)])
        clearCPTVisited(cptComputeNodes)
        clearCPTVisited(cptRequestNodes)
        writeCPTDot(cptComputeNodes, cptRequestNodes)
        
if __name__ == '__main__':
    main()
