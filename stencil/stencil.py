#!/usr/bin/env python

import sys
import random
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

def getStaticCoefficient(opts):
    if opts.noCoeff:
        return 1.0
    return 1.0/(opts.width*2+1)

def stencil(a, i, opts):
    start = i-opts.width
    if start < 0:
        start = 0
    end = i+opts.width+1
    if end > len(a):
        end = len(a)
    
    s = 0
    for i in range(start, end):
        s += a[i]
        
    return getStaticCoefficient(opts)*s

def computeNaive(indata, opts):
    print
    print "Naive implementation with "+str(2*opts.width+1)+" point stencil"
    print
    
    printSegment = opts.width*opts.depth
    
    a = [a for a in indata]
    b = [0.0 for i in range(len(a))]
    print "0", dataToStr(a)[printSegment:-printSegment]
    
    for n in range(opts.depth):
        for i in range(len(a))[opts.width:-opts.width]:
            b[i] = stencil(a, i, opts)
        print n+1,dataToStr(b)[printSegment:-printSegment]
        for i in range(len(a)):
            a[i] = b[i]
    
    return a[printSegment:-printSegment]

def createRepeatPattern(repeats, opts):
    
    assert opts.width == 1
    r1 = repeats + [0, 0]
    r2 = [0] + repeats + [0]
    r3 = [0,0] + repeats
    
    rOut = [0 for i in range(len(r1))]
    for i in range(len(r1)):
        rOut[i] = r1[i] + r2[i] + r3[i]
    
    return rOut

def computeRepeats(repeats, affectedResults, opts):
    # Handles depth equal to 1
    if len(repeats) == affectedResults:
        return repeats
    
    repeats = createRepeatPattern(repeats, opts)
    if opts.debugOut:
        print "Repeat pattern at length "+str(len(repeats))+" is "+str(repeats)
    
    if len(repeats) < affectedResults:
        repeats = computeRepeats(repeats, affectedResults, opts) 
    return repeats

def computeCoeffcients(opts):
    # Note: procedure assumes symetric stencil
    numAffectedResults = 2 * opts.width*opts.depth + 1
    stencilWidth = 2*opts.width+1
    
    repeats = computeRepeats([1 for i in range(stencilWidth)], numAffectedResults, opts)
    
    if opts.debugOut:
        print "Repeats:", str(repeats)
    
    coeffs = [(getStaticCoefficient(opts)**opts.depth)*r for r in repeats]
    
    if opts.debugOut:
        print "Coefficients:", dataToStr(coeffs)
    
    return coeffs

def computeOurScheme(indata, opts):
    
    print
    print "The scheme with depth", opts.depth
    print

    resultBufferSize = 2 * opts.width*opts.depth + opts.paraInputs
    numIncompleteResults = 2*opts.width+opts.depth-2
    numOutputValues = len(indata)
    print "0", dataToStr(indata)
    
    # End-padding is a hack ensure that the impact of the final elements propagate to the output
    a = [a for a in indata] + [0.0 for x in range(numIncompleteResults)]
    resultBuffer = [0 for i in range(resultBufferSize)]
    
    coeff = computeCoeffcients(opts)
    
    outputs = []
    for inputStart in range(len(a))[::opts.paraInputs]:
    
        inputs = a[inputStart:inputStart+opts.paraInputs]
        
        for i in range(len(inputs)):
            for j in range(len(coeff)):
                resultBuffer[i+j] += coeff[j]*inputs[i]
                
        if opts.debugOut:
            print "Result buffer @",inputStart,":",dataToStr(resultBuffer)
        
        for i in range(opts.paraInputs):
            outputs.append(resultBuffer[i])
            
        for i in range(resultBufferSize - opts.paraInputs):
            resultBuffer[i] = resultBuffer[i+opts.paraInputs]
            
        for i in range(resultBufferSize - opts.paraInputs, resultBufferSize):
            resultBuffer[i] = 0.0 
            

    result = outputs[numIncompleteResults:numIncompleteResults+numOutputValues]
    print "1", dataToStr(result)
    return result

def main():
    opts, args = parseArgs()
    
    random.seed(15)
    indata = []
    while len(indata) < opts.inputSize:
        testVal = random.randint(1,opts.inputSize)
        if testVal not in indata:
            indata.append(testVal)
    
    paddedData = [0.0 for a in range(opts.width*opts.depth)]+[i for i in indata]+[0.0 for a in range(opts.width*opts.depth)]
    naive = computeNaive(paddedData, opts)
    scheme = computeOurScheme(indata, opts)
    
    print
    assert len(naive) == len(scheme)
    for i in range(len(naive)):
        assert eToStr(naive[i]) == eToStr(scheme[i]), "Item "+str(i)+" is not equal"
    print "Compute methods are equivalent"
        

if __name__ == '__main__':
    main()

