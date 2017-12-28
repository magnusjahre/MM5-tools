#!/usr/bin/env python

import sys
import random
import math
from optparse import OptionParser

def parseArgs():
    
    parser = OptionParser(usage="stencil.py [options]")
    parser.add_option("--verbose", '-v', action="store_true", dest="verbose", default=False, help="Print all lines")
    parser.add_option("--stencil-width", action="store", dest="width", default=1, type="int", help="The width of the one-dimensional symmetric stencil")
    parser.add_option("--depth", action="store", dest="depth", default=2, type="int", help="The number of iterations to compute in a single push")
    parser.add_option("--input-size", action="store", dest="inputSize", default=10, type="int", help="Size of the unpadded input array")
    parser.add_option("--parallel-inputs", action="store", dest="paraInputs", default=2, type="int", help="Number of inputs to process on each fetch")
    parser.add_option("--no-coeff", action="store_true", dest="noCoeff", default=False, help="Disable coefficients to simplify debugging")
    parser.add_option("--debug", action="store_true", dest="debugOut", default=False, help="Output debug prints")
    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Supress output")
    parser.add_option("--regression-tests", action="store_true", dest="regressionTests", default=False, help="Run regression test suite (all other parameters are ignored)")
    opts, args = parser.parse_args()
    
    if len(args) != 0:
        print "Usage:"
        print parser.usage
        sys.exit()
    
    return opts, args

def eToStr(e):
    return "%.2f" % e

def dataToStr(b):
    return [eToStr(e) for e in b]

class Coefficients:
    
    def __init__(self, width, noCoeff):
        self.noCoeff = noCoeff
        self.width = width
        
        if noCoeff:
            self.coeffs = [1.0 for i in range(2*width+1)]
        else:
            self.coeffs = []
            for i in range(self.width):
                self.coeffs.append(random.random())
            rev = [a for a in self.coeffs]
            rev.reverse()
            self.coeffs = self.coeffs + [1.0] + rev

    def getSingle(self, i):
        assert i >= 0
        assert i < len(self.coeffs)
        
        if self.noCoeff:
            return 1.0
        return self.coeffs[i]
    
    def getAll(self):
        return self.coeffs
 
class CoefficientNode:
    
    def __init__(self, nodeID, depth):
        self.depth = depth
        self.ID = nodeID
        
        self.coefficient = 0
        self.value = 1
        self.visited = False
        self.childWeights = []
        self.children = []
        
    def addChildren(self, children, weights):
        assert len(children) == len(weights)
        self.children = children
        self.childWeights = weights

def stencil(a, i, width, coeffs):
    start = i-width
    if start < 0:
        start = 0
    end = i+width+1
    if end > len(a):
        end = len(a)
    
    s = 0
    for i in range(start, end):
        s += coeffs.getSingle(i-start)*a[i]
        
    return s

def computeNaive(indata, coefficients, spec):
    if not spec.quiet:
        print
        print "=====","Naive implementation with "+str(2*spec.width+1)+" point stencil","====="
        print
    
    printSegment = spec.width*spec.depth
    
    a = [a for a in indata]
    b = [0.0 for i in range(len(a))]
    if not spec.quiet:
        print "Input: ", dataToStr(a)[printSegment:-printSegment]
    
    for n in range(spec.depth):
        for i in range(len(a))[spec.width:-spec.width]:
            b[i] = stencil(a, i, spec.width, coefficients)
        if not spec.quiet:
            print n+1,dataToStr(b)[printSegment:-printSegment]
        for i in range(len(a)):
            a[i] = b[i]
    
    return a[printSegment:-printSegment]

def createRepeatPattern(repeats, opts):

    padval = 0
    
    prePad = []
    postPad = [padval for i in range(2*opts.width)]
    
    shiftedRepeats = []
    for i in range(2*opts.width+1):
        shiftedRepeats.append(prePad + repeats + postPad)
        prePad.append(padval)
        postPad = postPad[:len(postPad)-1]
        
    newRepeats = [padval for i in range(len(repeats)+2*opts.width)]
    for i in range(len(shiftedRepeats)):
        for j in range(len(newRepeats)):
            newRepeats[j] += shiftedRepeats[i][j]
                
    return newRepeats

