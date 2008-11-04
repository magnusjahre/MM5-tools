
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

def checkFile(filename, pattern, limit):
    try:
        tmpfile = open(filename)
    except:
        tmpfile = None

    if tmpfile != None:
        res = pattern.findall(tmpfile.read())
        if res != []:
            assert(len(res) == 1)
            value = int(res[0].split()[1])
            if value >= (limit * 0.99):
                dirname,textfile = os.path.split(filename)
                print "Copying results for exp "+dirname
                curDest = resdir+"/"+dirname 
                os.mkdir(curDest)
                shutil.copy(filename, curDest)
                for f in resultfiles:
                    names = glob.glob(dirname+'/'+f)
                    for name in names:
                        shutil.copy(name, curDest)
                return True

    return False
    


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
instpattern = re.compile("COM:count.*")


print
print "Starting result copy..."
print "Ticks:       "+str(simticks)
print "Destination: "+resdir
print

resfiles = []
alonefiles = []

print "Retrieving result filenames.. ",

for cmd, params in pbsconfig.commandlines:
    resID = pbsconfig.get_unique_id(params)
    
    resfiles.append(resID+"/"+resID+".txt")

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
        if checkFile(rf, tickpattern, simticks):
            resfiles.remove(rf)

    alonecopy = list(alonefiles)
    for af in alonecopy:
        if checkFile(af, instpattern, 0):
            alonefiles.remove(af)


    print "Sleeping"
    time.sleep(sleeptime)

shutil.copy("pbsconfig.py", resdir)

print "All results copied!"
    
