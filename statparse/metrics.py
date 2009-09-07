
__metaclass__ = type

metrics = {"hmos": "Harmonic Mean of Speedups",
           "fairness": "Fairness",
           "stp": "System Throughput",
           "hmean": "Harmonic Mean",
           "amean": "Arithmetic Mean",
           "sum": "Sum"}

def printPossibleMetrics():
    print
    print "The following metrics are supported:"
    mkeys = metrics.keys()
    mkeys.sort() 
    for m in mkeys:
        print m.ljust(10)+metrics[m]

def createMetric(name):
    if name.lower() == "hmean":
        return HarmonicMean()
    elif name.lower() == "hmos":
        return HarmonicMeanOfSpeedups()
    elif name.lower() == "amean":
        return ArithmeticMean()
    elif name.lower() == "fairness":
        return Fairness()
    elif name.lower() == "stp": 
        return SystemThroughput()
    elif name.lower() == "sum":
        return Sum()
    
    raise Exception("Unknown metric "+name)

class WorkloadMetric():

    def __init__(self):
        self.n = 0
        self.speedups = []
        self.spmNeeded = False

    def setValues(self, multiprogramValues, singleProgramValues = None):
        
        self.n = len(multiprogramValues)
        
        if singleProgramValues == None:
            singleProgramValues = [1 for i in range(self.n)]
            
            if self.spmNeeded:
                raise Exception("Single program mode results needed by metric but not provided")
        
        if len(multiprogramValues) != len(singleProgramValues):
            raise Exception("single program and multiprogram results must be the same lenght") 
    
        self.speedups = [1 for i in range(self.n)]
        for i in range(len(multiprogramValues)):
            self.speedups[i] = float(multiprogramValues[i]) / float(singleProgramValues[i])
    
    
    def computeMetricValue(self):
        raise Exception("compute metric should only be called on subclasses")
    
    def computeSum(self):
        res = 0.0
        for v in self.speedups:
            res += v
        return res
    
    def computeHmean(self):
        invSum = 0.0
        for sp in self.speedups:
            invSum += 1 / sp
            
        return self.n / invSum
    
class SystemThroughput(WorkloadMetric):
    
    def __init__(self):
        self.spmNeeded = True
    
    def computeMeticValue(self):
        return self.computeSum()
    
class HarmonicMeanOfSpeedups(WorkloadMetric):
    
    def __init__(self):
        self.spmNeeded = True
    
    def computeMeticValue(self):
        return self.computeHmean()
    
class Fairness(WorkloadMetric):
    
    def __init__(self):
        self.spmNeeded = True
    
    def computeMeticValue(self):
        largestSpeedup = max(self.speedups)
        smallestSpeedup = min(self.speedups)
        return smallestSpeedup / largestSpeedup

class Sum(WorkloadMetric):
    
    def __init__(self):
        self.spmNeeded = True
    
    def computeMeticValue(self):
        return self.computeSum()

class HarmonicMean(WorkloadMetric):
    
    def __init__(self):
        self.spmNeeded = False
    
    def computeMeticValue(self):
        return self.computeHmean()

class ArithmeticMean(WorkloadMetric):
    
    def __init__(self):
        self.spmNeeded = False
    
    def computeMeticValue(self):
        return self.computeSum() / float(self.n)