def buildCoefficientGraph(coeffs, spec):
    
    # 1. Add nodes organized by level
    nodes = [[CoefficientNode(0, 0)]]
    nodeID = 1
    for d in range(spec.depth+1)[1:]:
        newLength = len(nodes[d-1])+2*spec.width
        nodes.append([CoefficientNode(nodeID+i, d) for i in range(newLength)])
        nodeID += newLength
    assert len(nodes[-1]) == 2 * spec.width*spec.depth + 1
    
    # 2. Update the children arrays and add appropriate weights
    stencilSize = 2*spec.width+1
    for nodeLevel in range(len(nodes)-1):
        i = 0
        while i+stencilSize <= len(nodes[nodeLevel+1]):
            nodes[nodeLevel][i].addChildren(nodes[nodeLevel+1][i:i+stencilSize], coeffs)
            i += 1
    
    return nodes[0][0]
    

def updateCoefficients(node, debugOut):
    if debugOut:
        print "-- Visiting node ", node.ID, "at depth", node.depth
    
    if node.children == []:
        node.coefficient += node.value
        if debugOut:
            print "-- Leaf node: Accumulating current value ", node.value, "to compute new coefficient", node.coefficient
    else:
        for i in range(len(node.children)):
            newWeight = node.value * node.childWeights[i] 
            node.children[i].value = newWeight
            if debugOut:
                print "-- Updating weight of child node ", node.children[i].ID, "to", newWeight, "index", i
            
            updateCoefficients(node.children[i], debugOut)
            
def retrieveCoefficients(node):
    if node.children == []:
        if not node.visited:
            node.visited = True
            return [node.coefficient]
        else:
            return []
    
    retdata = []
    for c in node.children:
        retdata = retdata + retrieveCoefficients(c)
    
    return retdata

def computeCoeffcients(coeffObj, spec):
    if spec.debugOut:
        print
        print "Computing coefficients for stencil width", str(2*spec.width+1),"and depth",spec.depth
    
    root = buildCoefficientGraph(coeffObj.getAll(), spec)
    updateCoefficients(root, spec.debugOut)
    coeffs = retrieveCoefficients(root)

    if spec.debugOut:
        print "Coefficients:", dataToStr(coeffs)

    return coeffs

def computeImpulseResponse(coeffObj, spec):
    padSize = spec.width*(spec.depth-1)
    impulse = [0.0 for i in range(padSize)] + [0.0 for i in range(2*spec.width+1)] + [0.0 for i in range(padSize)] 
    impulse[len(impulse)/2] = 1.0 #Correct since we assume that all stencil lenghts are odd numbers and integer div cuts decimals
    
    assert len(impulse) == 2*spec.width*spec.depth+1
    
    coeffs = coeffObj.getAll()
    for d in range(spec.depth):
        tmp = [0.0 for i in range(len(impulse))]
        for i in range(len(impulse)):
            for j in range(len(coeffs)):
                offset = j-spec.width+i
                if offset >= 0 and offset < len(impulse):
                    tmp[i] += coeffs[j]*impulse[offset]
        impulse = [tmp[i] for i in range(len(tmp))]
         
    return impulse

def computeOurScheme(indata, coefficients, spec):
    
    if not spec.quiet:
        print
        print "=====","The scheme with depth", spec.depth,"====="
    
    resultBufferSize = 2 * spec.width*spec.depth + spec.paraInputs
    numIncompleteResults = spec.depth*spec.width
    assert numIncompleteResults > 0
    numOutputValues = len(indata)
    if not spec.quiet:
        print "Input: ", dataToStr(indata)
    
    # End-padding is a hack ensure that the impact of the final elements propagate to the output
    a = [a for a in indata] + [0.0 for x in range(numIncompleteResults)]
    resultBuffer = [0 for i in range(resultBufferSize)]
    
    graphCoeff = []
    if spec.depth <= 10:
        graphCoeff = computeCoeffcients(coefficients, spec)
        
    impulseCoeff = computeImpulseResponse(coefficients, spec)
    
    if graphCoeff != []:
        if not spec.quiet:
            print "Graph coefficients:  ", dataToStr(graphCoeff)
            print "Impulse coefficients:", dataToStr(impulseCoeff)
        
        assert len(graphCoeff) == len(impulseCoeff)
        for i in range(len(graphCoeff)):
            assert fpValsAreEqual(graphCoeff[i], impulseCoeff[i])
    
    if not spec.quiet:
        print
        print "Performing stencil computation:"
    
    outputs = []
    for inputStart in range(len(a))[::spec.paraInputs]:
    
        inputs = a[inputStart:inputStart+spec.paraInputs]
        
        for i in range(len(inputs)):
            for j in range(len(impulseCoeff)):
                resultBuffer[i+j] += impulseCoeff[j]*inputs[i]
                
        if spec.debugOut:
            print "-- Result buffer @",inputStart,":",dataToStr(resultBuffer)
        
        for i in range(spec.paraInputs):
            outputs.append(resultBuffer[i])
            
        for i in range(resultBufferSize - spec.paraInputs):
            resultBuffer[i] = resultBuffer[i+spec.paraInputs]
            
        for i in range(resultBufferSize - spec.paraInputs, resultBufferSize):
            resultBuffer[i] = 0.0 
            

    result = outputs[numIncompleteResults:numIncompleteResults+numOutputValues]
    if not spec.quiet:
        print "Output:", dataToStr(result)
    return result

