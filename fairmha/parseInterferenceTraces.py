
import pbsconfig
import getInterference
import re
import parsemethods
import os

np = 4
memsys = "RingBased"
channels = "4"

dirname = "interference_summaries"

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

def computeImpactFactors(data):

    intTypes = data.keys()
    intTypes.sort()

    reqs = {}
    for t in intTypes:
        reqs[t] = 0

    for intType in intTypes:
        for intTick in data[intType]:
            reqs[intType] += data[intType][intTick]

    for i in range(len(reqs.keys()))[1:]:
        assert reqs[reqs.keys()[i-1]] == reqs[reqs.keys()[i]]


    impact = {}
    for t in intTypes:
        impact[t] = {}

    for intType in intTypes:
        for intTick in data[intType]:
            assert intTick not in impact[intType]
            impact[intType][intTick] = float(intTick) * (float(data[intType][intTick]) / float(reqs[intType]))

    return impact

def addToAggregate(aggregate, newData):
    
    if len(aggregate) == 0:
        intTypes = data.keys()
        for t in intTypes:
            aggregate[t] = {}

    for intType in data:
        for intTick in data[intType]:
            if intTick not in aggregate[intType]:
                aggregate[intType][intTick] = data[intType][intTick]
            else:
                aggregate[intType][intTick] += data[intType][intTick]

    return aggregate

def writeSummaryFile(data,name):
    file = open(name, "w")
    
    w = 30
    file.write("#".ljust(w))
    intTypes = data.keys()
    intTypes.sort()
    for k in intTypes:
        file.write(k.ljust(w))
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
            file.write(str(i).ljust(w))
            for t in intTypes:
                if i in data[t]:
                    file.write(str(data[t][i]).ljust(w))
                else:
                    file.write("".ljust(w))

            file.write("\n")

    file.flush()
    file.close()


os.mkdir(dirname)

aggData = {}

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
                aggData = addToAggregate(aggData, data)
                impact = computeImpactFactors(data)
                writeSummaryFile(impact,dirname+"/int_summary_"+shID+"_"+str(cpuid)+".txt")
                

            print "Finished processing "+aID
            cpuid += 1
             
aggImpact = computeImpactFactors(aggData)
writeSummaryFile(aggImpact, dirname+"/interference_"+memsys+"_"+channels+".txt")

