
import sys
import re

CACHE_BANK_COUNT = 4

file = None
try:
    file = open(sys.argv[1])
except:
    print "File not found, quitting"
    sys.exit()

wlOfBm = sys.argv[1].split('/')[0].split('_')[1]

np = -1
try:
    np = int(sys.argv[2])
except:
    print "No processor count given, quitting"
    sys.exit()

def getCPUID(resStr):
    res = cpuidPattern.findall(resStr)
    if res == []:
        return 0

    assert len(res) <= 1
    return int(res[0].split("_")[1])

def getBankID(resStr):
    res = bankidPattern.findall(resStr)
    assert len(res) == 1
    return int(res[0][6])

def getCacheValue(key, i, b, data, outData):
    curIndex = i + (np*b)
    cpuid = getCPUID(data[curIndex])
    bankid = getBankID(data[curIndex])
    if bankid not in outData[key]:
        outData[key][bankid] = {}
    assert cpuid not in outData[key][bankid]
    outData[key][bankid][cpuid] = float(data[curIndex].split()[1])


def getBusValue(key, i, data, outData):
    cpuid = getCPUID(data[i])
    assert cpuid not in outData[key]
    outData[key][cpuid] = float(data[i].split()[1])

def getCPUValue(key, i, data, outData):
    cpuid = int(data[i][11])
    assert cpuid not in outData[key]
    outData[key][cpuid] = float(data[i].split()[1])

cacheMissPattern = re.compile("L2Bank..misses_per_cpu_[0-9].*")
cacheAccessPattern = re.compile("L2Bank..accesses_per_cpu_[0-9].*")
busAccessPattern = re.compile("toMemBus.accesses_per_cpu_[0-9].*")
busHitPattern = re.compile("toMemBus.page_hits_per_cpu_[0-9].*")

if np == 1:
    cacheMissPattern = re.compile("L2Bank..misses_per_cpu.*")
    cacheAccessPattern = re.compile("L2Bank..accesses_per_cpu.*")
    busAccessPattern = re.compile("toMemBus.accesses_per_cpu.*")
    busHitPattern = re.compile("toMemBus.page_hits_per_cp.*")

stallPattern = re.compile("detailedCPU..COM:total_ticks_stalled_for_memory.*")
committPattern = re.compile("detailedCPU..COM:count.*")
cpuidPattern = re.compile("cpu_[0-9]")
bankidPattern = re.compile("L2Bank[0-9]")

text = file.read()

cacheAccesses = cacheAccessPattern.findall(text)
cacheMisses = cacheMissPattern.findall(text)
busHits = busHitPattern.findall(text)
busAccesses = busAccessPattern.findall(text)
cpuCommits = committPattern.findall(text)
cpuStalls = stallPattern.findall(text)

assert np * CACHE_BANK_COUNT == len(cacheAccesses)
assert np * CACHE_BANK_COUNT == len(cacheMisses)

cacheData = {"accesses":{}, "misses":{}}
busData = {"accesses":{}, "hits":{}}
cpuData = {"committed":{}, "stalled":{}}

for i in range(np):
    for b in range(CACHE_BANK_COUNT):
        getCacheValue("accesses", i, b, cacheAccesses, cacheData)
        getCacheValue("misses", i, b, cacheMisses, cacheData)

for i in range(np):
    getBusValue("accesses", i, busAccesses, busData)
    getBusValue("hits", i, busHits, busData)

for i in range(np):
    getCPUValue("committed", i, cpuCommits, cpuData)
    getCPUValue("stalled", i, cpuStalls, cpuData)


print
print "Per CPU Cache Miss rates for "+str(wlOfBm)+":"
for b in range(CACHE_BANK_COUNT):
    print
    print "Cache bank "+str(b)+":"
    for i in range(np):
        tmp = cacheData["misses"][b][i] / cacheData["accesses"][b][i]
        print ("CPU"+str(i)).ljust(10)+str(tmp).rjust(20)

print
print "Per CPU Memory Page Miss rates:"
for i in range(np):
    tmp = -1
    try:
        tmp = (busData["accesses"][i] - busData["hits"][i]) / busData["accesses"][i]
    except:
        tmp = -1

    if tmp != -1:
        print ("CPU"+str(i)).ljust(10)+str(tmp).rjust(20)
    else:
        print ("CPU"+str(i)).ljust(10)+str("No accesses").rjust(20)

print
print "Per CPU Stall cycles and Miss Cycles per Instruction (MCPI):"
for i in range(np):
    tmp = cpuData["stalled"][i] / cpuData["committed"][i]
    print ("CPU"+str(i)).ljust(10)+str(cpuData["stalled"][i]).rjust(20)+str(tmp).rjust(20)

print
