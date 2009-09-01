
import IniFile
import IniFileSection

__metaclass__ = type

class Checkpoint():

    def __init__(self):
        self.sections = None
    
    def prepareOutputFile(self, outfilename):
        of = open(outfilename, "w")
        of.write("")
        of.flush()
        of.close()
    
    def createFromFile(self, filename, outfilename, newCoreID):
        self.sections = IniFile.read(filename, outfilename, newCoreID)
        
    def mergeSharedCache(self, checkpoints):
        print "Merge not impl"
        
    def writeToFile(self, filename):
        IniFile.write(filename, self.sections)
        
        