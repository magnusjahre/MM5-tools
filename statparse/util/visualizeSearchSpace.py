#!/usr/bin/env python

from optparse import OptionParser
from statparse.util import fatal
import os

import statparse.plotResults as plotResults

def parseArgs():
    parser = OptionParser(usage="visualizeSearchSpace.py [options] FILENAME")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--xrange", action="store", dest="xrange", type="string", default="", help="X-range to use")
    parser.add_option("--yrange", action="store", dest="yrange", type="string", default="", help="Y-range to use")

    opts, args = parser.parse_args()
    
    if len(args) != 1:
        fatal("Command line error, need filename as argument")
    
    return opts,args

def main():

    opts,args = parseArgs()

    if not os.path.exists(args[0]):
        fatal("File "+args[0]+" not found")
    
    data = []
    
    for line in open(args[0]):
        splitted = line.strip().split(";")
        assert len(splitted) == 5
        
        mshrs1 = int(splitted[0])
        mshrs2 = int(splitted[1])
        mshrs3 = int(splitted[2])
        mshrs4 = int(splitted[3])
        
        value = float(splitted[4])
        
        data.append(([mshrs1,mshrs2, mshrs3, mshrs4], value) )

    matrix = {}

    fixedDims = [True for i in range(4)]
    for mha, value in data:
        for i in range(len(mha)):
            if mha[i] != 16:
                fixedDims[i] = False


    variableCnt = 0
    freeDimIDList = []
    tmpcnt = 0
    for f in fixedDims:
        if not f:
            variableCnt += 1
            freeDimIDList.append(tmpcnt)
        tmpcnt += 1

    if variableCnt == 1:
        fatal("one dim plotting not impl")
    elif variableCnt == 2:
        
        picture = [ [0 for j in range(17)] for i in range(17)]
        for mha, value in data:
            xval = mha[freeDimIDList[0]]
            yval = mha[freeDimIDList[1]]
            picture[xval][yval] = value
        
        if opts.xrange != "":
            xrange=opts.xrange
        else:
            xrange="1,16"
        
        if opts.yrange != "":
            yrange=opts.yrange
        else:
            yrange="1,16"
        
        plotResults.plotImage(picture,
                              xrange=xrange,
                              yrange=yrange,
                              xlabel="MSHRs CPU "+str(freeDimIDList[1]),
                              ylabel="MSHRs CPU "+str(freeDimIDList[0]))
        
    else:
        for mha, value in data:
            
            xpair = (mha[0],mha[1])
            ypair = (mha[2],mha[3])
            
            if xpair not in matrix:
                matrix[xpair] = {}
            
            assert ypair not in matrix[xpair]
            matrix[xpair][ypair] = value
        
        xkeys = matrix.keys()
        xkeys.sort()
        ykeys = matrix[xkeys[0]].keys()
        ykeys.sort()
        
        picture = [ [0 for j in range(16*16)] for i in range(16*16)]
        for i in range(len(xkeys)):
            for j in range(len(ykeys)):
                picture[i][j] = matrix[xkeys[i]][ykeys[j]]
    
        plotResults.plotImage(picture,
                              xrange=opts.xrange,
                              yrange=opts.yrange,
                              xlabel="MSHRs CPU 2 and 3",
                              ylabel="MSHRs CPU 0 and 1")

if __name__ == '__main__':
    main()