'''
Created on Dec 7, 2009

@author: jahre
'''
from statparse.analysis import computeMean, computeMedian
from statparse.analysis import computeRMS
from statparse.analysis import computeStddev
from statparse.printResults import printData
from statparse.printResults import numberToString
from statparse.plotResults import plotRawBoxPlot
import sys
import math

statNames = ["mean", "rms", "stdev", "median"]

def checkStatName(name):
    if name in statNames:
        return True
    return False
         
def getStatnameMessage():
    retstr = "Available statistics are: "+statNames[0]
    for s in statNames[1:]:
        retstr += ", "+s
    return retstr

def getTitleLine(relative):
    if relative:
        return ["Relative-Mean-Error-(%)", "Relative-Median-Error-(%)", "Relative-RMS-Error-(%)", "Relative-Standard-Deviation-(%)"]
    return  ["Mean-Error", "Median-Error", "RMS-Error", "Standard-Deviation"]

def getJustifyArray(printAvgVals):
    if printAvgVals:
        return [True, False, False, False, False, False]
    return [True, False, False, False, False]

""" Prints a error dictionary

    errors: key string -> ErrorStatistics object
"""
def printErrorStatDict(errors, relative, decimals, sortedkeys = None, outfile = sys.stdout):
    lines = []
    header = [""]
    for t in getTitleLine(relative):
        header.append(t)
    
    lines.append(header)
    
    if sortedkeys == None:
        keys = errors.keys()
        keys.sort()
    else:
        keys = sortedkeys
    
    for k in keys:
        mean, rms, stdev, median = errors[k].getStats()
        thisLine = [str(k)]
        
        thisLine.append(numberToString(mean, decimals))
        thisLine.append(numberToString(median, decimals))
        thisLine.append(numberToString(rms, decimals))
        thisLine.append(numberToString(stdev, decimals))
        lines.append(thisLine)
        
    printData(lines, getJustifyArray(False), outfile, decimals)

""" Prints error dictionary with parameters

    errors: key string -> parameter string --> ErrorStatistics object
    sortedParamKeys: list of strings with the order the parameters should appear in
    statistic: a string describing the statistic to print
"""
def printParamErrorStatDict(errors, sortedParamKeys, statistic, relative, decimals, outfile = sys.stdout):
    
    header = [""]
    justify = [True]
    for p in sortedParamKeys:
        header.append(p)
        justify.append(False)
    
    lines = [header]
    
    mainkeys = errors.keys()
    mainkeys.sort()
    
    for key in mainkeys:
        thisLine = [key]
        for p in sortedParamKeys:
            if p in errors[key]:
                thisLine.append(numberToString(errors[key][p].getStatByName(statistic), decimals))
            else:
                thisLine.append("N/A")
        lines.append(thisLine)
    
    printData(lines, justify, outfile, decimals)
    
""" Prints error dictionary with parameters but sorts each data data set to create a sorted value distribution

    errors: key string -> parameter string --> ErrorStatistics object
    sortedParamKeys: list of strings with the order the parameters should appear in
    statistic: a string describing the statistic to print
"""
def printParamErrorStatDistribution(errors, sortedParamKeys, statistic, relative, decimals, outfile = sys.stdout):
    header = [""]
    justify = [True]
    for p in sortedParamKeys:
        header.append(p)
        justify.append(False)
    
    lines = [header]
    
    mainkeys = errors.keys()
    mainkeys.sort()
    
    data = {}
    for k in mainkeys:
        for p in sortedParamKeys:
            if p not in data:
                data[p] = []
            if p in errors[k]:
                data[p].append(errors[k][p].getStatByName(statistic))
            else:
                data[p].append("N/A")
    
    for p in sortedParamKeys:
        data[p].sort()
        
    for i in range(len(mainkeys)):
        line = [str(i+1)]
        for p in sortedParamKeys:
            line.append(numberToString(data[p][i], decimals))
        lines.append(line)
    
    printData(lines, justify, outfile, decimals)    


