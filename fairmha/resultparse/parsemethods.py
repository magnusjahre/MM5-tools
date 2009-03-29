
import re
import sys

# Globals

bmPattern = re.compile("-EBENCHMARK=[a-zA-Z0-9]*")
instPattern = re.compile(" [0-9]+ ")
intPattern = re.compile("[0-9]+")
committedPattern = re.compile("[0-9]+ committed")

# Procedures

def getBenchmark(cmd):
    res = bmPattern.findall(cmd)
    bm = res[0].split('=')[1]
    return bm

def getSwitchCounts(fileID):
    switchfile = None
    name = fileID+"/cpuSwitchInsts.txt"
    try:
        switchfile = open(name)
    except IOError:
        sys.stderr.write("WARNING:\tCould not find file "+name+'\n')
        
    insts = {}
    if switchfile != None:
        for line in switchfile.readlines():
            res = instPattern.findall(line)
            cpuID = int(line.split(":")[0][9])
            insts[cpuID] = int(res[0])
            
    return insts

def checkAvgLatDriftError(idDict):
    
    minDiff = 0
    maxDiff = 0
    
    for wl in idDict:
        sharedID, aloneIDs = idDict[wl]
        
        sharedStarts = getSwitchCounts(sharedID)
        if sharedStarts != {}:
            cpuID = 0
            for a in aloneIDs:
                starts = getSwitchCounts(a)
                diff = (float(starts[0]) / float(sharedStarts[cpuID])) - 1
                if diff > maxDiff:
                    maxDiff = diff
                if diff < minDiff:
                    minDiff = diff
                
                cpuID += 1

    sys.stderr.write("Drift errors: "+str(maxDiff)+", "+str(minDiff)+"\n")

def getAloneDrift(sharedid, aloneids):
    
    try:
        sharedSwitch = open(sharedid+"/cpuSwitchInsts.txt")
        sSwitchLines = sharedSwitch.readlines()
        sharedSwitch.close()
    except:
        e = ["N/A" for i in range(len(aloneids))]
        return (e,e)

    sharedCom = [0 for i in range(len(aloneids))]
    
    for l in sSwitchLines:
        stmp = l.split(":")
        
        idRes = intPattern.findall(stmp[0])
        assert len(idRes) == 1
        id = int(idRes[0])
        
        comRes = committedPattern.findall(stmp[1])
        assert len(comRes) == 1
        com = int(comRes[0].split(" ")[0])

        sharedCom[id] = com

    aloneCom = [0 for i in range(len(aloneids))]
    i = 0
    for aid in aloneids:
        aswitch = open(aid+"/cpuSwitchInsts.txt")
        alines = aswitch.readlines()
        aswitch.close()

        assert len(alines) == 1
        comRes = committedPattern.findall(alines[0])
        assert len(comRes) == 1
        com = int(comRes[0].split(" ")[0])
        
        aloneCom[i] = com
        i += 1

    error = [0 for i in range(len(aloneids))]
    diff = [0 for i in range(len(aloneids))]
    for i in range(len(sharedCom)):
        error[i] = ((float(sharedCom[i]) - float(aloneCom[i])) / float(aloneCom[i])) * 100
        diff[i] = sharedCom[i] - aloneCom[i]

    return (error,diff)

def readInterferenceTraceSummary(filename):
    
    first = True
    colnames = []
    data = []
    minkey = 0
    maxkey = 0

    filename = open(filename)

    for l in filename:
        if first:
            colnames = l.split()[1:]
            first = False
            continue

        splitstr = l.split()
    
        key = int(splitstr[0])

        if key < minkey:
            minkey = key

        if key > maxkey:
            maxkey = key

        tmpdata = []
        for i in splitstr[1:]:
            if i == "-":
                tmpdata.append(-1)
            else:
                tmpdata.append(float(i))

        data.append((key, tmpdata))

    filename.close()

    return (data, colnames, minkey, maxkey)

def getFilenames(configobject, cmd, config, np):
    sharedID = configobject.get_unique_id(config)
    shName = sharedID+'/'+sharedID+'.txt'
    wl = getBenchmark(cmd)
    
    aloneIDs = []
    aloneNames = []
    for i in range(np):
        tmpaparams = configobject.get_alone_params(wl, i, config)
        tmpID = configobject.get_unique_id(tmpaparams)
        aloneIDs.append(tmpID)
        aloneNames.append(tmpID+'/'+tmpID+'.txt')

    return shName, aloneNames

def getAllFilenames(configobject, np):
    
    allFilenames = {}
    
    for cmd, config in configobject.commandlines:
        shName, aloneNames = getFilenames(configobject, cmd, config, np)
        wl = getBenchmark(cmd)
        key = configobject.get_key(cmd, config)

        if wl not in allFilenames:
            allFilenames[wl] = {}
            
        assert key not in allFilenames[wl]
        allFilenames[wl][key] = (shName, aloneNames)
        
    return allFilenames

def findValues(patternString, filename):
    pattern = re.compile(patternString)
    
    file = open(filename)
    text = file.read()
    file.close()
    
    results = pattern.findall(text)
    
    retval = {}
    for r in results:
         tmp = r.split()
         cpuid = int(intPattern.findall(tmp[0])[0])
         value = float(tmp[1])
         
         retval[cpuid] = value
    
    return retval
    
    