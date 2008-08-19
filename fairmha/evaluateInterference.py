
import sys
import pbsconfig
import re
import deterministic_fw_wls as fair_wls
import single_core_fw as single_wls

#MPB best 1,1,66,46,1,0
#SPB best 1,1,1,21,1,0

icWeights = [1] #[1]
L2BWWeights = [1] #[1]
#L2CapWeights = [0.01, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 5, 10, 20, 50, 100]
L2CapWeights = [66]
BusBusWeights = [46] #[40]
#BusConflictWeights = [10, 20, 30, 40, 60, 80, 100, 120, 140, 160, 200]
BusConflictWeights = [1]
BusHtMWeights = [0]

short = 11
long = 202

#for i in range(1,2):
#    icWeights.append(i)

#for i in range(1,2):
#    L2BWWeights.append(i)

#for i in range(1,102)[::5]:
#    BusBusWeights.append(i)

#for i in range(1,long)[::5]:
#    L2CapWeights.append(i)

#for i in range(1,long)[::5]:
#    BusConflictWeights.append(i)

RESULT_KEY = "Conventional_RDFCFS_ConventionalCB"

bmPattern = re.compile("-EBENCHMARK=[a-zA-Z0-9]*")
startPattern = re.compile("^[0-9]:")
ipcPattern = re.compile("detailedCPU[0-9].COM:IPC.*")
stallPattern = re.compile("detailedCPU[0-9].COM:total_ticks_stalled_for_memory.*")
instCountPattern = re.compile("detailedCPU[0-9].COM:count.*")
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

def getWorkload(wlNum):
    bms = ["" for i in range(np)]
    
    for i in range(np):
        bmName = fair_wls.workloads[wlNum][0][i]
        fw = fair_wls.workloads[wlNum][1][i]

        offset = fw - 1000000000
        bmName = bmName+str(offset / 20000000)
        bms[i] = bmName
    return bms

def getPattern(resIDs, results, useKey, pattern):
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

            res = pattern.findall(infile.read())
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

def addMatrix(ipKey, cost, outMat, wl, resKey):
    for i in range(np):
        for j in range(np):
            outMat[i][j] = outMat[i][j] + (cost * interferenceRes[wl][resKey][ipKey][i][j])

def computeIPs(ic, l2bw, l2cap, bus, conflict, htm):

    allIPs = {}

    for wl in interferenceRes:

        tmpIPs = [[0 for x in range(np)] for x in range(np)]
        addMatrix("ic", ic, tmpIPs, wl, RESULT_KEY)

        for i in range(banks):            
            addMatrix("L2bank"+str(i)+"BW", l2bw, tmpIPs, wl, RESULT_KEY)        
            addMatrix("L2bank"+str(i)+"CP", l2cap, tmpIPs, wl, RESULT_KEY)
            
        addMatrix("MemBus", bus, tmpIPs, wl, RESULT_KEY)
        addMatrix("MemCon", conflict, tmpIPs, wl, RESULT_KEY)
        addMatrix("MemHtM", htm, tmpIPs, wl, RESULT_KEY)

        allIPs[wl] = [0 for x in range(np)]
        for i in range(np):
            for j in range(np):
                allIPs[wl][i] = allIPs[wl][i] + tmpIPs[i][j]
        
    return allIPs

def normalizeIPs(IPs):
    normIPs = {}
    for wl in IPs:
        normIPs[wl] = [0 for x in range(np)]
        maxVal = float(max(IPs[wl]))
        for i in range(np):
            normIPs[wl][i] = float(IPs[wl][i]) / maxVal
    return normIPs

def evaluateWeights(ic, l2bw, l2cap, bus, conflict, htm, bestMPB, bestSPB):

    print "Evaluating "+str(ic)+", "+str(l2bw)+", cap cost "+str(l2cap)+", "+str(bus)+", bus conflict "+str(conflict)

    ips = computeIPs(ic, l2bw, l2cap, bus, conflict, htm)

    cnt = 0
    spbDiffSum = 0
    mpbDiffSum = 0
    for wl in ips:
        bms = getWorkload(int(wl[4:6]))
        
        predFair = float(min(ips[wl])) / float(max(ips[wl]))
        spbFair = float(min(aloneRatios[wl][RESULT_KEY].itervalues())) / float(max(aloneRatios[wl][RESULT_KEY].itervalues()))
        mpbFair = float(min(staticRatios[wl][RESULT_KEY].itervalues())) / float(max(staticRatios[wl][RESULT_KEY].itervalues()))
        spbDiff = predFair / spbFair
        mpbDiff = predFair /mpbFair
        
        print wl+": SPB diff = "+str(spbDiff)+", MPB diff = "+str(mpbDiff)

        cnt = cnt + 1
        spbDiffSum = spbDiffSum + spbDiff
        mpbDiffSum = mpbDiffSum + mpbDiff

    mpbOffset = abs((mpbDiffSum/cnt)-1)
    spbOffset = abs((spbDiffSum/cnt)-1)

    print "AVERAGE: SPB = "+str(spbOffset)+", MPB = "+str(mpbOffset)

    if mpbOffset < bestMPB[0]:
        print "New best MTB!"
        bestMPB = [mpbOffset, ic, l2bw, l2cap, bus, conflict]

    if spbOffset < bestSPB[0]:
        print "New best STB!"
        bestSPB = [spbOffset, ic, l2bw, l2cap, bus, conflict]

    print

    return (bestMPB, bestSPB)

        