def createRandomVector(veclen):
    random.seed(15)
    indata = []
    while len(indata) < veclen:
        testVal = random.randint(1, veclen)
        if testVal not in indata:
            indata.append(testVal)
    return indata

def generateInput(spec):
    indata = createRandomVector(spec.inputSize)
    paddedData = [0.0 for a in range(spec.width*spec.depth)]+[i for i in indata]+[0.0 for a in range(spec.width*spec.depth)]
    coefficients = Coefficients(spec.width, spec.noCoeff)
    
    return indata, paddedData, coefficients
    
class StencilSpec:
    
    def __init__(self):
        self.width = 0
        self.depth = 0 
        self.paraInputs = 0
        self.debugOut = False
        self.inputSize = 0
        self.noCoeff = False
        self.quiet = True
        
    def setFromOptions(self, opts):
        self.width = opts.width
        self.depth = opts.depth
        self.paraInputs = opts.paraInputs
        self.debugOut = opts.debugOut
        self.inputSize = opts.inputSize
        self.noCoeff = opts.noCoeff
        self.quiet = opts.quiet

def fpValsAreEqual(a,b):
    
    baseEpsilon= 10**-10
    newEpsilon = baseEpsilon*(10**int(math.log10(a)))
    if newEpsilon <= baseEpsilon:
        newEpsilon = baseEpsilon
    
    if abs(a-b) < newEpsilon:
        return True
    return False

def compareOutput(naive, scheme):
    if len(naive) != len(scheme):
        return False
    for i in range(len(naive)):
        if not fpValsAreEqual(naive[i], scheme[i]):
            return False
    return True

def printDifferences(naive, scheme):
    if len(naive) != len(scheme):
        print "The length of the arrays differ"
        return
    for i in range(len(naive)):
        if not fpValsAreEqual(naive[i], scheme[i]):
            print "Arrays differ at position",i,"naive",eToStr(naive[i]),"scheme",eToStr(scheme[i])

def evaluateSingle(spec):
    indata, paddedData, coefficients = generateInput(spec)
    naive = computeNaive(paddedData, coefficients, spec)
    scheme = computeOurScheme(indata, coefficients, spec)
    return compareOutput(naive, scheme)

def runRegressionTests():
    print 
    print "Regression test suite"
    print

    # Baseline configuration
    spec = StencilSpec()
    spec.inputSize = 1000
    spec.depth = 5
    spec.paraInputs = 10
    spec.width = 1
    
    tests = 0
    passed = 0
    
    print "Depth"
    depths = [i for i in range(1,20)] + [i for i in range(20,101,5)]
    for d in depths:
        spec.depth = d
        res = evaluateSingle(spec)
        print str(d), res
        sys.stdout.flush()
        
        if res:
            passed += 1
        tests += 1
        
    spec.depth = 5
    
    print
    print "Parallel inputs"
    for i in range(1,20):
        spec.paraInputs = i
        res = evaluateSingle(spec)
        print str(i), res
        sys.stdout.flush()
        
        if res:
            passed += 1
        tests += 1

    spec.paraInputs = 10
    
    print
    print "Stencil radius"
    for w in range(1, 15):
        spec.width = w
        res = evaluateSingle(spec)
        print str(w), res
        sys.stdout.flush()
        
        if res:
            passed += 1
        tests += 1

    print
    print "SUMMARY: Passed",passed,"out of",tests,"tests."
    print
    

def main():
    opts, args = parseArgs()
    
    if opts.regressionTests:
        runRegressionTests()
        return
    
    print
    print "Stencil computing test program"
    
    spec = StencilSpec()
    spec.setFromOptions(opts)
    indata, paddedData, coefficients = generateInput(spec)
    
    print "Using stencil coefficients: "+str(dataToStr(coefficients.getAll()))
    
    naive = computeNaive(paddedData, coefficients, spec)
    scheme = computeOurScheme(indata, coefficients, spec)
    
    equal = compareOutput(naive, scheme)
    print
    if equal:
        print "Compute methods are equivalent"
    else:
        print "Compute methods produced different output"
        printDifferences(naive, scheme)
        

if __name__ == '__main__':
    main()

