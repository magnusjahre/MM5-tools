
import re
import sys

# Globals

bmPattern = re.compile("-EBENCHMARK=[a-zA-Z0-9]*")
instPattern = re.compile(" [0-9]+ ")

# Procedures

def getBenchmark(cmd):
    res = bmPattern.findall(cmd)
    bm = res[0].split('=')[1]
    return bm

def getSwitchCounts(fileID):
    switchfile = None
    name = fileID+"/cpuSwitchInsts.txt"
    try:
        switchfile = open(name)
    except IOError:
        sys.stderr.write("WARNING:\tCould not find file "+name+'\n')
        
    insts = {}
    if switchfile != None:
        for line in switchfile.readlines():
            res = instPattern.findall(line)
            cpuID = int(line.split(":")[0][9])
            insts[cpuID] = int(res[0])
            
    return insts

def checkAvgLatDriftError(idDict):
    
    minDiff = 0
    maxDiff = 0
    
    for wl in idDict:
        sharedID, aloneIDs = idDict[wl]
        
        sharedStarts = getSwitchCounts(sharedID)
        if sharedStarts != {}:
            cpuID = 0
            for a in aloneIDs:
                starts = getSwitchCounts(a)
                diff = (float(starts[0]) / float(sharedStarts[cpuID])) - 1
                if diff > maxDiff:
                    maxDiff = diff
                if diff < minDiff:
                    minDiff = diff
                
                cpuID += 1

    sys.stderr.write("Drift errors: "+str(maxDiff)+", "+str(minDiff)+"\n")