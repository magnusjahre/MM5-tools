
import sys
import pbsconfig
import getInterference
import re
import parsemethods
import os
import plot

assert len(sys.argv) > 1

nps = []
npstrs = sys.argv[1:]
for n in npstrs:
    nps.append(int(n))


memsyss = ["CrossbarBased", "RingBased"]
channels = ["1","2","4"]

#memsyss = ["CrossbarBased"]
#channels = ["4"]

dirname = "interference_summaries"
plotdirname = "interference_plots"

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
        intTypes = newData.keys()
        for t in intTypes:
            aggregate[t] = {}

    for intType in newData:
        for intTick in newData[intType]:
            if intTick not in aggregate[intType]:
                aggregate[intType][intTick] = newData[intType][intTick]
            else:
                aggregate[intType][intTick] += newData[intType][intTick]

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
                    if data[t][i] != 0.0:
                        file.write(str(data[t][i]).ljust(w))
                    else:
                        file.write("-".ljust(w))
                else:
                    file.write("-".ljust(w))

            file.write("\n")

    file.flush()
    file.close()

def gatherData(shID, aloneIDs, curAgg):
    cpuid = 0
    for aID in aloneIDs:
        data = {}
        if memsys == "CrossbarBased":
            tmpAgg = {}
            tmpData = getInterference.parseInterferenceTraceExternal(shID+"/L1dcaches"+str(cpuid)+"LatencyTrace.txt", 
                                                                     aID+"/L1dcaches0LatencyTrace.txt", 
                                                                     dirname+"/interference_"+aID+"_dcache.txt", 
                                                                     dirname+"/stats.txt", 
                                                                     aID+"_dcache")
            tmpAgg = addToAggregate(tmpAgg, tmpData)
            tmpData = getInterference.parseInterferenceTraceExternal(shID+"/L1icaches"+str(cpuid)+"LatencyTrace.txt",
                                                                     aID+"/L1icaches0LatencyTrace.txt",
                                                                     dirname+"/interference_"+aID+"_icache.txt",
                                                                     dirname+"/stats.txt",
                                                                     aID+"_icache")
            tmpAgg = addToAggregate(tmpAgg, tmpData)
            data = tmpAgg
        else:
            data = getInterference.parseInterferenceTraceExternal(shID+"/PrivateL2Cache"+str(cpuid)+"LatencyTrace.txt",
                                                                  aID+"/PrivateL2Cache0LatencyTrace.txt",
                                                                  dirname+"/interference_"+aID+".txt",
                                                                  dirname+"/stats.txt",
                                                                  aID+"_priv")
        curAgg = addToAggregate(curAgg, data)

        
        impact = computeImpactFactors(data)
        writeSummaryFile(impact,dirname+"/int_summary_"+shID+"_"+str(cpuid)+".txt")
                
            
        print "Finished processing "+aID
        cpuid += 1
    return curAgg


os.mkdir(dirname)
os.mkdir(plotdirname)

for np in nps:
    for memsys in memsyss:
        for channel in channels:
            
            memPattern = re.compile(memsys)
            channelPattern = re.compile("-EMEMORY-BUS-CHANNELS="+channel)
            
            print "Parsing "+str(np)+" CPUs, "+memsys+", "+channel+" channel(s)"

            aggData = {}
            for cmd,config in pbsconfig.commandlines:
                if pbsconfig.get_np(config) == np and memPattern.findall(cmd) != [] and channelPattern.findall(cmd) != []:
                    shID, aloneIDs = getFilenames(cmd,config)
                    print "Gathering data from experiment "+shID
                    aggData = gatherData(shID, aloneIDs, aggData)
             
            assert aggData != {}
            writeSummaryFile(aggData, dirname+"/interference_"+memsys+"_"+channel+"_requests.txt")
            aggImpact = computeImpactFactors(aggData)
            writeSummaryFile(aggImpact, dirname+"/interference_"+memsys+"_"+channel+"_impact.txt")
            
            titles = aggImpact.keys()
            titles.sort()
            plot.plotScatter(plotdirname+"/"+str(np)+"_"+memsys+"_"+channel+"_channels",
                             str(np)+" CPUs, "+memsys+", "+channel+" channels",
                             "Interference (cycles)",
                             "Interference Impact Factor",
                             titles,
                             dirname+"/interference_"+memsys+"_"+channel+"_impact.txt")
                
            
