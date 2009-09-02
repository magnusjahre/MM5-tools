
import IniFile
from CacheState import CacheState

__metaclass__ = type    

def mergeSharedCache(checkpoints, outfilename):
    
    bankStates = {}
    
    for cp in checkpoints:
        for bank in cp.sharedCaches:
            if bank not in bankStates:
                bankStates[bank] = []
            bankStates[bank].append(cp.sharedCaches[bank])
    
    bankNames = bankStates.keys()
    bankNames.sort()
    newSharedCaches = {}
    for bankName in bankNames:
        mergedState = CacheState(bankName, -1)
        mergedState.merge(bankStates[bankName], len(checkpoints))
        newSharedCaches[bankName] = mergedState
        
    newCheckpoint = Checkpoint()
    newCheckpoint.sharedCaches = newSharedCaches
    newCheckpoint.writeToFile(outfilename)

class Checkpoint():

    def __init__(self):
        self.sharedCaches = None
    
    def createFromFile(self, filename, outfilename, newCoreID):
        self.sharedCaches = IniFile.read(filename, outfilename, newCoreID)
        
    def writeToFile(self, filename):
        IniFile.write(filename, self.sharedCaches)
        
        
