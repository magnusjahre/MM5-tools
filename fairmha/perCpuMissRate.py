
import pbsconfig
import re
import workloads

np = 4
nb = 4

numMissPattern = re.compile("L2.*misses_per_cpu_[0-9].*")
numAccessPattern = re.compile("L2.*accesses_per_cpu_[0-9].*")
bmPattern = re.compile("-EBENCHMARK=[a-zA-Z0-9]*")

#command = "MISS_RATE"
command = "MISS_PER_MILL_CC"

simlength = pbsconfig.simticks / 1000000

def returnPatterns(instr):
    res = {}
    for m in instr:
        text,val = m.split()[0:2]
        bank,cpu = text.split(".")
        bank = int(bank[len(bank)-1])
        cpu = int(cpu[len(cpu)-1])
                    
        if bank not in res:
            res[bank] = {}
        if cpu not in res[bank]:
            res[bank][cpu] = {}
        res[bank][cpu] = int(val)

    resPerCPU = []
    for i in range(0,np):
        resPerCPU.append(0)

    for i in range(0,np):
        for j in range(0,nb):
            resPerCPU[i] = resPerCPU[i] + res[j][i]

    return resPerCPU


perWorkloadRes = {}

for cmd, config in pbsconfig.commandlines:
    resID = pbsconfig.get_unique_id(config)
    resultfile = None
    try:
        resultfile = open(resID+'/'+resID+'.txt')
    except IOError:
        print "WARNING (quickparse.py):\tCould not find file "+resID+'/'+resID+'.txt'

    if resultfile != None:
        data = resultfile.read()
        missRes = numMissPattern.findall(data)
        accessRes = numAccessPattern.findall(data)

        missesPerCPU = returnPatterns(missRes)
        accessesPerCPU = returnPatterns(accessRes) 

        res = []
        wl = bmPattern.findall(cmd)[0].split('=')[1]
        key = pbsconfig.get_key(cmd, config)


        if command == "MISS_RATE":
            missRate = []
            for i in range(0, np):
                missRate.append(0)

            for i in range(0, np):
                missRate[i] = float(missesPerCPU[i])/float(accessesPerCPU[i])

            res = missRate
        elif command == "MISS_PER_MILL_CC":
            missPerCC = []
            for i in range(0,np):
                missPerCC.append(0)

            for i in range(0,np):
                missPerCC[i] = float(missesPerCPU[i])/float(simlength)
                
            res = missPerCC
        else:
            print "Unknown command"
            exit()

        if key not in perWorkloadRes:
            perWorkloadRes[key] = {}
        if wl not in perWorkloadRes[key]:
            perWorkloadRes[key][wl] = {}
        perWorkloadRes[key][wl] = res


res = {}
for wl in workloads.workloads[np]:
    for k in perWorkloadRes:
        for i in range(0,np):

            bmname = workloads.workloads[np][wl][0][i]

            if k not in res:
                res[k] = {}
            if bmname not in res[k]:
                res[k][bmname] = []

            res[k][bmname].append(perWorkloadRes[k][str(wl)][i])

sortedKeys = res.keys()
sortedKeys.sort()
sortedBMs = res[sortedKeys[0]].keys()
sortedBMs.sort()

width = 20

print "".ljust(width),
for k in sortedKeys:
    print str(k).ljust(width),
print

for bm in sortedBMs:
    print str(bm).ljust(width),
    for k in sortedKeys:
        sum = 0
        for a in res[k][bm]:
            sum = sum + a
        avg = float(sum) / float(len(res[k][bm]))
        
        print str(avg).ljust(width),
    print
