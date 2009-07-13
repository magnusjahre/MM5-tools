
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

width = 30


resfile = open("pageResults.txt", "w")
errfile = open("pageErrors.txt", "w")

resfile.write("".ljust(width))
for i in range(np):
    resfile.write(("CPU "+str(i)).rjust(width))
resfile.write("\n")

first = True

for cmd,params in pbsconfig.commandlines:
    sID, aIDs = getFilenames(cmd,params)

    id = 0
    acc = ["N/A" for i in range(np)]
    errs = [{} for i in range(np)]
    for aID in aIDs:
        print "Checking "+sID+" CPU"+str(id)
        try:
            c,w,errcounts = getInterference.compareBusAccessTraces(sID+"/estimation_access_trace_"+str(id)+".txt", aID+"/dram_access_trace.txt", False)
            acc[id] = c
            errs[id] = errcounts
        except:
            pass
        id += 1

    resfile.write(sID.ljust(width))
    for i in range(np):
        resfile.write(acc[i].rjust(width))
    resfile.write("\n")
    resfile.flush()

    if first:
        errfile.write("".ljust(width))
        keys = errs[0].keys()
        keys.sort()
        for k in keys:
            errfile.write(k.rjust(width))
        errfile.write("\n")
        first = False

    for i in range(np):
        errfile.write((sID+"-CPU"+str(i)).ljust(width))
        keys = errs[i].keys()
        keys.sort()
        for k in keys:
            errfile.write(str(errs[i][k]).rjust(width))
        errfile.write("\n")
    errfile.flush()

resfile.flush()
resfile.close()

errfile.flush()
errfile.close()
