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

def getStaticCoefficient(width):
    return 1.0/(width*2+1)

def stencil(a, i, width):
    start = i-width
    if start < 0:
        start = 0
    end = i+width+1
    if end > len(a):
        end = len(a)
    
    s = 0
    for i in range(start, end):
        s += a[i]
        
    return getStaticCoefficient(width)*s

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
            b[i] = stencil(a, i, opts.width)
        print n+1,dataToStr(b)[printSegment:-printSegment]
        for i in range(len(a)):
            a[i] = b[i]
    
    return a[printSegment:-printSegment]

def computeCoeffcients(opts):
    # Note: procedure assumes symetric stencil
    numAffectedResults = 2 * opts.width*opts.depth + 1
    centerIndex = opts.width*opts.depth
    repeats = []
    
    curRepeat = 1
    for i in range(numAffectedResults):
        repeats.append(curRepeat)
        if i < centerIndex:
            curRepeat += 1
        else:
            curRepeat -= 1
    
    assert repeats[centerIndex] == 2*opts.width + 1
    coeffs = [(getStaticCoefficient(opts.width)**opts.depth)*r for r in repeats]
    
    return coeffs

def computeOurScheme(indata, opts):
    
    print
    print "The scheme with depth", opts.depth
    print

    resultBufferSize = 2 * opts.width*opts.depth + opts.paraInputs
    numIncompleteResults = 2*opts.width
    
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
        
        for i in range(opts.paraInputs):
            outputs.append(resultBuffer[i])
            
        for i in range(resultBufferSize - opts.paraInputs):
            resultBuffer[i] = resultBuffer[i+opts.paraInputs]
            
        for i in range(resultBufferSize - opts.paraInputs, resultBufferSize):
            resultBuffer[i] = 0.0 

    result = outputs[numIncompleteResults:]
    print "1", dataToStr(result)
    return result

def main():
    opts, args = parseArgs()
    
    random.seed(15)
    indata = [random.randint(1,9) for i in range(opts.inputSize)]
    
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

