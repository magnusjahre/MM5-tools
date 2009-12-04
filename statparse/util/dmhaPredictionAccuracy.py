#!/usr/bin/env python

""" This program is a convenience program for computing the accuracy of the 
    DMHA predictions based on the missBandwidthPolicy prediction and 
    measurement traces
"""

from optparse import OptionParser

def parseArgs():
    parser = OptionParser(usage="[name here].py [options] [arguments]")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")

    opts, args = parser.parse_args()
    return opts,args
    
def main():

    opts,args = parseArgs()

if __name__ == '__main__':
    main()