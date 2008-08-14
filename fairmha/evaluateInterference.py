
import sys
import pbsconfig
import re
import deterministic_fw_wls as fair_wls
import single_core_fw as single_wls

bmPattern = re.compile("-EBENCHMARK=[a-zA-Z0-9]*")
startPattern = re.compile("^[0-9]:")
ipcPattern = re.compile("detailedCPU[0-9].COM:IPC.*")
idPattern = re.compile("[0-9]+")

np = 4
banks = 4

def getBenchmark(cmd):
    res = bmPattern.findall(cmd)
    bm = res[0].split('=')[1]
    return bm

def getBMFromKey(id):
    idSplit = id.split('_')
    return idSplit[1]

def getKeyFromID(id):
    idSplit = id.split('_')
    restStr = idSplit[2]
    for n in idSplit[3:]:
        restStr = restStr + "_" + n
    return restStr

def getMatrix(infile):
    matrix = []
    for i in range(np):
        matrix.append([])

    findCnt = 0
    for l in infile:
        res = startPattern.findall(l)
        if res != []:
           vals = l.split() 
           findCnt = findCnt+1
           for v in vals[1:]:
               matrix[int(res[0][0])].append(int(v))
        
        if findCnt == np:
            return matrix

def getIPCs(resIDs, results, useKey):
    for resID in resIDs:
        bm = getBMFromKey(resID)
        wlNum = int(idPattern.findall(bm)[0])
        key = getKeyFromID(resID)
    
        infile = None
        try:
            infile = open(resID+'/'+resID+'.txt')
        except IOError:
            sys.stderr.write("WARNING: could not open file for experiment "+resID+"!\n")
        
        if infile != None:
            if bm not in results:
                results[bm] = {}

            if useKey:
                if key not in results:
                    results[bm][key] = {}

            res = ipcPattern.findall(infile.read())
            for r in res:
                resAr = r.split()
                if len(res) == 1:
                    assert not useKey
                    results[bm] = float(resAr[1])
                else:
                    id = int(idPattern.findall(resAr[0])[0])
                    bmName = fair_wls.workloads[wlNum][0][id]
                    fw = fair_wls.workloads[wlNum][1][id]

                    offset = fw - 1000000000
                    bmName = bmName+str(offset / 20000000)

                    if useKey:
                        results[bm][key][bmName] = float(resAr[1])
                    else:
                        results[bm][bmName] = float(resAr[1])
                    
def getRatios(data, baseline, alone):
    ratios = {}
    for wl in data:
        for key in data[wl]:
            for bm in data[wl][key]:
                if wl not in ratios:
                    ratios[wl] = {}
                if key not in ratios[wl]:
                    ratios[wl][key] = {}

                sharedIPC = data[wl][key][bm]
                baselineIPC = -10000000.0
                if alone:
                    baselineIPC = baseline[bm]
                else:
                    baselineIPC = baseline[wl][bm]

                ratios[wl][key][bm] = sharedIPC / baselineIPC

    return ratios
                


staticIDs = []
for cmd, config in pbsconfig.staticcommands:
    staticIDs.append(pbsconfig.get_unique_id(config))

aloneIDs = []
for cmd, config in pbsconfig.alonecommands:
    aloneIDs.append(pbsconfig.get_unique_id(config))


interferenceRes = {}
sharedIPCs = {}
runIDs = []
for cmd, config in pbsconfig.commandlines:
    resID = pbsconfig.get_unique_id(config)
    bm = getBenchmark(cmd)
    key = pbsconfig.get_key(cmd, config)
    
    if resID not in staticIDs and resID not in aloneIDs:
        infile = None
        try:
            infile = open(resID+'/interferenceStats.txt')
        except IOError:
            sys.stderr.write("WARNING: could not open file for experiment "+resID+"!\n")
        
        if infile != None:
            runIDs.append(resID)

            if bm not in interferenceRes:
                interferenceRes[bm] = {}
                
            if key not in interferenceRes:
                interferenceRes[bm][key] = {}
            interferenceRes[bm][key]["ic"] = getMatrix(infile)

            for i in range(banks):
                interferenceRes[bm][key]["L2bank"+str(i)+"BW"] = getMatrix(infile)
                interferenceRes[bm][key]["L2bank"+str(i)+"CP"] = getMatrix(infile)

            interferenceRes[bm][key]["Mem"+str(i)+"Bus"] = getMatrix(infile)
            interferenceRes[bm][key]["Mem"+str(i)+"Con"] = getMatrix(infile)
            interferenceRes[bm][key]["Mem"+str(i)+"HtM"] = getMatrix(infile)
   
runIPCs = {}
getIPCs(runIDs, runIPCs, True)
staticIPCs = {}
getIPCs(staticIDs, staticIPCs, False)
aloneIPCs = {}
getIPCs(aloneIDs, aloneIPCs, False)

staticRatios = getRatios(runIPCs, staticIPCs, False)
aloneRatios = getRatios(runIPCs, aloneIPCs, True)


