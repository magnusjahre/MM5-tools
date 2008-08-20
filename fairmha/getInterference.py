
import sys
import re

np = 4

filename = sys.argv[1]
file = open(filename)
filetext = file.read()
file.close()

def getResult(r, array):
    value = int(r.split()[1])
    text = r.split()[0]
    cpuID = int(text.split("_")[3])
    array[cpuID] += value
    return array

icReqsPattern = re.compile("interconnect.master_requests.*")

l2CapPattern = re.compile("L2Bank[0-9].cpu_capacity_interference_0-9].*")

patterns = {
"ic":re.compile("interconnect.cpu_interference_cycles_[0-9].*"),
"l2BW": re.compile("L2Bank[0-9].cpu_interference_cycles_[0-9].*"),
"bus": re.compile("toMemBus.cpu_interference_bus_[0-9].*"),
"busConflict": re.compile("toMemBus.cpu_interference_conflict_[0-9].*"),
"busHtM": re.compile("toMemBus.cpu_interference_htm_[0-9].*")
}

accessPatterns = {
"misses": re.compile("L1[di]caches[0-9].overall_misses.*"),
"lat": re.compile("L1[di]caches[0-9].overall_miss_latency.*"),
"resp": re.compile("L1[di]caches[0-9].miss_responses_recv.*"),
"wbs": re.compile("L1[di]caches[0-9].writebacks.*"),
"mshr": re.compile("L1[di]caches[0-9].overall_mshr_hits.*")
}

totalInterference = [0 for i in range(np)]

for p in patterns:
    res = patterns[p].findall(filetext)
    for r in res:
        totalInterference = getResult(r, totalInterference)
        
capacityInterference = [0 for i in range(np)]
capacityRes = l2CapPattern.findall(filetext)
for r in capacityRes:
    capacityInterference = getResult(r, capacityInterference)


totLat = [0 for i in range(np)]
readReqs = [0 for i in range(np)]
numResps = [0 for i in range(np)]
numWbs = [0 for i in range(np)]
numMSHRHits = [0 for i in range(np)]
for p in accessPatterns:
    res = accessPatterns[p].findall(filetext)
    for r in res:
        value = float(r.split()[1])
        text = r.split()[0]
        cpuID = int(text[9])
        if p == "misses":
            readReqs[cpuID] += value
        elif p == "lat":
            totLat[cpuID] += value
        elif p == "resp":
            numResps[cpuID] += value
        elif p == "wbs":
            numWbs[cpuID] += value
        elif p == "mshr":
            numMSHRHits[cpuID] += value
        else:
            assert False

missSum = float(sum(readReqs))+float(sum(numWbs))-float(sum(numMSHRHits))
IandDmissRes = icReqsPattern.findall(filetext)
IandDmisses = float(IandDmissRes[0].split()[1])
iError = 1 - (missSum / IandDmisses)

allReqs = [0 for i in range(np)]
for i in range(np):
    allReqs[i] = readReqs[i] + numWbs[i] - numMSHRHits[i]

print
print "Interference summary for file "+filename
print
print "Bandwidth interference in cycles:"
for i in range(np):
    print "CPU "+str(i)+": "+str(totalInterference[i])+", "+str(float(totalInterference[i])/allReqs[i])+" per req"
print
print "Capacity interference in evictions:"
for i in range(np):
    print "CPU "+str(i)+": "+str(capacityInterference[i])
print
print
print "Interference due to blocking:"
for i in range(np):
    print "CPU "+str(i)+": N/A"
print
print "Average latencies"
for i in range(np):
   print "CPU "+str(i)+": "+str(totLat[i]/allReqs[i])+", "+str(allReqs[i])+" requests, error = "+str((readReqs[i]/numResps[i])-1)
print
print "Estimated error (requests not taken into account) "+str(iError)
print
