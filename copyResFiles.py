#!/usr/bin/python

import sys
import os
import pbsconfig
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
               "amhaTrace.txt",
               "MemoryBusQueueTime.txt",
               "MemoryBusQueueTrace*.txt",
               "dram_access_trace.txt",
               "estimation_access_trace_*.txt",
               "private_estimated_arrival_order_*.txt",
               "private_execution_order_*.txt",
               "*QueueOccupancyTrace.txt",
               "bbv_outfile.bb",
               "statsDumpOrder.txt"]

finResPrintPattern = re.compile("---------- End Simulation Statistics   ----------")

def checkFile(filename):
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

print "Retrieving result filenames.. ",

for cmd, params in pbsconfig.commandlines:
    resID = pbsconfig.get_unique_id(params)
    
    resfiles.append(resID+"/"+resID+".txt")

    if pbsconfig.get_np(params) > 1:
        wl = pbsconfig.get_workload(params)
        for i in range(pbsconfig.get_np(params)):
            aloneparams = pbsconfig.get_alone_params(wl,i,params)
            aloneid = pbsconfig.get_unique_id(aloneparams)
            alonefiles.append(aloneid+"/"+aloneid+".txt")

print "done!"


while resfiles != [] or alonefiles != []:
    print "Checking for finished experiments..."
    rfcopy = list(resfiles)
    for rf in rfcopy:
        if checkFile(rf):
            resfiles.remove(rf)

    alonecopy = list(alonefiles)
    for af in alonecopy:
        if checkFile(af):
            alonefiles.remove(af)


    print "Sleeping"
    time.sleep(sleeptime)

shutil.copy("pbsconfig.py", resdir)

print "All results copied!"
    
