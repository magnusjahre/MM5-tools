'''
Created on Dec 7, 2009

@author: jahre
'''
from statparse.analysis import computeMean
from statparse.analysis import computeRMS
from statparse.analysis import computeStddev
from statparse.printResults import printData
from statparse.printResults import numberToString
import sys

def getTitleLine(relative):
    if relative:
        return ["", "Relative Mean Error (%)", "Relative RMS Error (%)", "Relative Standard Deviation (%)"]
    return  ["", "Mean Error", "RMS Error", "Standard Deviation"]

def getJustifyArray():
    return [True, False, False, False]

""" Prints a error dictionary

    errors: key string -> ErrorStatistics object
"""
def printErrorStatDict(errors, relative, decimals):
    lines = []
    lines.append(getTitleLine(relative))
    
    keys = errors.keys()
    keys.sort()
    
    for k in keys:
        mean, rms, stdev = errors[k].getStats()
        thisLine = [str(k),
                    numberToString(mean, decimals),
                    numberToString(rms, decimals),
                    numberToString(stdev, decimals)]
        lines.append(thisLine)
        
    printData(lines, getJustifyArray(), sys.stdout, decimals)
        

class ErrorStatistics():


    def __init__(self, relative):
        self.errsum = 0
        self.errsqsum = 0
        self.numerrs = 0
        
        self.relative = relative
        
    def sample(self, error, baseline):
        if self.relative:
            tmperr = (float(error) / float(baseline)) * 100
        else:
            tmperr = float(error)
        
        self.errsum += tmperr
        self.errsqsum += tmperr*tmperr
        self.numerrs += 1
    
    def getStats(self):
        mean = computeMean(self.numerrs, self.errsum)
        rms = computeRMS(self.numerrs, self.errsqsum)
        stdev = computeStddev(self.numerrs, self.errsum, self.errsqsum)
        return mean, rms, stdev
    
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