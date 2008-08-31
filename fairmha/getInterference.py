
import sys
import re

try:
    filename = sys.argv[1]
    np = int(sys.argv[2])
except:
    print "Usage: prog file np"
    sys.exit(0)

file = open(filename)
filetext = file.read()
file.close()

def getResult(r, array):
    value = int(r.split()[1])
    text = r.split()[0]
    cpuID = int(text.split("_")[3])
    array[cpuID] += value
    return array

#icReqsPattern = re.compile("interconnect.master_requests.*")

l2CapPattern = re.compile("L2Bank[0-9].cpu_capacity_interference_0-9].*")

patterns = {
"ic":re.compile("interconnect.cpu_interference_cycles_[0-9].*"),
"l2BW": re.compile("L2Bank[0-9].cpu_interference_cycles_[0-9].*"),
"bus": re.compile("toMemBus.cpu_interference_bus_[0-9].*"),
"busConflict": re.compile("toMemBus.cpu_interference_conflict_[0-9].*"),
"busHtM": re.compile("toMemBus.cpu_interference_htm_[0-9].*")
}

accessPatterns = {
"misses": re.compile("L1[di]caches[0-9].overall_mshr_misses.*"),
"lat": re.compile("L1[di]caches[0-9].overall_mshr_miss_latency.*")
#"wbs": re.compile("L1[di]caches[0-9].writebacks.*")
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


mshrMissTotLat = [0 for i in range(np)]
mshrMisses = [0 for i in range(np)]
numWbs = [0 for i in range(np)]
numMSHRHits = [0 for i in range(np)]
for p in accessPatterns:
    res = accessPatterns[p].findall(filetext)
    for r in res:
        value = float(r.split()[1])
        text = r.split()[0]
        cpuID = int(text[9])
        if p == "misses":
            mshrMisses[cpuID] += value
        elif p == "lat":
            mshrMissTotLat[cpuID] += value
#        elif p == "wbs":
#            numWbs[cpuID] += value
        else:
            assert False


print
print "Interference summary for file "+filename
print
print "Bandwidth interference in cycles:"
for i in range(np):
    print "CPU "+str(i)+": "+str(totalInterference[i])+", "+str(float(totalInterference[i])/mshrMisses[i])+" per req ("+str(mshrMisses[i])+" reqs)"
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
   print "CPU "+str(i)+": "+str(mshrMissTotLat[i]/mshrMisses[i])+", "+str(mshrMisses[i])+" requests"
print

