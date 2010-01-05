'''
Created on Dec 7, 2009

@author: jahre
'''
from statparse.analysis import computeMean
from statparse.analysis import computeRMS
from statparse.analysis import computeStddev
from statparse.printResults import printData
from statparse.printResults import numberToString
from statparse.plotResults import plotRawBoxPlot
import sys

def getTitleLine(relative):
    if relative:
        return ["Relative Mean Error (%)", "Relative RMS Error (%)", "Relative Standard Deviation (%)"]
    return  ["Mean Error", "RMS Error", "Standard Deviation"]

def getJustifyArray(printAvgVals):
    if printAvgVals:
        return [True, False, False, False, False, False]
    return [True, False, False, False]

""" Prints a error dictionary

    errors: key string -> ErrorStatistics object
"""
def printErrorStatDict(errors, relative, decimals, printAvgValues):
    lines = []
    header = [""]
    if printAvgValues:
        header.append("Average Value")
        header.append("Average Baseline Value")
    for t in getTitleLine(relative):
        header.append(t)
    
    lines.append(header)
    
    keys = errors.keys()
    keys.sort()
    
    for k in keys:
        mean, rms, stdev = errors[k].getStats()
        thisLine = [str(k)]
        if printAvgValues:
            val, baseline = errors[k].getValues()
            thisLine.append(numberToString(val, decimals))
            thisLine.append(numberToString(baseline, decimals))
        
        thisLine.append(numberToString(mean, decimals))
        thisLine.append(numberToString(rms, decimals))
        thisLine.append(numberToString(stdev, decimals))
        lines.append(thisLine)
        
    printData(lines, getJustifyArray(printAvgValues), sys.stdout, decimals)

""" Plots a box and whiskers plot based on data from a dictionary of ErrorStatistics
    objects
"""
def plotBoxFromDict(results, hideOutliers, title):
    allErrors = []
    for key in results:
        for errVal in results[key].getAllErrors():
            allErrors.append(errVal)
    
    plotRawBoxPlot([allErrors], hideOutliers=hideOutliers, titles=[title])

class ErrorStatistics():


    def __init__(self, relative):
        self.errsum = 0
        self.errsqsum = 0
        self.numerrs = 0
        
        self.valsum = 0
        self.baselinesum = 0
        
        self.relative = relative
        self.allErrors = []
        
    def sample(self, value, baseline):
        
        self.valsum += value
        self.baselinesum += baseline
        
        error = value - baseline
        if self.relative:
            try:
                tmperr = (float(error) / float(baseline)) * 100
            except ZeroDivisionError:
                tmperr = 0
        else:
            tmperr = float(error)
        
        self.errsum += tmperr
        self.errsqsum += tmperr*tmperr
        self.numerrs += 1
        
        self.allErrors.append(tmperr)
    
    def getStats(self):
        mean = computeMean(self.numerrs, self.errsum)
        rms = computeRMS(self.numerrs, self.errsqsum)
        stdev = computeStddev(self.numerrs, self.errsum, self.errsqsum)
        return mean, rms, stdev
    
    def getValues(self):
        valmean = computeMean(self.numerrs, self.valsum)
        baselinemean = computeMean(self.numerrs, self.baselinesum)
        return valmean, baselinemean
    
    def getAllErrors(self):
        return self.allErrors
    
    def __str__(self):
        return self.toString(2)
        
    def toString(self, decimals):
        
        mean, rms, stddev = self.getStats()
        
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
        return retstr
    
    def aggregate(self, addErrors):
        self.errsum += addErrors.errsum
        self.errsqsum += addErrors.errsqsum
        self.numerrs += addErrors.numerrs        
        