
import re
import struct
import os

__metaclass__ = type

def writeBinaryData(file, typestr, data):
    outstr = struct.pack(typestr, data)
    file.write(outstr)

class CheckpointConverter():

    cachePat = re.compile("[Cc]aches?[0-9]")
    memPat = re.compile("workload0.MainMem")

    def __init__(self, checkpointFileName):
        self.filename = checkpointFileName
        self.cachedata = {}
        
    def convert(self):
        cptfile = open(self.filename)
        
        for line in cptfile:
            if line.startswith("["):
                sectionName = self._removeBrackets(line)
                if self.cachePat.search(sectionName):
                    
                    if "." in sectionName:
                        self._parseCacheBlock(cptfile, sectionName)
                    else:
                        if sectionName not in self.cachedata:
                            self.cachedata[sectionName] = {}
                        
                elif self.memPat.search(sectionName):
                    print "Generating page data for section "+sectionName
                    pages = self._parseMemory(cptfile)
                    print "Writing pages to the pagefile"
                    self._writePagesToFile(pages)
                    pages = None
                    print sectionName+" done"
                    
        self._writeCacheData()
    
        print "Removing obsolete elements from checkpointfile"
        self._cleanCheckpoint()
    
    def _cleanCheckpoint(self):
        os.rename(self.filename, self.filename+".old")
        infile = open(self.filename+".old")
        outfile = open(self.filename, "w")
        
        for line in infile:
            if line.startswith("["):
                sectionName = self._removeBrackets(line)
                if self.cachePat.search(sectionName):
                    if "." in sectionName:
                        self._cleanCache(infile)
                    else:
                        outfile.write(line)
                        outfile.write("filename="+sectionName+"-content.bin\n")
                elif self.memPat.search(sectionName):
                    self._cleanMemPages(sectionName, infile, outfile)
                else:
                    outfile.write(line)
            else:
                outfile.write(line)
                
        outfile.close()
        infile.close()
        
    def _cleanCache(self, infile):
        for line in infile:
            if line.strip() == "":
                return
    
    def _cleanMemPages(self, sectionName, infile, outfile):
        outfile.write("["+sectionName+"]\n")
        for line in infile:
            if line.strip() == "":
                outfile.write("filename=pages0.bin\n\n")
                return
            elif line.startswith("tag"):
                continue
            elif line.startswith("page"):
                continue
            else:
                outfile.write(line)
    
    def _writeCacheData(self):
        caches = self.cachedata.keys()
        
        for c in caches:
            print "Writing datafile for cache "+c
            cachefile = open(c+"-content.bin", "wb")
            
            indexes = self.cachedata[c].keys()
            indexes.sort()
            
            positions = self.cachedata[c][indexes[0]].keys()
            positions.sort()
            
            elements = len(indexes) * len(positions)
            writeBinaryData(cachefile, "i", elements)
            
            for i in indexes:
                for p in positions:
                    self.cachedata[c][i][p].write(cachefile)
            
            cachefile.close()
    
    def _parseCacheBlock(self, cptfile, sectionName):
        
        cache,blockname = sectionName.split(".")
        namesplit = blockname.split("_")
        cacheSet = int(namesplit[1])
        lruPos = int(namesplit[2])
        
        if cacheSet not in self.cachedata[cache]:
            self.cachedata[cache][cacheSet] = {}
        assert lruPos not in self.cachedata[cache][cacheSet]
        self.cachedata[cache][cacheSet][lruPos] = CacheBlock()
        
        for line in cptfile:
            if line.strip() == "":
                return
            assert "=" in line
            name,val = line.strip().split("=")
            self.cachedata[cache][cacheSet][lruPos].setElement(name, val)
            
        
    
    def _parseMemory(self, cptfile):
        
        pages = {}
        
        for line in cptfile:
            if line.strip() == "":
                return pages
            
            if not (line.startswith("tag") or line.startswith("page")):
                continue
            
            key, data = line.strip().split("=")
            splitted = key.split("-")
            name = splitted[0]
            index = int(splitted[1])
            pos = int(splitted[2])
            
            if name == "tag":
                if index not in pages:
                    pages[index] = {}                
                else:
                    assert pos not in pages[index]
                pages[index][pos] = MemoryPage(data)
            elif name == "page":
                assert index in pages
                assert pos in pages[index]
                pages[index][pos].addData(data)
                
        raise Exception("Unexpected end of file")
    
    def _writePagesToFile(self, pages):
        outfile = open("pages0.bin", "wb")
        
        indexes = pages.keys()
        indexes.sort()
        
        writeBinaryData(outfile, "i", len(indexes))
        
        indexnum = 0
        for i in indexes:
            
            if (indexnum % 500) == 0 and indexnum > 0:
                print "Wrote "+str(indexnum)+" out of "+str(len(indexes))+" indexes"
            indexnum += 1
            
            positions = pages[i].keys()
            positions.sort()
            
            writeBinaryData(outfile, "i", i)
            writeBinaryData(outfile, "i", len(positions))
            
            for p in positions:
                pages[i][p].write(outfile)
    
        outfile.close()
    
    def _removeBrackets(self, text):
        return text[1:-2]
    
class MemoryPage():
    
    def __init__(self, tag):
        self.tag = int(tag)
        self.data = []
        
    def addData(self, pagestring):
        tmpdata = pagestring.split()
        for elem in tmpdata:
            self.data.append(int(elem))
            
    def write(self, file):
        writeBinaryData(file, "Q", self.tag)
        for byte in self.data:
            writeBinaryData(file, "B", byte)
            
class CacheBlock():
    
    def __init__(self):
        self.asid = -1
        self.tag = -1
        self.status = -1
        self.origRequestingCpuID = -1
        self.prevOrigRequestingCpuID = -1
        self.set = -1
        
    def setElement(self, name, value):
        if name == "asid":
            self.asid = int(value)
        elif name == "tag":
            self.tag = int(value)
        elif name == "status":
            self.status = int(value)
        elif name == "origRequestingCpuID":
            self.origRequestingCpuID = int(value)
        elif name == "prevOrigRequestingCpuID":
            self.prevOrigRequestingCpuID = int(value)
        elif name == "set":
            self.set = int(value)
        else:
            raise Exception("unknown data element in cache block")
        
    def write(self, file):
        writeBinaryData(file, "i", self.asid)
        writeBinaryData(file, "Q", self.tag)
        writeBinaryData(file, "I", self.status)
        writeBinaryData(file, "i", self.origRequestingCpuID)
        writeBinaryData(file, "i", self.prevOrigRequestingCpuID)
        writeBinaryData(file, "i", self.set)
