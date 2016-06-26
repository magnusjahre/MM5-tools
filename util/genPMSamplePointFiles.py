#!/usr/bin/python

import sys
import os
from optparse import OptionParser
from statparse.util import getNpExperimentDirs
from statparse.tracefile.tracefileData import TracefileData
from workloadfiles.workloads import Workloads

def parseArgs():
    
    parser = OptionParser(usage="genPMSamplePointFiles.py [options] [trace-file-name]")
    #parser.add_option("--max-insts", action="store", dest="maxInsts", default=100000000, type="int", help="Size of a private mode experiment in committed instructions (Default: 100 million)")
    parser.add_option("--outfile", action="store", dest="outfile", default="sample-ints.txt", type="string", help="Output file name (Default: sample-insts.txt)")
    parser.add_option("--np", action="store", dest="np", default=4, type="int", help="Number of CPUs used in the experiment (Default: 4)")
    opts, args = parser.parse_args()
    
    if len(args) > 1:
        print "Command line error, usage:"
        print parser.usage
        sys.exit()
        
    return opts, args

def readSharedModeInstSamples(tracefilename):
    print "Retrieving instruction sample points from file "+tracefilename
    tracedata = TracefileData(tracefilename)
    tracedata.readTracefile()
    colID = tracedata.findColumnID("Cummulative Committed Instructions", -1)
    instSampPoints = tracedata.getColumn(colID)
    return instSampPoints

def writeSamplePointFile(samplePoints, outputFileName):
    if len(samplePoints) == 0:
        print "WARNING: No sample points for outfile "+outputFileName
        return

    print "Writing instruction sample points to file "+outputFileName
    outfile = open(outputFileName, "w")
    
    outfile.write(str(int(samplePoints[0])))
    samplePoints.pop(0)
    while samplePoints != []:
        outfile.write(","+str(int(samplePoints[0])))
        samplePoints.pop(0)
    outfile.write("\n")
        
    outfile.flush()
    outfile.close()
    
def main():
    opts,args = parseArgs()
    
    if len(args) != 0:
        samplePoints = readSharedModeInstSamples(args[0])
        writeSamplePointFile(samplePoints, opts.outfile)
        return 0
    
    expDirs, expParams = getNpExperimentDirs(opts.np)
    workloads = Workloads()
    for d in expDirs:
        wlID, params, smDir, pmIDs = d
        print "Processing directory "+smDir
        os.chdir(smDir)
        bms = workloads.getBms(wlID, opts.np)
        bmID = 0
        for bm in bms:
            samplePoints = readSharedModeInstSamples("globalPolicyCommittedInsts"+str(bmID)+".txt")
            writeSamplePointFile(samplePoints, "pm-sample-points-"+wlID+"-"+str(bmID)+"-"+bm+".txt")
            bmID += 1
            
        os.chdir("..")

if __name__ == '__main__':
    main()
