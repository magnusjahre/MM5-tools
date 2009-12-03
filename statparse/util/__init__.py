
import sys
import os

def fatal(message):
    print
    print "ERROR: "+message
    print
    sys.exit(-1)
    
def warn(message):
    print "Warning: "+message
    
    
def getExperimentDirs(np, includeParams):
    if not os.path.exists("pbsconfig.py"):
        fatal("pbsconfig.py not found!")
    
    pbsconfig = __import__("pbsconfig")
    configobj = pbsconfig.config

    paramDict = {}
    if includeParams != "":
        import statparse.experimentConfiguration as expconf
        paramDict, paramSpec = expconf.parseParameterString(includeParams)

    experimentdirs = []
    for cmd, shparams in pbsconfig.commandlines:
        
        expNp = configobj.getParam(shparams, "np")
        if expNp != np:
            continue
        
        includeDirs = True
        for includeParam in paramDict:
            paramval = configobj.getNamedParamVal(shparams, includeParam)
            if paramval != paramDict[includeParam]:
                includeDirs = False
        
        if includeDirs:
            wl = configobj.getParam(shparams, "wl")
            sharedFileID = configobj.getFileIdentifier(shparams)
    
            aloneFileIDs = []
            for i in range(np):
                aparams = configobj.getSPMParameters(shparams, wl, i)
                aloneFileID = configobj.getFileIdentifier(aparams)
                aloneFileIDs.append(aloneFileID)
            
            experimentdirs.append( (wl, sharedFileID, aloneFileIDs) )
    
    return experimentdirs