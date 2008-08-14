
import sys
import pbsconfig
import re

bmPattern = re.compile("-EBENCHMARK=[a-zA-Z0-9]*")
startPattern = re.compile("^[0-9]:")

np = 4
banks = 4

def getBenchmark(cmd):
    res = bmPattern.findall(cmd)
    bm = res[0].split('=')[1]
    return bm

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


staticIDs = []
for cmd, config in pbsconfig.staticcommands:
    staticIDs.append(pbsconfig.get_unique_id(config))

aloneIDs = []
for cmd, config in pbsconfig.alonecommands:
    aloneIDs.append(pbsconfig.get_unique_id(config))


interferenceRes = {}
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
            
print interferenceRes

