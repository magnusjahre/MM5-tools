#!/usr/bin/python

import sys
import pbsconfig
import parsemethods
from optparse import OptionParser

def parseParameters():
    parser = OptionParser(usage="retrieveInterferenceMissDistribution.py [options] ['writeback'|'miss'] [np]")
    #parser.add_option("--tolerance", type="int", action="store", dest="tolerance", default=-1, help="The number of misses needed to include the results in the statistics")
    options,args = parser.parse_args()
    
    return parser,options,args

def writeOutput(histograms, filePrefix):

    aggregateHistogram = {}

    for k in histograms:
        aggregateHistogram[k] = {}

        for cachebank in histograms[k]:
            for distance in histograms[k][cachebank]:
                if distance not in aggregateHistogram[k]:
                    aggregateHistogram[k][distance] = 0
                aggregateHistogram[k][distance] += histograms[k][cachebank][distance]

    for k in aggregateHistogram:
        filename = filePrefix+"-"+str(k)+".txt"
        print "Writing histogram to file "+filename
        outfile = open(filename, "w")
        outfile.write("Distance;Freq\n")
        for distance in aggregateHistogram[k]:
            outfile.write(str(distance)+";"+str(aggregateHistogram[k][distance])+"\n")
    print

def main(argv):

    parser,options,args = parseParameters()    

    if len(args) != 2:
        print "Wrong number of arguments"
        print "Usage: "+parser.usage
        sys.exit(-1)

    if args[0] == "miss":
        filePrefix = "interference-miss-distribution"
        baseDistName = "SharedCache.*interference_miss_distance_distribution"
    elif args[0] == "writeback":
        filePrefix = "writeback-distance-distribution"
        baseDistName = "SharedCache.*private_writeback_distance_distribution"
    else:
        print "Unknown command: must be either miss or writeback"
        sys.exit(-1)

    try:
        np = int(args[1])
    except:
        print "Unknown CPU count provided"
        sys.exit(-1)

    print
    print "Parsing experiment results to retrieve "+args[0]+" distribution.."
    print 

    distributionNames = []
    for i in range(np):
        distributionNames.append(baseDistName+"_"+str(i))
    
    histograms = parsemethods.createHistograms(pbsconfig, distributionNames)
    
    writeOutput(histograms, filePrefix)
    

if __name__ == "__main__":
    sys.exit(main(sys.argv))
