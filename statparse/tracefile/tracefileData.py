'''
Created on Nov 19, 2009

@author: jahre
'''

from statparse.tracefile import isInt
from statparse.tracefile import isFloat

import statparse.plotResults as plotResults
from statparse.util import warn
import math

__metaclass__ = type

def parseColumnSpec(colSpec):
    
    errMessage = "Y-col spec can be a comma separated list of integers (1,2,3), a range (1-5) or a single number (1). All numbers may be preceeded with a file ID number (1:1, 2:4)"
    
    newColSpec = []
    if "," in colSpec:
        splitted = colSpec.split(",")
        for sp in splitted:
            fileID = 0
            if ":" in sp:
                try:
                    fileIDStr,colIDStr = sp.split(":")
                    fileID = int(fileIDStr)
                    colID = int(colIDStr)
                except:
                    raise Exception(errMessage)
            else:
                try:
                    colID = int(sp)
                except:
                    raise Exception(errMessage)
            newColSpec.append( (fileID,colID) )
            
    elif "-" in colSpec:
        fileID = 0
        if ":" in colSpec:
            try:
                fileIDStr, rangeSpec = colSpec.split(":")
                fileID = int(fileID)
            except:
                raise Exception(errMessage)
        else:
            rangeSpec = colSpec
        
        splitted = rangeSpec.split("-")
        if len(splitted) != 2:
            raise Exception(errMessage)
        try:
            colRange = range(int(splitted[0]), int(splitted[1])+1)
        except:
            raise Exception(errMessage)
        
        for val in colRange:
            newColSpec.append( (fileID, val) )
        
    else:
        fileID = 0
        if ":" in colSpec:
            try:
                fileIDStr, colIDStr = colSpec.split(":")
                fileID = int(fileID)
                colID = int(colID)
            except:
                raise Exception(errMessage)
        
        else:
            try:
                colID = int(colSpec)
            except:
                raise Exception(errMessage)
            
        newColSpec.append( (fileID, colID) )
    
    return newColSpec

def plot(tracefiles, xCol, yCols, **kwargs):
        
        filename = ""
        xrange = ""
        if "filename" in kwargs:
            filename = kwargs["filename"]
        if "xrange" in kwargs:
            xrange = kwargs["xrange"]
        if "yrange" in kwargs:
            yrange = kwargs["yrange"]
        
        
        xColSpec = parseColumnSpec(xCol)        
        yColSpec = parseColumnSpec(yCols)
        
        if len(xColSpec) != len(tracefiles):
            raise Exception("We need one x column from each trace to unify traces")
        
        try:
            xColValues = [tracefiles[xFileID].data[xColID] for xFileID, xColID in xColSpec]
        except:
            raise Exception("X file id or x column id out of range") 
        
        yvalues = []
        xvalues = []
        legendTitles = []
        for yFileID, yColID in yColSpec:
            try:
                yvalues.append(tracefiles[yFileID].data[yColID])
            except:
                raise Exception("Y file id or y column id out of range")     
            xvalues.append(xColValues[yFileID])
            legendTitles.append(tracefiles[yFileID].headers[yColID])
            
        plotResults.plotLines(xvalues, yvalues, legendTitles=legendTitles, filename=filename, xrange=xrange, yrange=yrange)

def findLowestEndpoint(value, sortedList):
    min = 0
    max = len(sortedList)
    mid = (min + max) / 2
    
    while min < max:
        mid = (min + max) / 2
                
        if value > sortedList[mid]:
            min = mid + 1
        else:
            max = mid - 1
        
    if min == len(sortedList):
        min = min-1
        assert value >= sortedList[min]
        return min
      
    if sortedList[min] > value: 
        min = min-1    
    
    
    if min >= 0: 
        assert sortedList[min] <= value
    if min+1 < len(sortedList):
        assert sortedList[min+1] >= value
    return min

def interpolate(findX, lowestIndex, xvalues, yvalues):
    assert len(xvalues) == len(yvalues)
    
    if lowestIndex == len(yvalues)-1:
        return yvalues[lowestIndex]
    
    if lowestIndex == -1:
        return yvalues[0]
    
    ydiff =  yvalues[lowestIndex+1] - yvalues[lowestIndex]
    xdiff =  xvalues[lowestIndex+1] - xvalues[lowestIndex]
    
    findXDiff = findX - xvalues[lowestIndex]
    
    if xdiff == 0:
        interpolY = yvalues[lowestIndex]
    else:
        interpolY = yvalues[lowestIndex] + findXDiff * (ydiff / xdiff)
    
    return interpolY 

def computeInterpolatedErrors(mainTrace,
                              mainXColumnID,
                              mainYColumnID,
                              interpolateTrace,
                              interpolateXColumnID,
                              interpolateYColumnID,
                              relative,
                              doNotWarn):

    assert len(mainTrace.data[mainXColumnID]) == len(mainTrace.data[mainYColumnID])

    errsum = 0
    errsqsum = 0
    numerrs = 0

    for i in range(len(mainTrace.data[mainXColumnID])):
        
        mainXval = mainTrace.data[mainXColumnID][i]
        
        interX1 = findLowestEndpoint(mainXval, interpolateTrace.data[interpolateXColumnID])
        intervalue = interpolate(mainXval,
                                 interX1,
                                 interpolateTrace.data[interpolateXColumnID],
                                 interpolateTrace.data[interpolateYColumnID])
        
        if math.isnan(intervalue):
            if not doNotWarn:
                warn("Value is NaN, skipping")
            continue
        
        error = mainTrace.data[mainYColumnID][i] - intervalue
        
        if relative:
            assert mainTrace.data[mainYColumnID][i] != 0
            error = error / mainTrace.data[mainYColumnID][i]
            error = error * 100
        
        errsum += error
        errsqsum += error*error
        numerrs += 1
            
    return errsum, errsqsum, numerrs

class TracefileData():

    def __init__(self, filename, separator = ";"):
        self.filename = filename
        self.headers = {}
        self.data = {}
        self.separator = separator
        
    def readTracefile(self):
        tracefile = open(self.filename)
        
        header = tracefile.readline()
        
        colID = 0
        for h in header.strip().split(self.separator):
            self.headers[colID] = h
            self.data[colID] = []
            colID += 1
            
        for line in tracefile:
            
            dataline = line.strip().split(self.separator)
            
            colID = 0
            for value in dataline:
                if isFloat(value):
                    storeval = float(value)
                elif isInt(value):
                    storeval = int(value)
                else:
                    raise Exception("Trace value must be integer or float")
                
                self.data[colID].append(storeval)
                colID += 1
         
        tracefile.close()
        
    def printColumnMapping(self):
        cols = self.headers.keys()
        cols.sort()
        
        for c in cols:
            print str(c)+": "+str(self.headers[c])

        