
import IniFile

__metaclass__ = type

class CacheState():

    def __init__(self):
        self.name = ""
        self.cacheParams = ""
        
        self.content = {}
        
        self.curIndex = -1
        self.curLRUPos = -1
    
    def setName(self, name):
        self.name = name
        
    def setCurrentBlock(self, sectionName):
        
        cacheName, blkName = sectionName.split(".")
        assert cacheName == self.name
        
        t, index, LRUPos = blkName.split("_")
        self.curIndex = int(index)
        self.curLRUPos = int(LRUPos)
        
        
    def addContent(self, line):
        if self.curIndex == -1 and self.curLRUPos == -1:
            self.cacheParams += line
            return
        
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

        