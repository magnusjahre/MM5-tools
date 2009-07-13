
import pbsconfig
import parsemethods
import getInterference
import os

latsum = {}
requests = {}

for cmd,config in pbsconfig.commandlines:
    
    resID = pbsconfig.get_unique_id(config)
    file = open(resID+"/MemoryBusQueueTime.txt")
    lines = file.readlines()
    file.close()

    bm = parsemethods.getBenchmark(cmd)

    key = pbsconfig.get_key(cmd,config)

    latmode = False
    first = False
    for l in lines:
        if l.strip() == "":
            continue
        elif l.startswith("CPU"):
            latmode = not latmode
            first = True
        else:
            if first:
                first = False
                continue
            else:
                data = l.strip().split()
                line = int(data[0].replace(":",""))
                tmpres = []
                for d in data[1:]:
                    tmpres.append(int(d))

                if latmode:
                    if bm not in latsum:
                        latsum[bm] = {}
                    if key not in latsum[bm]:
                        latsum[bm][key] = {}
                    latsum[bm][key][line] = tmpres
                else:
                    if bm not in requests:
                        requests[bm] = {}
                    if key not in requests[bm]:
                        requests[bm][key] = {}
                    requests[bm][key][line] = tmpres

avgres = {}
bms = requests.keys()
bms.sort()
keys = requests[bms[0]].keys()
keys.sort()
lines = requests[bms[0]][keys[0]].keys()
lines.sort()

for b in bms:
    if b not in avgres:
        avgres[b] = {}
    for k in keys:
        if k not in avgres[b]:
            avgres[b][k] = {}
        for l in lines:
            if l not in avgres[b][k]:
                avgres[b][k][l] = [0 for i in range(len(lines))]
            
            for i in range(len(lines)):
                if requests[b][k][l][i] == 0:
                    assert latsum[b][k][l][i] == 0
                    avgres[b][k][l][i] = ""
                else:
                    avgres[b][k][l][i] = getInterference.computeAverage(latsum[b][k][l][i],requests[b][k][l][i])
                


usekey = "2048"

aggavg = [[0 for i in range(len(lines))] for j in range(len(lines))]

for i in range(len(lines)):
    for j in range(len(lines)):
        sum = 0
        cnt = 0
        for b in bms:
            if avgres[b][usekey][i][j] != "":
                sum += avgres[b][usekey][i][j]
                cnt += 1
        if cnt >= 5:
            aggavg[i][j] = int(float(sum) / float(cnt))
        else:
            aggavg[i][j] = -1000

w = 20
print "".ljust(w),
for i in range(len(lines)):
    print str(i).rjust(w),
print

for i in range(len(lines)):
    print str(i).ljust(w),
    for j in range(len(lines)):
        print str(aggavg[i][j]).rjust(w),
    print
