
import experimentConfiguration

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

    def setValues(self, multiprogramValues, singleProgramValues):
        
        self.numSimpoints = len(multiprogramValues)
        assert self.numSimpoints > 0
        self.n = len(multiprogramValues[multiprogramValues.keys()[0]])
        self.speedups = [[] for i in range(self.numSimpoints)]
        
        if singleProgramValues == {}:
            if self.spmNeeded:
                raise Exception("Single program mode results needed by metric but not provided")
            
            for simpoint in multiprogramValues:
                
                if self.numSimpoints == 1:
                    simpointkey = 0
                else:
                    simpointkey = simpoint
                
                assert simpointkey not in self.speedups
                self.speedups[simpointkey] = []
                for bm in multiprogramValues[simpoint]:
                    self.speedups[simpointkey].append(float(multiprogramValues[simpoint][bm]))
        else:
            
            for simpoint in multiprogramValues:
                if simpoint not in singleProgramValues:
                    raise Exception("Results contain no single program data for simpoint "+str(simpoint))
                
                if self.numSimpoints == 1:
                    simpointkey = 0
                else:
                    simpointkey = simpoint
                
                assert simpointkey not in self.speedups
                self.speedups[simpointkey] = []
                for bm in multiprogramValues:
                    if bm not in singleProgramValues:
                        raise Exception("Results contain no single program data for benchmark "+str(bm))
                    
                    self.speedups[simpointkey].append(float(multiprogramValues[simpoint][bm]) / float(singleProgramValues[simpoint][bm]))
    
    def computeMetricValue(self):
        raise Exception("compute metric should only be called on subclasses")
    
    def computeSum(self):
        res = []
        for simpointVals in self.speedups:
            tmp = 0.0
            for v in simpointVals:
                tmp += v
            res.append(tmp)
        return res
    
    def computeHmean(self):
        res = []
        for simpointVals in self.speedups:
            invSum = 0.0
            for sp in simpointVals:
                invSum += 1 / sp
            
            res.append(self.n / invSum)
        return res
    
class SystemThroughput(WorkloadMetric):
    
    def __init__(self):
        self.spmNeeded = True
    
    def __str__(self):
        return "System Throughput"
    
    def computeMetricValue(self):
        return self.computeSum()
    
class HarmonicMeanOfSpeedups(WorkloadMetric):
    
    def __init__(self):
        self.spmNeeded = True
    
    def __str__(self):
        return "Harmonic Mean of Speedups"
    
    def computeMetricValue(self):
        return self.computeHmean()
    
class Fairness(WorkloadMetric):
    
    def __init__(self):
        self.spmNeeded = True
    
    def __str__(self):
        return "Fairness"
    
    def computeMetricValue(self):
        res = []
        for simpointVals in self.speedups:
            largestSpeedup = max(simpointVals)
            smallestSpeedup = min(simpointVals)
            res.append(smallestSpeedup / largestSpeedup)
        return res

class Sum(WorkloadMetric):
    
    def __init__(self):
        super(Sum, self).__init__()
        self.spmNeeded = False
        
    def __str__(self):
        return "Sum"
    
    def computeMetricValue(self):
        return self.computeSum()

class HarmonicMean(WorkloadMetric):
    
    def __init__(self):
        self.spmNeeded = False
        
    def __str__(self):
        return "Harmonic Mean"
    
    def computeMetricValue(self):
        return self.computeHmean()

class ArithmeticMean(WorkloadMetric):
    
    def __init__(self):
        self.spmNeeded = False
    
    def __str__(self):
        return "Arithmetic Mean"
    
    def computeMetricValue(self):
        res = []
        for sum in self.computeSum():
            res.append(sum / float(self.n))
        return res
