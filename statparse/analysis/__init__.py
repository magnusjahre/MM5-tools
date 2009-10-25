
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