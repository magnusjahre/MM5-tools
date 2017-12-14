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

class Coefficients:
    
    def __init__(self, opts):
        self.noCoeff = opts.noCoeff
        self.width = opts.width
        
        if opts.noCoeff:
            self.coeffs = [1.0 for i in range(2*opts.width+1)]
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

def stencil(a, i, opts, coeffs):
    start = i-opts.width
    if start < 0:
        start = 0
    end = i+opts.width+1
    if end > len(a):
        end = len(a)
    
    s = 0
    for i in range(start, end):
        s += coeffs.getSingle(i-start)*a[i]
        
    return s

def computeNaive(indata, coefficients, opts):
    print
    print "=====","Naive implementation with "+str(2*opts.width+1)+" point stencil","====="
    print
    
    printSegment = opts.width*opts.depth
    
    a = [a for a in indata]
    b = [0.0 for i in range(len(a))]
    print "Input: ", dataToStr(a)[printSegment:-printSegment]
    
    for n in range(opts.depth):
        for i in range(len(a))[opts.width:-opts.width]:
            b[i] = stencil(a, i, opts, coefficients)
        print n+1,dataToStr(b)[printSegment:-printSegment]
        for i in range(len(a)):
            a[i] = b[i]
    
    return a[printSegment:-printSegment]

def createRepeatPattern(repeats, doAdd, opts):
    padval = 1.0
    if doAdd:
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
            if doAdd:
                newRepeats[j] += shiftedRepeats[i][j]
            else:
                newRepeats[j] *= shiftedRepeats[i][j]
                
    return newRepeats

def computeRepeats(repeats, affectedResults, doAdd, opts):
    # Handles depth equal to 1
    if len(repeats) == affectedResults:
        return repeats
    
    repeats = createRepeatPattern(repeats, doAdd, opts)
    if opts.debugOut:
        print "-- Repeat pattern at length "+str(len(repeats))+" is "+str(dataToStr(repeats))
    
    if len(repeats) < affectedResults:
        repeats = computeRepeats(repeats, affectedResults, doAdd, opts) 
    return repeats

def computeCoeffcients(coeffObj, opts):
    # Note: procedure assumes symetric stencil
    numAffectedResults = 2 * opts.width*opts.depth + 1
    stencilWidth = 2*opts.width+1
    
    if opts.debugOut:
        print
        print "Computing coefficients for stencil width", str(stencilWidth),"and affected results",numAffectedResults
    
    repeats = computeRepeats([1 for i in range(stencilWidth)], numAffectedResults, True, opts)
    if opts.debugOut:
        print "Repeats:", str(repeats)
    
    coeffs = computeRepeats(coeffObj.getAll(), numAffectedResults, False, opts)
    if opts.debugOut:
        print "Coefficients:", dataToStr(coeffs)
    
    multipliers = [coeffs[i]*repeats[i] for i in range(len(repeats))]
    
    if opts.debugOut:
        print "Multipliers:", dataToStr(multipliers)
    
    return multipliers

def computeOurScheme(indata, coefficients,opts):
    
    print
    print "=====","The scheme with depth", opts.depth,"====="
    
    resultBufferSize = 2 * opts.width*opts.depth + opts.paraInputs
    numIncompleteResults = opts.depth*opts.width
    assert numIncompleteResults > 0
    numOutputValues = len(indata)
    print "Input: ", dataToStr(indata)
    
    # End-padding is a hack ensure that the impact of the final elements propagate to the output
    a = [a for a in indata] + [0.0 for x in range(numIncompleteResults)]
    resultBuffer = [0 for i in range(resultBufferSize)]
    
    coeff = computeCoeffcients(coefficients, opts)
    
    print
    print "Performing stencil computation:"
    
    outputs = []
    for inputStart in range(len(a))[::opts.paraInputs]:
    
        inputs = a[inputStart:inputStart+opts.paraInputs]
        
        for i in range(len(inputs)):
            for j in range(len(coeff)):
                resultBuffer[i+j] += coeff[j]*inputs[i]
                
        if opts.debugOut:
            print "-- Result buffer @",inputStart,":",dataToStr(resultBuffer)
        
        for i in range(opts.paraInputs):
            outputs.append(resultBuffer[i])
            
        for i in range(resultBufferSize - opts.paraInputs):
            resultBuffer[i] = resultBuffer[i+opts.paraInputs]
            
        for i in range(resultBufferSize - opts.paraInputs, resultBufferSize):
            resultBuffer[i] = 0.0 
            

    result = outputs[numIncompleteResults:numIncompleteResults+numOutputValues]
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

def main():
    opts, args = parseArgs()
    
    print
    print "Stencil computing test program"
    
    indata = createRandomVector(opts.inputSize)
    paddedData = [0.0 for a in range(opts.width*opts.depth)]+[i for i in indata]+[0.0 for a in range(opts.width*opts.depth)]
    
    coefficients = Coefficients(opts)
    
    print "Using stencil coefficients: "+str(dataToStr(coefficients.getAll()))
    
    naive = computeNaive(paddedData, coefficients, opts)
    scheme = computeOurScheme(indata, coefficients, opts)
    
    print
    assert len(naive) == len(scheme)
    for i in range(len(naive)):
        assert eToStr(naive[i]) == eToStr(scheme[i]), "Item "+str(i)+" is not equal"
    print "Compute methods are equivalent"
        

if __name__ == '__main__':
    main()

