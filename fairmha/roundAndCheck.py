
import tmp_workloads

np = 4
wls = range(1,11)

allCnt = {}

baseFF = 1000000000
FFincrement = 20000000
outFileName = "deterministic_fw_wls.py"
singleCoreFileName = "single_core_fw.py"

print
print "Generating fast-forward configuration suitable for comparison with single core experiments"
print

newWls = {}

for wl in wls:
    names = tmp_workloads.workloads[np][wl][0]
    cntDict = {}
    for n in names:
        if n not in cntDict:
            cntDict[n] = 0
        cntDict[n] = cntDict[n] + 1

    for bm in cntDict:
        if bm not in allCnt:
            allCnt[bm] = cntDict[bm]

        if allCnt[bm] < cntDict[bm]:
            allCnt[bm] = cntDict[bm]

    newWls[wl] = ([],[])
    for bm in cntDict:
        for i in range(cntDict[bm]):
            newWls[wl][0].append(bm)
            newWls[wl][1].append(baseFF + i*FFincrement)

print "Writing new fast forward configuration to file " + outFileName

outfile = open(outFileName, 'w')

outfile.write("workloads = {\n")
for wl in wls[:len(wls)-1]:
    outfile.write(str(wl)+":"+str(newWls[wl])+",\n")
outfile.write(str(len(wls))+":"+str(newWls[len(wls)])+"\n")
outfile.write("}\n")

outfile.flush()
outfile.close()

print "Done!"
print

print "Writing single core configuration to file " + singleCoreFileName

keys = allCnt.keys()
keys.sort()

singleCoreFile = open(singleCoreFileName, 'w')

singleCoreFile.write("configuration = {\n")
first = True
for key in keys[:len(keys)]:    
    for i in range(allCnt[key]):
        if first:
            first = False
        else:
            singleCoreFile.write(",\n")

        singleCoreFile.write("'"+key+str(i)+"': ['"+key+"',"+str(baseFF + i*FFincrement)+"]")

singleCoreFile.write("\n}\n")
singleCoreFile.flush()
singleCoreFile.close()

print "Done!"
print

print "Single configuration summary:"

sum = 0

for key in keys:
    print key.ljust(20)+str(allCnt[key]).rjust(3)
    sum = sum + allCnt[key]

print
print "Total configuration count: "+str(sum)