""" Plots a box and whiskers plot based on data from a dictionary 

    results, dictionary - experimentKey -> parameterKey -> ErrorStatistics object
    hideOutliers, bool 
    title, list of strings - the sorted parameter titles
"""
def plotBoxFromDict(results, hideOutliers, titles):
    allErrors = {}
    for expkey in results:
        for paramkey in results[expkey]:
            if paramkey not in allErrors:
                allErrors[paramkey] = []
            for errVal in results[expkey][paramkey].getAllErrors():
                allErrors[paramkey].append(errVal)
    
    allErrorLists = []
    for t in titles:
        allErrorLists.append(allErrors[t])
    
    plotRawBoxPlot(allErrorLists, hideOutliers=hideOutliers, titles=titles)

def dumpAllErrors(results, filename):
    outfile = open(filename, "w")
    
    for expkey in results:
        for paramkey in results[expkey]:
            for errval in results[expkey][paramkey].getAllErrors():
                outfile.write(str(errval)+" ")
    
    outfile.flush()
    outfile.close()

class ErrorStatistics():


    def __init__(self, relative):
        self.errsum = 0
        self.errsqsum = 0
        self.numerrs = 0
        
        self.valsum = 0
        self.baselinesum = 0
        
        self.relative = relative
        self.allErrors = []
        
    def sample(self, estimate, actual, baseline = -1):
        
        self.valsum += estimate
        self.baselinesum += actual
        
        error = estimate - actual
        if self.relative:
            try:
                if baseline == -1:
                    tmperr = (float(error) / float(actual)) * 100
                else:
                    tmperr = (float(error) / float(baseline)) * 100
            except ZeroDivisionError:
                tmperr = 0
        else:
            assert baseline == -1
            try:
                tmperr = (math.fabs(error) / math.fabs(actual)) * 100
            except ZeroDivisionError:
                tmperr = 0
        
        self.errsum += tmperr
        self.errsqsum += tmperr*tmperr
        self.numerrs += 1
        
        self.allErrors.append(tmperr)
    
    
    def getStatByName(self, name):
        
        if name not in statNames:
            raise Exception("Unknown statistic name "+str(name))
        
        mean,rms,stdev,median = self.getStats()
        if name == "mean":
            return mean
        if name == "rms":
            return rms
        if name == "median":
            return median
        
        assert name == "stdev"
        return stdev
    
    def getStats(self):
        mean = computeMean(self.numerrs, self.errsum)
        rms = computeRMS(self.numerrs, self.errsqsum)
        stdev = computeStddev(self.numerrs, self.errsum, self.errsqsum)
        median = computeMedian(self.allErrors)
        return mean, rms, stdev, median
    
    def getValues(self):
        valmean = computeMean(self.numerrs, self.valsum)
        baselinemean = computeMean(self.numerrs, self.baselinesum)
        return valmean, baselinemean
    
    def getAllErrors(self):
        return self.allErrors
    
    def __str__(self):
        return self.toString(2)
        
    def toString(self, decimals):
        
        mean, rms, stddev, median = self.getStats()
        
        if self.relative:
            prefix = "Relative "
            post = " %\n"
        else:
            prefix = ""
            post = "\n"
        
        retstr = ""
        retstr += prefix+"Mean Error:        "+(("%."+str(decimals)+"f") % mean).rjust(5+decimals)+post
        retstr += prefix+"RMS Error:         "+(("%."+str(decimals)+"f") % rms).rjust(5+decimals)+post
        retstr += prefix+"Standard Deviation:"+(("%."+str(decimals)+"f") % stddev).rjust(5+decimals)+post
        retstr += prefix+"Median:            "+(("%."+str(decimals)+"f") % median).rjust(5+decimals)+post
        return retstr
    
    def aggregate(self, addErrors):
        self.errsum += addErrors.errsum
        self.errsqsum += addErrors.errsqsum
        self.numerrs += addErrors.numerrs  
        self.allErrors = self.allErrors + addErrors.allErrors
        