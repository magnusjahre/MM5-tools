#!/usr/bin/python

import sys
import os
import re
import time
import shutil
import glob

sleeptime = 60

resultfiles = ["interconnect*.txt",
               "adaptiveMHATrace.txt",
               "memoryBusTrace.txt",
               "*CapacityProfile.txt",
               "cpuSwitchInsts.txt",
               "*BlockedTrace.txt",
               "ipcTrace.txt",
               "fairAlgTrace.txt",
               "*MTPTrace.txt",
               "*HitStats.txt",
               "interferenceStats.txt",
               "*InterferenceTrace.txt",
               "*LatencyTrace.txt",
               "*MissTrace.txt",
               "amhaTrace.txt",
               "MemoryBusQueueTime.txt",
               "MemoryBusQueueTrace*.txt",
               "dram_access_trace.txt",
               "estimation_access_trace_*.txt",
               "private_estimated_arrival_order_*.txt",
               "private_execution_order_*.txt",
               "*QueueOccupancyTrace.txt",
               "bbv_outfile.bb",
               "statsDumpOrder.txt",
               "missBandwidthPolicy*.txt",
               "globalPolicy*.txt",
               "detailedCPU*IPCTrace.txt",
               "*-bmout.txt",
               "membus*.txt",
               "overlapEstimator*.txt",
               "overlapTable*.txt",
               "pm-sample-points*.txt",
               "simoutput.txt",
               "cachePartitioning*.txt"]

finResPrintPattern = re.compile("---------- End Simulation Statistics   ----------")

def checkFile(filename, resdir):
    try:
        tmpfile = open(filename)
    except:
        tmpfile = None

    if tmpfile != None:
        res = finResPrintPattern.findall(tmpfile.read())
        if res != []:
            dirname,textfile = os.path.split(filename)
            curDest = resdir+"/"+dirname 
            if os.path.exists(curDest):
                print "Directory exists for experiment "+filename+", skipping"
                if not os.path.exists(curDest+"/"+textfile):
                    print "WARNING: no resultsfile found ("+textfile+")"
                for f in resultfiles:
                    names = glob.glob(dirname+'/'+f)
                    for name in names:
                        if not os.path.exists(name):
                            print "WARNING: file not found ("+name+")"

            else:
                print "Copying results for exp "+dirname
                os.mkdir(curDest)
                shutil.copy(filename, curDest)
                for f in resultfiles:
                    names = glob.glob(dirname+'/'+f)
                    for name in names:
                        shutil.copy(name, curDest)
            return True

    return False
    
def main():

    try:
        resdir = sys.argv[1]
    except:
        print "Cannot parse commandline..."
        print "Usage: python -c \"import getResFiles\" result_dir"
        sys.exit()
    
    if not os.path.isdir(resdir):
        print "Destination directory is not valid, quitting"
        sys.exit()
    
    print
    print "Starting result copy..."
    print "Destination: "+resdir
    print
    
    resfiles = []
    alonefiles = []
    
    print "Retrieving result filenames.. "
    
    pbsconfig = __import__("pbsconfig")
    for cmd, params in pbsconfig.commandlines:
        resID = pbsconfig.get_unique_id(params)
        resfiles.append(resID+"/"+resID+".txt")

    if hasattr(pbsconfig, "privModeCommandlines"):
        for cmd, params in pbsconfig.privModeCommandlines:
            resID = pbsconfig.get_unique_id(params)
            resfiles.append(resID+"/"+resID+".txt")
    else:
        print "Warning: PBS-file does not contain a privModeCommandlines variable"
    
    shutil.copy("pbsconfig.py", resdir)
    
    while resfiles != [] or alonefiles != []:
        print "Checking for finished experiments..."
        rfcopy = list(resfiles)
        for rf in rfcopy:
            if checkFile(rf, resdir):
                resfiles.remove(rf)
    
        alonecopy = list(alonefiles)
        for af in alonecopy:
            if checkFile(af, resdir):
                alonefiles.remove(af)
    
    
        print "Sleeping"
        time.sleep(sleeptime)
    
    print "All results copied!"
        
if __name__ == '__main__':
    main()
