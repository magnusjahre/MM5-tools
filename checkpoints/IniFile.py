
from CacheState import CacheState
import re
import sys

sectionPattern = re.compile("\[.*\]")
whitespacePattern = re.compile("^\s+")
commentPattern = re.compile("^//.*")
elementPattern = re.compile(".*=.*")

sharedCachePattern = re.compile("SharedCache[0-9]")
simpleCPUPattern = re.compile("SimpleCPU[0-9]")
l1cachePattern = re.compile("L1[di]caches[0-9]")
blkPattern = re.compile("blk") 


    
def read(filename, outfilename, newCoreID):
    inifile = open(filename)
    
    outfile = open(outfilename, "a")
    
    sharedCaches = {}
    
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
            
                if blkPattern.search(name) != None:
                    cache, blk = name.split(".")
                    assert cache in sharedCaches
                    sharedCaches[cache].setCurrentBlock(name)
                    
                else:
                    if name not in sharedCaches:
                        thisSection = CacheState()
                        thisSection.setName(name)
                        sharedCaches[name] = thisSection
                        curSec = thisSection
                        

                writeToFile = False
            
            else:
                writeHeader(name, outfile)
                writeToFile = True
                curSec = None
            
            
        elif elementPattern.match(l) != None:
            if writeToFile:
                assert curSec == None
                outfile.write(l.strip()+"\n")
            else:
                assert curSec != None
                curSec.addContent(l)
        
        else:
            print "Unknown section encountered in checkpointfile "+filename
            print "Line: "+l
            sys.exit(-1)
            
    inifile.close()
    
    outfile.flush()
    outfile.close()
    
    return sharedCaches
    
    
def write(filename, sharedCaches):
    
    outfile = open(filename, "a")
    
    for scName in sharedCaches:
        sharedCaches[scName].writeValues(outfile)
    
    outfile.flush()
    outfile.close()
    
def writeHeader(name, outfile):        
    outfile.write("\n["+name+"]\n")
    
