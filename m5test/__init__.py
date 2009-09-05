
import re
import os

def findStatsPattern(patternString, statsfilename):
    pattern = re.compile(patternString)

    statsfile = open(statsfilename)
    res = pattern.findall(statsfile.read())
    statsfile.close()

    resDict = {}
    for r in res:
        splitted = r.split()
        simObj = splitted[0].split(".")[0]
        value = float(splitted[1])
        
        assert simObj not in resDict
        resDict[simObj] = value

    return resDict


def getWorkspaceRoot():
    envVarName = "M5TOOLSROOT" 
    if envVarName in os.environ:
        return os.environ[envVarName]
    return "/home/jahre/workspace/m5sim-tools/"