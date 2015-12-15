
from math import sqrt
from numpy import median

def computeStddev(n, insum, sumsq):
    if n <= 1:
        return 0
    
    n = float(n)
    sumsq = float(sumsq)
    insum = float(insum)
    return  sqrt( max(((n * sumsq) - insum * insum) / (n * (n-1)), 0) )

def computeMean(n, insum):
    if n == 0:
        return 0
    
    n = float(n)
    insum = float(insum)
    return insum / n

def computeRMS(n, sumsq):
    meanSquare = computeMean(n, sumsq)
    return sqrt(max(meanSquare ,0))

def computeMedian(values):
    if values == []:
        return 0
    return float(median(values))

def computeDistributionAverage(distribution):
    
    samples = distribution["samples"]
    wsum = 0
    
    for key in distribution:
        if key == "min_value" or key == "max_value" or key == "samples":
            continue
        wsum += key * distribution[key]
        
    return float(wsum) / float(samples)
    
def computePercError(estimate, actual):
    err = (float(estimate) - float(actual)) / float(actual)
    return err*100