import simpoints.simpoints as simpoints
import experimentConfiguration

from workloadfiles.workloads import Workloads
workloads = Workloads()

__metaclass__ = type

metrics = {"hmos": "Harmonic Mean of Speedups",
           "fairness": "Fairness",
           "stp": "System Throughput",
           "hmean": "Harmonic Mean",
           "amean": "Arithmetic Mean",
           "sum": "Sum"}

mpMetricNames = ["hmos", "fairness", "stp", "sum"]

errorString = "N/A"

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

def buildSimpointDict(benchmarkList, performanceList):
    
    if len(benchmarkList) != len(performanceList):
        raise Exception("Benchmark name list and performance list must have the same length")
    
    bmdict = {}
    for i in range(len(benchmarkList)):
        bmdict[benchmarkList[i]] = performanceList[i]
    
    retdict = {}
    retdict[experimentConfiguration.NO_SIMPOINT_VAL] = bmdict
    return retdict

class WorkloadMetric():

    def __init__(self):
        self.n = 0
        self.speedups = []
        self.spmNeeded = False
        self.errStr = errorString
        self.doTablePrint = False
        self.speedups = [[]]

    def setValues(self, multiprogramValues, singleProgramValues, np, wlOrBm):
        
        self.n = np
        
        if multiprogramValues == {} and singleProgramValues == {}:
            #results are missing, assume one simpoint 
            self.numSimpoints = 1
            self.speedups = [[]]
            
        elif experimentConfiguration.NO_SIMPOINT_VAL in multiprogramValues:
            # Simpoints have been removed by aggregation
            self.numSimpoints = 1
            self.speedups = [[]]
        else:
            # Simpoints are still present
            self.numSimpoints = simpoints.maxk
            self.speedups = [[] for i in range(self.numSimpoints)]
        
        if singleProgramValues == {}:
            if multiprogramValues != {} and self.spmNeeded:
                raise Exception("Single program mode results needed by metric but not provided")
            
            for simpoint in multiprogramValues:
                
                if self.numSimpoints == 1:
                    simpointkey = experimentConfiguration.NO_SIMPOINT_VAL
                else:
                    simpointkey = simpoint
                
                self._addSimpointValue(simpointkey, simpoint, multiprogramValues, singleProgramValues, wlOrBm)
                
        else:
            
            for simpoint in multiprogramValues:
                
                if self.numSimpoints == 1:
                    simpointkey = experimentConfiguration.NO_SIMPOINT_VAL 
                else:
                    simpointkey = simpoint
                
                self._addSimpointValue(simpointkey, simpoint, multiprogramValues, singleProgramValues, wlOrBm)
                
                    
    def _addSimpointValue(self, simpointkey, simpoint, mpb, spb, wlOrBm):
        
        if self.n == 1:
            benchmarks = [wlOrBm]
        else:
            benchmarks = workloads.getBms(wlOrBm, self.n, True)
        
        assert simpointkey not in self.speedups
        self.speedups[simpointkey] = []
        cpuID = 0
        for bm in benchmarks:
            subkey = experimentConfiguration.getSubkey(bm, cpuID)
            if subkey not in mpb[simpointkey]:
                self.speedups[simpoint].append(errorString)
                continue
                
            if spb != {}:
                if subkey not in spb[simpoint]:
                    #TODO: might want to leave values in as in MPB mode
                    self.speedups[simpoint] = []
                    return
                
                if spb[simpoint][subkey] == 0.0:
                    self.speedups[simpointkey].append(errorString)
                else:
                    self.speedups[simpointkey].append(float(mpb[simpoint][subkey]) / float(spb[simpoint][subkey]))
            else:
                self.speedups[simpointkey].append(float(mpb[simpoint][subkey]))
                
            cpuID += 1
        
    
    def addValue(self, value, np):
        if value == self.errStr:
            return
        self.speedups[0].append(value)
        self.n += 1
    
    def clearValues(self):
        self.speedups = [[]]
        self.n = 0
    
    def computeMetricValue(self):
        raise Exception("compute metric should only be called on subclasses")
    
    def computeSum(self):
        res = []
        for simpointVals in self.speedups:
            if simpointVals == []:
                res.append(self.errStr)
            else:
                tmp = 0.0
                for v in simpointVals:
                    tmp += v
                res.append(tmp)
        return res
    
    def computeHmean(self):
        res = []
        for simpointVals in self.speedups:
            if simpointVals == []:
                res.append(self.errStr)
            else:
                invSum = 0.0
                for sp in simpointVals:
                    invSum += 1 / sp
                
                res.append(self.n / invSum)
        return res

    def returnErrorString(self):
        return [self.errStr for i in range(simpoints.maxk)]
    
class SystemThroughput(WorkloadMetric):
    
    def __init__(self):
        super(SystemThroughput, self).__init__()
        self.spmNeeded = True
    
    def __str__(self):
        return "System Throughput"
    
    def key(self):
        return "stp"
    
    def computeMetricValue(self):
        return self.computeSum()
    
class HarmonicMeanOfSpeedups(WorkloadMetric):
    
    def __init__(self):
        super(HarmonicMeanOfSpeedups, self).__init__()
        self.spmNeeded = True
    
    def __str__(self):
        return "Harmonic Mean of Speedups"
    
    def key(self):
        return "hmos"
    
    def computeMetricValue(self):
        return self.computeHmean()
    
class Fairness(WorkloadMetric):
    
    def __init__(self):
        super(Fairness, self).__init__()
        self.spmNeeded = True
    
    def __str__(self):
        return "Fairness"
    
    def key(self):
        return "fairness"
    
    def computeMetricValue(self):
        res = []
        for simpointVals in self.speedups:
            if simpointVals == []:
                res.append(self.errStr)
            else:
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
    
    def key(self):
        return "sum"
    
    def computeMetricValue(self):
        return self.computeSum()

class HarmonicMean(WorkloadMetric):
    
    def __init__(self):
        super(HarmonicMean, self).__init__()
        self.spmNeeded = False
        
    def __str__(self):
        return "Harmonic Mean"
    
    def key(self):
        return "hmean"
    
    def computeMetricValue(self):
        return self.computeHmean()

class ArithmeticMean(WorkloadMetric):
    
    def __init__(self):
        super(ArithmeticMean, self).__init__()
        self.spmNeeded = False
    
    def __str__(self):
        return "Arithmetic Mean"
    
    def key(self):
        return "amean"
    
    def computeMetricValue(self):
        res = []
        for sum in self.computeSum():
            if sum == self.errStr:
                res.append(self.errStr)
            else:
                res.append(sum / float(self.n))
        return res

class NoAggregation(WorkloadMetric):
    def __init__(self, computeSpeedups):
        super(NoAggregation, self).__init__()
        self.spmNeeded = computeSpeedups
        self.doTablePrint = True
    
    def __str__(self):
        return "No Aggregation Metric"
    
    def computeMetricValue(self):
        retarr = []
        for simpointVals in self.speedups:
            if simpointVals == []:
                retarr.append([self.errStr for i in range(self.n)])
            else:
                retarr.append(simpointVals)
        return retarr