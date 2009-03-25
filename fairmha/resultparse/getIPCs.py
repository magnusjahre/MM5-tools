
import sys
import re
import pbsconfig
import deterministic_fw_wls as workloads

file = None
try:
    file = open(sys.argv[1])
except:
    print "File not found, quitting"
    sys.exit()

wl = sys.argv[1].split('/')[0].split('_')[1]

ipcPattern = re.compile("detailedCPU..COM:IPC.*")
idPattern = re.compile("[0-9]+")

wlID = int(idPattern.findall(wl)[0])

text = file.read()

ipcs = ipcPattern.findall(text)

cpuData = {"shared":{}, "alone":{}}


for t in ipcs:
    splitted = t.split()
    cpuid = int(idPattern.findall(splitted[0])[0])
    ipc = float(splitted[1])
    cpuData["shared"][cpuid] = ipc

curWl = workloads.workloads[wlID][0]
wlDict = {}

wlID = {}
transWl = []
for w in curWl:
    if w not in wlDict:
        wlDict[w] = 0
    else:
        wlDict[w] = wlDict[w] + 1

    transWl.append(w+str(wlDict[w]))

fileIDs = {}
for cmd, params in pbsconfig.alonecommands:
    fileid = pbsconfig.get_unique_id(params)
    bm = fileid.split('_')[1]
    if bm in transWl:
        fileIDs[bm] = fileid

pos = 0
for bm in transWl:
    bmFile = open(fileIDs[bm]+"/"+fileIDs[bm]+".txt")
    bmText = bmFile.read()
    ipc =float(ipcPattern.findall(bmText)[0].split()[1])
    cpuData["alone"][pos] = ipc
    pos = pos + 1

width = 20

print
print "IPCs for workload "+wl+":"
print
print "Benchmark".ljust(width)+"Shared".ljust(width)+"Alone".ljust(width)+"Ratio".ljust(width)
for i in range(len(cpuData["shared"])):
    print transWl[i].ljust(width) \
          + str(cpuData["shared"][i]).ljust(width) \
          + str(cpuData["alone"][i]).ljust(width) \
          + str(cpuData["shared"][i] / cpuData["alone"][i]).ljust(width)

print
