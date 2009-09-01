
import IniFile
import IniFileSection

__metaclass__ = type

class Checkpoint():

    def __init__(self):
        self.sections = None
        self.iniFile = IniFile.IniFile()
    
    def createFromFile(self, filename):
        self.sections = self.iniFile.read(filename)
        
    def createFromCheckpoints(self, checkpoints):
        print "Merge not impl"
        
    def writeToFile(self, filename):
        self.iniFile.write(filename, self.sections)
        
        