def printStats(ic, l2bw, l2cap, bus, conflict, htm):
    baseName = str(ic)+"_"+str(l2bw)+"_"+str(l2cap)+"_"+str(bus)+"_"+str(conflict)+"_"+str(htm)
    ipFile = open("ips_"+baseName+".txt", "w")
    spbFile = open("spb_"+baseName+".txt", "w")
    mpbFile = open("mpb_"+baseName+".txt", "w")
    stallFile = open("spb_stall_"+baseName+".txt", "w")
    mpbStallFile = open("mpb_stall_"+baseName+".txt", "w")

    ips = computeIPs(ic, l2bw, l2cap, bus, conflict, htm)
    wls = ips.keys()
    wls.sort()

    for wl in wls:
        ipFile.write(str(wl).ljust(20))
        spbFile.write(str(wl).ljust(20))
        mpbFile.write(str(wl).ljust(20))
        stallFile.write(str(wl).ljust(20))
        mpbStallFile.write(str(wl).ljust(20))

        for i in range(np):
            ipFile.write(str(ips[wl][i]).rjust(20))
        ipFile.write("\n")

        for bm in getWorkload(int(wl[4:6])):
            mpbFile.write(str(staticRatios[wl][RESULT_KEY][bm]).rjust(20))
        mpbFile.write("\n")

        for bm in getWorkload(int(wl[4:6])):
            spbFile.write(str(aloneRatios[wl][RESULT_KEY][bm]).rjust(20))
        spbFile.write("\n")

        for bm in getWorkload(int(wl[4:6])):
            stallFile.write(str(spbStallRatios[wl][RESULT_KEY][bm]).rjust(20))
        stallFile.write("\n")

        for bm in getWorkload(int(wl[4:6])):
            mpbStallFile.write(str(mpbStallRatios[wl][RESULT_KEY][bm]).rjust(20))
        mpbStallFile.write("\n")

def divideRes(divisor, dividend, dims):
    assert dims >= 1 and dims <= 3
    for wl in divisor:
        if dims == 1:
            divisor[wl] = divisor[wl] / dividend[wl]
        else:
            for a in divisor[wl]:
                if dims == 3:
                    for b in divisor[wl][a]:
                        divisor[wl][a][b] = divisor[wl][a][b] / dividend[wl][a][b]
                else:
                    divisor[wl][a] = divisor[wl][a] / dividend[wl][a]
    return divisor
    

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

            interferenceRes[bm][key]["MemBus"] = getMatrix(infile)
            interferenceRes[bm][key]["MemCon"] = getMatrix(infile)
            interferenceRes[bm][key]["MemHtM"] = getMatrix(infile)
   
runIPCs = {}
getPattern(runIDs, runIPCs, True, ipcPattern)
staticIPCs = {}
getPattern(staticIDs, staticIPCs, False, ipcPattern)
aloneIPCs = {}
getPattern(aloneIDs, aloneIPCs, False, ipcPattern)

runStalls = {}
getPattern(runIDs, runStalls, True, stallPattern)
runInsts = {}
getPattern(runIDs, runInsts, True, instCountPattern)
staticStalls = {}
getPattern(staticIDs, staticStalls, False, stallPattern)
staticInsts = {}
getPattern(staticIDs, staticInsts, False, instCountPattern)
aloneStalls = {}
getPattern(aloneIDs, aloneStalls, False, stallPattern)
aloneInsts = {}
getPattern(aloneIDs, aloneInsts, False, instCountPattern)

runMCPI = divideRes(runStalls, runInsts, 3)
staticMCPI = divideRes(staticStalls, staticInsts, 2)
aloneMCPI = divideRes(aloneStalls, aloneInsts, 1)

staticRatios = getRatios(runIPCs, staticIPCs, False)
aloneRatios = getRatios(runIPCs, aloneIPCs, True)
mpbStallRatios = getRatios(runMCPI, staticMCPI, False)
spbStallRatios = getRatios(runMCPI, aloneMCPI, True)


bestMPB = [1000000.0, -1, -1, -1, -1, -1]
bestSPB = [1000000.0, -1, -1, -1, -1, -1]

for ic in icWeights:
    for l2bw in L2BWWeights:
        for l2cap in L2CapWeights:
            for bus in BusBusWeights:
                for conflict in BusConflictWeights:
                    for htm in BusHtMWeights:
                        bestMPB, bestSPB = evaluateWeights(ic, l2bw, l2cap, bus, conflict, htm, bestMPB, bestSPB)
                        printStats(ic, l2bw, l2cap, bus, conflict, htm)


print "Best configurations"
print "MPB: "+str(bestMPB)
print "SPB: "+str(bestSPB)
print
