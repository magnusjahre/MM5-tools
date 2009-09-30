
from CacheState import CacheState
import re
import sys

sectionPattern = re.compile("\[.*\]")
whitespacePattern = re.compile("^\s+")
commentPattern = re.compile("^//.*")
elementPattern = re.compile(".*=.*")

sharedCachePattern = re.compile("SharedCache[0-9]")
simpleCPUPattern = re.compile("simpleCPU[0-9]")
l1cachePattern = re.compile("L1[di]caches[0-9]")
privL2cachePattern = re.compile("PrivateL2Cache[0-9]")
detailedCPUPattern = re.compile("detailedCPU")
blkPattern = re.compile("blk") 
cacheCPUIDPattern = re.compile("cacheCpuID")
workloadPattern = re.compile("workload")
filenamePattern = re.compile("filename=")
    
def read(filename, outfilename, newCoreID):
    inifile = open(filename)
    
    outfile = open(outfilename, "a")
    
    curSec = None
    writeToFile = False
    
    for l in inifile:
        
        if whitespacePattern.match(l) != None:
            # skip whitespace
            continue
        elif commentPattern.match(l) != None:
            # skip comments
            continue
        
        elif sectionPattern.match(l) != None:
            name = l.strip()
            name = name.replace("[","")
            name = name.replace("]", "") 
            
            if sharedCachePattern.match(name) != None:
                writeToFile = False
            
            else:
                if translationNeeded(name):
                    newName = translateHeader(name, newCoreID)
                    
                    if workloadPattern.search(newName) != None:
                        newName = newName.replace("workload0", "workload")
                    
                    writeHeader(newName, outfile)
                    writeToFile = True
                else:
                    if newCoreID == 0 and detailedCPUPattern.match(name) == None:
                        writeHeader(name, outfile)
                        writeToFile = True
                    else:
                        writeToFile = False
                curSec = None
            
            
        elif elementPattern.match(l) != None:
            if writeToFile:
                assert curSec == None
                line = l.strip()
                if cacheCPUIDPattern.match(line):
                    outfile.write("cacheCpuID="+str(newCoreID)+"\n")
                if filenamePattern.match(line):
                    outfile.write(line.strip().replace("0", str(newCoreID))+"\n")
                else:
                    outfile.write(l.strip()+"\n")
            else:
                if curSec != None:
                    curSec.addContent(l, newCoreID)
        
        else:
            print "Unknown section encountered in checkpointfile "+filename
            print "Line: "+l
            sys.exit(-1)
            
    inifile.close()
    
    outfile.flush()
    outfile.close()

def translateHeader(name, newCPUID):
    split = name.split(".")
    
    newName = split[0].replace("0", str(newCPUID))
    for n in split[1:]:
        newName += "."+n
    return newName

def translationNeeded(name):
    if sharedCachePattern.match(name) != None or simpleCPUPattern.match(name) != None or l1cachePattern.match(name) != None or privL2cachePattern.match(name) != None:
        return True
    return False
    

def write(filename, sharedCaches):
    
    outfile = open(filename, "a")
    
    for scName in sharedCaches:
        sharedCaches[scName].writeValues(outfile)
    
    outfile.flush()
    outfile.close()
    
def writeHeader(name, outfile):        
    outfile.write("\n["+name+"]\n")
    
