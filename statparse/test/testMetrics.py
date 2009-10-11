import statparse.metrics as metrics
from statparse import experimentConfiguration

import unittest
import random
import simpoints.simpoints as simpoints
import deterministic_fw_wls as workloads


class TestMetrics(unittest.TestCase):


    def generateValues(self):
        
        mpbvals = {}
        spbvals = {}
        
        for i in range(self.np):
            mpbval = random.random()
            spbval = random.random()
            while spbval < mpbval:
                spbval = random.random()
                
            mpbvals[self.bms[i]] = mpbval
            spbvals[self.bms[i]] = spbval
        return mpbvals, spbvals

    def setUp(self):

        self.np = 16
        self.maxk = simpoints.maxk
        self.wl = "fair01"
        self.bms = workloads.getBms(self.wl, self.np, True)

        random.seed(3)

        self.noSimpointMPBValues = {}
        self.noSimpointSPBValues = {}
        self.simpointMPBValues = {}
        self.simpointSPBValues = {}

        noSimMPB, noSimSPB = self.generateValues()
        self.noSimpointMPBValues[experimentConfiguration.NO_SIMPOINT_VAL] = noSimMPB
        self.noSimpointSPBValues[experimentConfiguration.NO_SIMPOINT_VAL] = noSimSPB
        
        for i in range(self.maxk):
            simMPB, simSPB = self.generateValues()
            self.simpointMPBValues[i] = simMPB
            self.simpointSPBValues[i] = simSPB
            
        self.avgTestValues = []
        for i in range(20):
            self.avgTestValues.append(random.random())
    
    def computeSpeedup(self, mpb, spb):
        res = {}
        for bm in mpb:
            assert bm in spb
            res[bm] = mpb[bm] / spb[bm]
        return res
    
    def computeHmean(self, vals):
        invsum = 0
        for bm in vals:
            invsum += 1 / vals[bm]
        return self.np / invsum
    
    def testBaseComputeError(self):
        metric = metrics.WorkloadMetric()
        causedException = False
        try:
            metric.computeMetricValue()
        except:
            causedException = True
            
        self.assert_(causedException)
        
    def testCreateMetricError(self):
        causedException = False
        try:
            metrics.createMetric("tullenavn")
        except:
            causedException = True
        self.assert_(causedException)
    
    def testHmosSpeedupExceptions(self):
        hmos = metrics.createMetric("hmos")
        causedException = False
        try:
            hmos.setValues(self.noSimpointMPBValues, {}, self.np, self.wl)
        except:
            causedException = True
            
        self.assert_(causedException)
            
    def checkRes(self, testres, actualres):
        for i in range(len(testres)):
            self.assertAlmostEqual(testres[i], actualres[i]) 
    
    
    def testHmeanNoSimpoint(self):
        metric = metrics.createMetric("hmean")
        metricname =  str(metric)
        metric.setValues(self.noSimpointMPBValues, {}, self.np, self.wl)
        result = metric.computeMetricValue()
        
        vals = self.noSimpointMPBValues[experimentConfiguration.NO_SIMPOINT_VAL]
        hmean = self.computeHmean(vals)
        
        self.assert_(len(result) == 1)
        self.assertAlmostEqual(hmean, result[0])
    
    def testHmeanSimpoints(self):
        metric = metrics.createMetric("hmean")
        metric.setValues(self.simpointMPBValues, {}, self.np, self.wl)
        result = metric.computeMetricValue()
        
        hmeanData = []
        for simpoint in self.simpointMPBValues:
            assert simpoint in self.simpointSPBValues
            hmeanData.append(self.computeHmean(self.simpointMPBValues[simpoint]))
        
        self.checkRes(hmeanData, result) 
        
    def testHmosSimpoints(self):
        metric = metrics.createMetric("hmos")
        metricname =  str(metric)
        metric.setValues(self.simpointMPBValues, self.simpointSPBValues, self.np, self.wl)
        result = metric.computeMetricValue()
        
        hmosData = []
        for simpoint in self.simpointMPBValues:
            assert simpoint in self.simpointSPBValues
            speedup = self.computeSpeedup(self.simpointMPBValues[simpoint], self.simpointSPBValues[simpoint])
            hmosData.append(self.computeHmean(speedup))
        
        self.checkRes(hmosData, result)
       
    def testFairness(self):
        metric = metrics.createMetric("fairness")
        metricname =  str(metric)
        metric.setValues(self.noSimpointMPBValues, self.noSimpointSPBValues, self.np, self.wl)
        result = metric.computeMetricValue()
        
        speedups = self.computeSpeedup(self.noSimpointMPBValues[experimentConfiguration.NO_SIMPOINT_VAL], self.noSimpointSPBValues[experimentConfiguration.NO_SIMPOINT_VAL])
        maxval = max(speedups.values())
        minval = min(speedups.values())
        fairness = minval / maxval

        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(fairness, result[0])
    
    def testSTP(self):
        metric = metrics.createMetric("stp")
        metricname =  str(metric)
        metric.setValues(self.noSimpointMPBValues, self.noSimpointSPBValues, self.np, self.wl)
        result = metric.computeMetricValue()
        
        speedups = self.computeSpeedup(self.noSimpointMPBValues[experimentConfiguration.NO_SIMPOINT_VAL], self.noSimpointSPBValues[experimentConfiguration.NO_SIMPOINT_VAL])
        stp = sum(speedups.values())

        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(stp, result[0])
    
    def testSum(self):
        metric = metrics.createMetric("sum")
        metricname =  str(metric)
        
        val = sum(self.avgTestValues)
        for v in self.avgTestValues:
            metric.addValue(v, self.np)
            
        result = metric.computeMetricValue()
        
        self.assertEqual(len(result), 1)    
        self.assertAlmostEqual(val, result[0])
        
        
        metric.clearValues()
        for v in self.avgTestValues:
            metric.addValue(v, self.np)
    
        newResult = metric.computeMetricValue()
        self.assertEqual(len(newResult), 1)    
        self.assertAlmostEqual(val, newResult[0])
    
    def testAmean(self):    
        metric = metrics.createMetric("amean")
        metricname =  str(metric)
        
        thisSum = sum(self.avgTestValues)
        
        for v in self.avgTestValues:
            metric.addValue(v, self.np)
            
        for i in range(5):
            metric.addValue(metric.errStr, self.np)
            
        result = metric.computeMetricValue()
        thisAvg = thisSum / len(self.avgTestValues)
        
        self.assertEqual(len(result), 1)    
        self.assertAlmostEqual(thisAvg, result[0])
    
    def testNoMetric(self):
        metric = metrics.NoAggregation(False)
        metricname =  str(metric)
        metric.setValues(self.noSimpointMPBValues, {}, self.np, self.wl)
        result = metric.computeMetricValue()
        
        vals = []
        for bm in self.bms:
            vals.append(self.noSimpointMPBValues[experimentConfiguration.NO_SIMPOINT_VAL][bm])
        
        self.assertEqual(len(result), 1)
        self.checkRes(vals, result[0])
        
    def testNoMetricSpeedup(self):
        metric = metrics.NoAggregation(True)
        metric.setValues(self.noSimpointMPBValues, self.noSimpointSPBValues, self.np, self.wl)
        result = metric.computeMetricValue()
        
        speedups = []
        for bm in self.bms:
            assert bm in self.noSimpointMPBValues[experimentConfiguration.NO_SIMPOINT_VAL]
            assert bm in self.noSimpointSPBValues[experimentConfiguration.NO_SIMPOINT_VAL]
            speedup = self.noSimpointMPBValues[experimentConfiguration.NO_SIMPOINT_VAL][bm] / self.noSimpointSPBValues[experimentConfiguration.NO_SIMPOINT_VAL][bm]
            speedups.append(speedup)
        

        self.assertEqual(len(result), 1)
        self.checkRes(speedups, result[0])
        
    def testPartialResults(self):
                
        results = {experimentConfiguration.NO_SIMPOINT_VAL: []}
        spbres = {experimentConfiguration.NO_SIMPOINT_VAL: []}

        self.checkMetric(metrics.Sum(), results, {})
        self.checkMetric(metrics.ArithmeticMean(), results, {})
        self.checkMetric(metrics.Fairness(), results, spbres)
        self.checkMetric(metrics.SystemThroughput(), results, spbres)
        self.checkMetric(metrics.HarmonicMean(), results, {})
        self.checkMetric(metrics.HarmonicMeanOfSpeedups(), results, spbres)
        
        expectedRes = [[metrics.WorkloadMetric().errStr for i in range(self.np)]]
        self.checkMetric(metrics.NoAggregation(False), results, {}, expectedRes)
        self.checkMetric(metrics.NoAggregation(True), results, spbres, expectedRes)
        
        # tests that no results are stored if only the spb results are missing
        self.checkMetric(metrics.Fairness(), self.noSimpointMPBValues, spbres)
        
        
    def checkMetric(self, metric, results, spbresults, expected = [metrics.WorkloadMetric().errStr]):
        metric.setValues(results, spbresults, self.np, self.wl)
        result = metric.computeMetricValue()
        self.assertEqual(result, expected)
        
    def testErrorString(self):
        
        metric = metrics.Fairness()
        errStr = metric.returnErrorString()
        
        self.assertEqual(len(errStr), simpoints.maxk)
        for e in errStr:
            self.assertEqual(e, metric.errStr)
            
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()