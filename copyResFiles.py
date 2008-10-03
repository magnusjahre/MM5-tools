
import sys
import os
import os.path
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
               "amhaTrace.txt"]

try:
    simticks = int(sys.argv[1])
    resdir = sys.argv[2]
except:
    print "Cannot parse commandline..."
    print "Usage: python -c \"import getResFiles\" simticks result_dir"
    sys.exit()

if not os.path.isdir(resdir):
    print "Destination directory is not valid, quitting"
    sys.exit()

tickpattern = re.compile("sim_ticks.*")

print
print "Starting result copy..."
print "Ticks:       "+str(simticks)
print "Destination: "+resdir
print

resfiles = []

print "Retrieving result filenames.. ",

for cmd, params in pbsconfig.commandlines:
    resID = pbsconfig.get_unique_id(params)
    resfiles.append(resID+"/"+resID+".txt")
    

print "done!"


while resfiles != []:
    print "Checking for finished experiments..."
    rfcopy = list(resfiles)
    for rf in rfcopy:

        try:
            tmpfile = open(rf)
        except:
            tmpfile = None

        if tmpfile != None:
            res = tickpattern.findall(tmpfile.read())
            if res != []:
                ticks = int(res[0].split()[1])
                if ticks >= (simticks * 0.99):
                    dirname,filename = os.path.split(rf)
                    print "Copying results for exp "+dirname
                    curDest = resdir+"/"+dirname 
                    os.mkdir(curDest)
                    shutil.copy(rf, curDest)
                    for f in resultfiles:
                        names = glob.glob(dirname+'/'+f)
                        for name in names:
                            shutil.copy(name, curDest)
                    
                    resfiles.remove(rf)


    print "Sleeping"
    time.sleep(sleeptime)

shutil.copy("pbsconfig.py", resdir)

print "All results copied!"
    
