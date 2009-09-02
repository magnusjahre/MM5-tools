
import IniFile

__metaclass__ = type    

class Checkpoint():

    def __init__(self):
        self.sharedCaches = None
    
    def createFromFile(self, filename, outfilename, newCoreID):
        self.sharedCaches = IniFile.read(filename, outfilename, newCoreID)
        
    def mergeSharedCache(self, checkpoints):
        print "Merge not impl"
        
    def writeToFile(self, filename):
        IniFile.write(filename, self.sharedCaches)
        
        
