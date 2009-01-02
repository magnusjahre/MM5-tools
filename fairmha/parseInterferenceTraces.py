
import pbsconfig
import getInterference
import re
import parsemethods

np = 4
memsys = "RingBased"
channels = "4"

memPattern = re.compile(memsys)
channelPattern = re.compile("-EMEMORY-BUS-CHANNELS="+channels)

def getFilenames(cmd, config):
    sharedID = pbsconfig.get_unique_id(config)
    wl = parsemethods.getBenchmark(cmd)
    
    aloneIDs = []
    for i in range(np):
        tmpaparams = pbsconfig.get_alone_params(wl, i, config)
        tmpID = pbsconfig.get_unique_id(tmpaparams)
        aloneIDs.append(tmpID)

    return sharedID, aloneIDs

def writeSummaryFile(data,name):
    file = open(name, "w")
    
    w = 30
    file.write("".rjust(w))
    intTypes = data.keys()
    intTypes.sort()
    for k in intTypes:
        file.write(k.rjust(w))
    file.write("\n")

    maxval = max(data[data.keys()[0]].keys())
    minval = min(data[data.keys()[0]].keys())

    for k in data:
        if max(data[k].keys()) > maxval:
            maxval = max(data[k].keys())

        if min(data[k].keys()) < minval:
            minval = min(data[k].keys())


    for i in range(minval,maxval+1):
        doPrint = False
        for t in intTypes:
            if i in data[t]:
                doPrint = True

        if doPrint:
            file.write(str(i).rjust(w))
            for t in intTypes:
                if i in data[t]:
                    file.write(str(data[t][i]).rjust(w))
                else:
                    file.write("".rjust(w))

            file.write("\n")

    file.flush()
    file.close()

bigfile = open("interference_"+memsys+"_"+channels, "w")

for cmd,config in pbsconfig.commandlines:

    if pbsconfig.get_np(config) == np and memPattern.findall(cmd) != [] and channelPattern.findall(cmd) != []:

        shID, aloneIDs = getFilenames(cmd,config)

        print "Gathering data from experiment "+shID

        cpuid = 0
        for aID in aloneIDs:
            name = ""
            if memsys == "CrossbarBased":
                print "not implemented"
                assert False
            else:
                int,stats = getInterference.computeInterferenceFromTrace(shID+"/PrivateL2Cache"+str(cpuid)+"LatencyTrace.txt", aID+"/PrivateL2Cache0LatencyTrace.txt", False)
                data = getInterference.createReqVsLatData(int)
                print data
                writeSummaryFile(data,"int_summary_"+shID+".txt")
                assert False
            cpuid += 1
             

                                                         
bigfile.flush()
bigfile.close()
