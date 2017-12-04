#!/usr/bin/env python

import sys
import random
from optparse import OptionParser

def parseArgs():
    
    parser = OptionParser(usage="stencil.py [options]")
    parser.add_option("--verbose", '-v', action="store_true", dest="verbose", default=False, help="Print all lines")
    parser.add_option("--stencil-width", action="store", dest="width", default=1, help="The width of the one-dimensional symmetric stencil")
    parser.add_option("--depth", action="store", dest="depth", default=2, help="The number of iterations to compute in a single push")
    parser.add_option("--input-size", action="store", dest="inputSize", default=10, help="Size of the unpadded input array")
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

def stencil(a, i, width):
    start = i-width
    end = i+width+1
    
    s = 0
    for i in range(start, end):
        s += a[i]
    
    return (1.0/(width*2+1))*s

def computeNaive(indata, opts):
    print "Naive implementation"
    print
    
    a = [0.0] + [i for i in indata] + [0.0]
    b = [0.0 for i in range(len(a))]
    print "0", dataToStr(a)
    
    for n in range(opts.depth):
        for i in range(len(a))[opts.width:-opts.width]:
            b[i] = stencil(a, i, opts.width)
        print n+1,dataToStr(b)
        for i in range(len(a)):
            a[i] = b[i]
    
    return a

def computeOurScheme(indata, opts):
    
    print
    print "The scheme with depth", opts.depth
    print
    
    padSize = 1
    iterations = 3
    
    a = [0.0] + [i for i in indata] + [0.0]
    b = [0.0 for i in range(len(a))]
    partials = [0 for i in range(3)]
    
    print "0", dataToStr(a)
    
    first = True
    startIndex = iterations-padSize
    
    for i in range(len(a))[startIndex:]:
        
        if first:
            for j in range(len(partials)):
                center = i-startIndex+j
                if center < padSize:
                    partials[j] = 0
                else:
                    partials[j] = stencil(a, center, opts.width)
                #b[i-1] = stencil(partials, 1)
            first = False
        else:
            if i < len(a)-1:
                partials[-1] = stencil(a, i, opts.width)
        
        b[i-1] = stencil(partials, 1, opts.width)
        # print i, "computed", eToStr(b[i]),"with partials", dataToStr(partials)
    
        partials = [partials[j+1] for j in range(len(partials))[:-1]]
        partials.append(0.0)
    
    print "1", dataToStr(b)
    
    return b

def main():
    opts, args = parseArgs()
    
    random.seed(15)
    indata = [random.randint(1,9) for i in range(opts.inputSize)]
    
    naive = computeNaive(indata, opts)
    scheme = computeOurScheme(indata, opts)
    
    print
    assert len(naive) == len(scheme)
    for i in range(len(naive)):
        assert naive[i] == scheme[i], "Item "+str(i)+" is not equal"
    print "Compute methods are equivalent"
        

if __name__ == '__main__':
    main()

