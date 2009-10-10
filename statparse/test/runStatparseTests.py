#!/usr/bin/python
from statparse.test.testStatifileParser import TestStatfileParser
from statparse.test.testMetrics import TestMetrics

import unittest
import sys

def main():
    
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner(verbosity=2) 
    
    print "Running parser tests..."
    
    parsertests = loader.loadTestsFromTestCase(TestStatfileParser)
    runner.run(parsertests)
    
    print "Running metrics tests..."
    metricstests = loader.loadTestsFromTestCase(TestMetrics)
    runner.run(metricstests)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())