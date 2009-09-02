
import IniFile

__metaclass__ = type

class CacheState():

    def __init__(self, name, cpuID):
        self.name = name
        self.cpuID = cpuID
        
        self.cacheParams = ""        
        self.content = {}
        self.curIndex = -1
        self.curLRUPos = -1
        
    def setCurrentBlock(self, sectionName):
        
        cacheName, blkName = sectionName.split(".")
        assert cacheName == self.name
        
        t, index, LRUPos = blkName.split("_")
        self.curIndex = int(index)
        self.curLRUPos = int(LRUPos)
        
        
    def addContent(self, line, newCPUID):
        if self.curIndex == -1 and self.curLRUPos == -1:
            self.cacheParams += line
            return
        
        line = line.replace("origRequestingCpuID=0", "origRequestingCpuID="+str(newCPUID))
        
        if self.curIndex not in self.content:
            self.content[self.curIndex] = {}
            
        if self.curLRUPos not in self.content[self.curIndex]:
            self.content[self.curIndex][self.curLRUPos] = ""    
        self.content[self.curIndex][self.curLRUPos] += line
            
    def writeValues(self, outfile):    
        IniFile.writeHeader(self.name, outfile)
        outfile.write(self.cacheParams)
        
        indexes = self.content.keys()
        indexes.sort()
        for i in indexes:
            for pos in self.content[i]:
                IniFile.writeHeader(self.name+".blk_"+str(i)+"_"+str(pos), outfile)
                outfile.write(self.content[i][pos])

    def merge(self, cacheStates, np):
        assert len(cacheStates) > 0
        
        print "Merging for "+self.name
        
        indexes = cacheStates[0].content.keys()
        indexes.sort()
        perCoreBlocks = len(cacheStates[0].content[0])
        
        for index in indexes:
            for c in cacheStates:
                assert index in c.content
                assert perCoreBlocks == len(c.content[index])
            
            assert index not in self.content
            self.content[index] = {}
            
            for i in range(perCoreBlocks):
                for j in range(np):
                    mergedLRUPos = (i*np)+j
                    assert mergedLRUPos not in self.content[index]
                    self.content[index][mergedLRUPos] = cacheStates[j].content[index][i]
        
        