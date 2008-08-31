
import re

committedPattern = re.compile(".*COM:count.*")

def getCommittedInsts(filename, procID, printOutput):
    file = open(filename)
    text = file.read()
    comRes = committedPattern.findall(text)
    iCount = int(comRes[procID].split()[1])
    if printOutput:
        print iCount
    return iCount
    
