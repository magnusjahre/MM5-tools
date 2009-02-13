
import pbsconfig
import parsemethods
import getInterference

np = 4

def getFilenames(cmd, config):
    sharedID = pbsconfig.get_unique_id(config)
    wl = parsemethods.getBenchmark(cmd)
    
    aloneIDs = []
    for i in range(np):
        tmpaparams = pbsconfig.get_alone_params(wl, i, config)
        tmpID = pbsconfig.get_unique_id(tmpaparams)
        aloneIDs.append(tmpID)

    return sharedID, aloneIDs

width = 20

print "".ljust(width),
for i in range(np):
    print ("CPU "+str(i)).rjust(width),
print


for cmd,params in pbsconfig.commandlines:
    sID, aIDs = getFilenames(cmd,params)

    id = 0
    acc = ["N/A" for i in range(np)]
    for aID in aIDs:
        try:
            c,w = getInterference.compareBusAccessTraces(sID+"/estimation_access_trace_"+str(id)+".txt", aID+"/dram_access_trace.txt", False)
            acc[id] = c
        except:
            pass
        id += 1

    
    print sID.ljust(width),
    for i in range(np):
        print acc[i].rjust(width),
    print

