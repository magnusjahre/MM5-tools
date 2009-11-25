'''
Created on Nov 19, 2009

@author: jahre
'''

from statparse.tracefile import isInt
from statparse.tracefile import isFloat

import statparse.plotResults as plotResults

__metaclass__ = type

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
        
        print "Tracefile contains the following column to header mapping:"
        for c in cols:
            print str(c)+": "+str(self.headers[c])
    
    def _parseColumnSpec(self, colSpec):
        
        errMessage = "Y-col spec can be a comma separated list of integers (1,2,3), a range (1-5) or a single number (1)"
        
        newColSpec = []
        if "," in colSpec:
            splitted = colSpec.split(",")
            for sp in splitted:
                try:
                    newColSpec.append(int(sp))
                except:
                    raise Exception(errMessage)
        elif "-" in colSpec:
            splitted = colSpec.split("-")
            if len(splitted) != 2:
                raise Exception(errMessage)
            try:
                newColSpec = range(int(splitted[0]), int(splitted[1])+1)
            except:
                raise Exception(errMessage)
        else:
            try:
                newColSpec.append(int(colSpec))
            except:
                raise Exception(errMessage)
        
        return newColSpec
    
    def plot(self, xCol, yCols, filename = ""):
        try:
            xColID = int(xCol)
        except:
            raise Exception("X Column ID must be an integer") 
        
        yColIDs = self._parseColumnSpec(yCols)
        
        xvalues = self.data[xColID]
        yvalues = []
        legendTitles = []
        for c in yColIDs:
            yvalues.append(self.data[c])
            legendTitles.append(self.headers[c])
        
        if filename == "":
            plotResults.plotLines(xvalues, yvalues, legendTitles=legendTitles)
        else:
            plotResults.plotLines(xvalues, yvalues, legendTitles=legendTitles, filename=filename)
        