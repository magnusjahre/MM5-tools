import pbsconfig
import fairmha.plot as plot
import getInterference
import os
import deterministic_fw_wls as workload_info

results = {}

np = 0

for cmd, params in pbsconfig.commandlines:
    
    resID = pbsconfig.get_unique_id(params)
    resKey = pbsconfig.get_key(cmd, params)
    sharedFiles = []
    np = pbsconfig.get_np(params)
    wl = pbsconfig.get_workload(params)
    for i in range(np):
        sharedFiles.append(resID+'/CPU'+str(i)+'InterferenceTrace.txt')

    wlNum = int(wl.replace("fair", ""))
    bms = pbsconfig.get_bm_names(workload_info.workloads[wlNum], np)
    
    aloneFiles = []
    for i in range(len(bms)):
        a_params = pbsconfig.get_alone_params(wl, i, params)
        aResID = pbsconfig.get_unique_id(a_params)
        aloneFiles.append(aResID+'/CPU0InterferenceTrace.txt')


    for i in range(np):

        if resKey not in results:
            results[resKey] = {}

        if wl not in results[resKey]:
            results[resKey][wl] = {}

        assert i not in results[resKey][wl]
        results[resKey][wl][i] = getInterference.getAverageSampleError(sharedFiles[i], aloneFiles[i])

w = 20

print "".ljust(w),
for k in results:
    for i in range(np):
        print (str(k)+"_CPU"+str(i)).rjust(w),
print

keys = results.keys()
keys.sort()

wls = results[keys[0]].keys()
wls.sort()

for wl in wls:
    print str(wl).ljust(w),
    for k in keys:
        for vkey in results[k][wl]:
            print str(results[k][wl][vkey]).rjust(w),
    print


    
    
