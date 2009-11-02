
from math import sqrt

def computeStddev(n, sum, sumsq):
    assert n > 1
    
    n = float(n)
    sumsq = float(sumsq)
    sum = float(sum)
    return  sqrt( max(((n * sumsq) - sum * sum) / (n * (n-1)), 0) )

def computeMean(n, sum):
    n = float(n)
    sum = float(sum)
    return sum / n

def computeRMS(n, sumsq):
    meanSquare = computeMean(n, sumsq)
    return sqrt(max(meanSquare ,0))

def computeDistributionAverage(distribution):
    
    samples = distribution["samples"]
    wsum = 0
    
    for key in distribution:
        if key == "min_value" or key == "max_value" or key == "samples":
            continue
        wsum += key * distribution[key]
        
    return float(wsum) / float(samples)
    