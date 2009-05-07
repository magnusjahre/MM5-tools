#!/usr/bin/python

import sys
import interferencemethods
import deterministic_fw_wls as fair_workloads
import fairmha.resultparse.parsemethods as parsemethods
from optparse import OptionParser
import math
import pbsconfig
import re
import fairmha.plot.plot as plot

def createOutputText(data, reskey):

    text = ""

    w = 25
    keys = data.keys()
    keys.sort()

    text += "".ljust(w)
    for k in keys:
        for i in range(np):
            text += (str(k)+"_CPU"+str(i)).rjust(w)
    text += "\n"

    wls = data[keys[0]].keys()
    wls.sort()

    for wl in wls:
        text += str(wl).ljust(w)
        for k in keys:
            for i in range(np):
                if reskey != None:
                    if data[k][wl] != {}:
                        text += str(data[k][wl][reskey][i]).rjust(w)
                    else:
                        text += "Error".rjust(w)
                else:
                    if data[k][wl] != {}:
                        text += str(data[k][wl][i]).rjust(w)
                    else:
                        text += "Error".rjust(w)    
        text += "\n"

    return text

def getFilenames(cmd, config):
    sharedID = pbsconfig.get_unique_id(config)
    shName = sharedID+'/'+sharedID+'.txt'
    wl = parsemethods.getBenchmark(cmd)
    
    aloneIDs = []
    aloneNames = []
    for i in range(np):
        tmpaparams = pbsconfig.get_alone_params(wl, i, config)
        tmpID = pbsconfig.get_unique_id(tmpaparams)
        aloneIDs.append(tmpID)
        aloneNames.append(tmpID+'/'+tmpID+'.txt')

    return shName, aloneNames

usage = "usage: %prog [options] <cpu-count> <architecture> <command>"
parser = OptionParser(usage=usage,prog="parseInterference.py")
parser.add_option("-a", "--absolute-error", action="store_true", dest="absolute", default=True, help="Print errors in clock cycles (default)")
parser.add_option("-r", "--relative-error", action="store_false", dest="absolute", help="Print errors in percentage difference")
parser.add_option("-t", "--interference-type", dest="type", default="total", help="Interference type to retrieve (default: total)")
parser.add_option("-w", "--workload", dest="workload", help="Workload to parse (only works with the 'one' command)")
parser.add_option("-l", "--long-output", action="store_true", default=False, dest="longoutput", help="Prints results for all keys (applies to the 'best-static' command only)")
parser.add_option("-s", "--sort-keys", action="store_true", default=False, dest="sortkeys", help="Pads key multi-digit key numbers with zeros and sorts them in ascending order")
parser.add_option("-b", "--bin-size", action="store", type="int", default=10, dest="binsize", help="Bin size to use when creating a histogram representation of the data")
parser.add_option("-p", "--key-pattern", action="store", type="string", default=".*", dest="pattern", help="Only return results with keys matching this regular expression")
parser.add_option("-c", "--use-cache", action="store_true", default=False, dest="usecache", help="Use interference measurements from cache and not InterferenceManager (off by default)")
parser.add_option("-m", "--only-benchmark", action="store", type="string", default="", dest="benchmark", help="Only show the results for this benchmark")


inoptions,args = parser.parse_args()

if(len(args)) != 3:
    parser.error("incorrect number of arguments")

iTypes = {"ic-entry": "IC Entry",
           "ic-transfer": "IC Transfer",
           "ic-delivery": "IC Delivery",
           "bus-entry": "Bus Entry",
           "bus-queue": "Bus Queue",
           "bus-service": "Bus Service",
           "total": "Total"}

commands = {"all": "",
           "one-wl": "",
           "rwerror": "",
           "breakdown": "",
           "best-static": "",
           "one-type": "",
           "histogram": "",
           "queue-error": "",
           "queue-int-speedup": "",
           "per-arch-error-breakdown": "",
           "avg-error-w-errorbars": ""}

if args[2] not in commands:
    posCom = ""
    for a in commands:
        posCom += " "+a
    
    parser.error("Unknown command\nSupported commands:"+posCom)
    
if inoptions.type not in iTypes:
    posCom = ""
    for a in iTypes:
        posCom += " "+a
    parser.error("Unknown interference type\nAvailable types:"+posCom)

np = int(args[0])
memsys = args[1]

printAll = False
printOne = False
printWl = ""
printRW = False
printAbsError = inoptions.absolute
printBreakdown = False
doBestStatic = False
doHistogram = False
doQueueErrorPlot = False
doQueueIntVsSpeedup = False
doPerArchErrorBreakdown = False
doAvgErrorWithErrorbars = False

if args[2] == "all":
    print "Writing all results to files..."
    printAll = True
elif args[2] == "rwerror":
    printRW = True
elif args[2] == "breakdown":
    printBreakdown = True
elif args[2] == "one-wl":
    printOne = True
    if inoptions.workload == None:
        parser.error("A workload name must be specified when the 'one' command is used")
    printWl = inoptions.workload
elif args[2] == "best-static":
    doBestStatic = True
elif args[2] == "one-type":
    assert inoptions.type != None
    pattern = iTypes[inoptions.type]
elif args[2] == "histogram":
    doHistogram = True
elif args[2] == "queue-error":
    assert inoptions.usecache
    doQueueErrorPlot = True
elif args[2] == "queue-int-speedup":
    assert inoptions.usecache
    doQueueIntVsSpeedup = True
elif args[2] ==  "per-arch-error-breakdown":
    doPerArchErrorBreakdown = True
elif args[2] ==  "avg-error-w-errorbars":
    doAvgErrorWithErrorbars = True
else:
    assert False, "Unknown command"

keypattern = re.compile(inoptions.pattern)
memsyspattern = re.compile(".*"+str(memsys)+".*")

if printOne:
    for cmd, config in pbsconfig.commandlines:
        wl = parsemethods.getBenchmark(cmd)
        key = pbsconfig.get_key(cmd,config)
        thisNP = pbsconfig.get_np(config)
        
        keymatch = keypattern.findall(key) 
        memsysmatch = memsyspattern.findall(key)
    
        if keymatch != [] and memsysmatch != [] and wl == printWl and np == thisNP:
            print 
            print "Interference data for wl "+printWl+", key: "+key
            print
            shName,aloneNames = getFilenames(cmd,config)
            interferencemethods.getInterferenceBreakdownError(shName,aloneNames,True,memsys)

    sys.exit()

# Retrieve data
data = {}
slats = {}
alats = {}
sints = {}
intManData = {}
reqerrors = {}
sharedRequests = {}
aloneRequests = {}
speedups = {}

for cmd, config in pbsconfig.commandlines:
    if pbsconfig.get_np(config) != np:
        continue
    
    shName, aloneNames = getFilenames(cmd,config)
    wl = parsemethods.getBenchmark(cmd)
    key = pbsconfig.get_key(cmd, config)
    
    keymatch = keypattern.findall(key) 
    memsysmatch = memsyspattern.findall(key)
    
    if keymatch != [] and memsysmatch != []:
        if key not in data:
            data[key] = {}
            slats[key] = {}
            alats[key] = {}
            sints[key] = {}
            speedups[key] = {}

        assert wl not in data[key]
        data[key][wl],slats[key][wl],alats[key][wl],sints[key][wl] = interferencemethods.getInterferenceErrors(shName, aloneNames, printAbsError,memsys)
    
        speedups[key][wl] = interferencemethods.computeSpeedup(shName,aloneNames)
    
        if key not in intManData:
            intManData[key] = {}
        if wl not in intManData:
            intManData[key][wl] = {}
            
        intManData[key][wl]["Total"] = interferencemethods.retrieveInterferenceManagerData(shName,aloneNames,np)
    
        if key not in reqerrors:
            reqerrors[key] = {}
            sharedRequests[key] = {}
            aloneRequests[key] = {}
        assert wl not in reqerrors[key]
        
        if data[key][wl] != {}:
            sharedRequests[key][wl], aloneRequests[key][wl], reqerrors[key][wl] = interferencemethods.getReadWriteCount(shName,aloneNames) 
        else:
            reqerrors[key][wl] = {}

if not inoptions.usecache:
    data = intManData

if data == {}:
    print "Fatal: No matching results found"
    sys.exit(-1)

# Find best configuration
bestResult = {}
sortedWorkloads = data[data.keys()[0]].keys()
sortedWorkloads.sort()
for wl in sortedWorkloads:
    bestResult[wl] = [10000000.0 for i in range(np)]

for key in data:
    for wl in data[key]:
        assert "Total" in data[key][wl] 
        total = data[key][wl]["Total"]

        if total != []:
            for i in range(np):
                if math.fabs(float(total[i])) < math.fabs(bestResult[wl][i]):
                    bestResult[wl][i] = total[i]

if inoptions.sortkeys:
    inkeys = []
    
    splitstr = "-"
    
    numKeys = 0
    for k in data.keys():
        tmpdata = k.split(splitstr)
        if numKeys == 0:
            numKeys = len(tmpdata)
        else:
            assert numKeys == len(tmpdata) 
    
    keystore = [[] for i in range(numKeys)] 
    isInt = [False for i in range(numKeys)]
    
    for k in data.keys():
        tmpdata = k.split(splitstr)
        for i in range(len(tmpdata)):
            if tmpdata[i].isdigit():
                isInt[i] = True
                keystore[i].append(int(tmpdata[i]))
            else:
                keystore[i].append(tmpdata[i])
    
    keyDigits = []
    keystoreIndex = 0
    for keylist in keystore:
        if isInt[keystoreIndex]:
            maxval = max(keylist)
            digitMax = 10
            digits = 1
            assert maxval > 0
            while maxval >= digitMax:
                digits += 1
                digitMax *= 10
                assert digitMax < 100000000
            keyDigits.append(digits)
        else:
            keyDigits.append(-1)
        keystoreIndex += 1
    
    
    paddedKeys = {}
    for k in data.keys():
        tmpdata = k.split(splitstr)
        newKey = []
        for i in range(len(tmpdata)):
            if isInt[i]:
                if len(tmpdata[i]) < keyDigits[i]:
                    zerostr = ""
                    diff = keyDigits[i] - len(tmpdata[i])
                    for j in range(diff):
                        zerostr += "0"
                    newKey.append(zerostr+tmpdata[i])
                else:
                    newKey.append(tmpdata[i])
            else:
                assert keyDigits[i] == -1
                newKey.append(tmpdata[i])
        
        newKeyStr = newKey[0]
        for nk in newKey[1:]:
            newKeyStr += splitstr+nk
        
        
        paddedKeys[k] = newKeyStr
    
    # Update dict with new keys
    newdata = {}
    for d in data:
        newdata[paddedKeys[d]] = data[d]
    data = newdata

if printAll:
    for o in iTypes:
        if iTypes[o] != "":
            text = createOutputText(data,iTypes[o])
            
            fname = "interference_error_"+o+".txt"
            print "Writing results for file "+fname

            tfile = open(fname, "w")
            tfile.write(text)
            tfile.flush()
            tfile.close()
elif printRW:
    print createOutputText(reqerrors, None)

elif printBreakdown:
    newdata = {}
    
    for key in data:
        
        if key not in newdata:
            newdata[key] = {}
        for wl in data[key]:
            
            if wl not in newdata[key]:
                newdata[key][wl] = {}
                
            if data[key][wl] != {}:
                assert "Total" in data[key][wl]
                for o in iTypes:
                    if iTypes[o] != "" and iTypes[o] != "Total":
                        
                        for i in range(np):
                            if i not in newdata[key][wl]:
                                newdata[key][wl][i] = {}
    
                            assert iTypes[o] not in newdata[key][wl][i]
                            newdata[key][wl][i][iTypes[o]] = data[key][wl][iTypes[o]][i]
            else:
                for o in iTypes:
                    if iTypes[o] != "" and iTypes[o] != "Total":
                        for i in range(np):
                            if i not in newdata[key][wl]:
                                newdata[key][wl][i] = {}
                            
                            newdata[key][wl][i][iTypes[o]] = "Error" 

    ndkey0 = newdata.keys()[0]
    wlkey0 = newdata[ndkey0].keys()[0]
    itypes = newdata[ndkey0][wlkey0][0].keys()
    itypes.sort()

    width = 25
    print "".ljust(width),
    for t in itypes:
        print t.rjust(width),
    print

    for k in newdata:
        for wl in newdata[k]:
            for i in newdata[k][wl]:
                print (k+"-"+wl+"-"+str(i)).ljust(width),
                for t in itypes:
                    print str(newdata[k][wl][i][t]).rjust(width),
                print

elif doBestStatic:
    
    wls = data[data.keys()[0]].keys()
    wls.sort()
    
    reskeys = data.keys()
    reskeys.sort()
    
    width = 25
    print "".ljust(width),
    if inoptions.longoutput:
        for k in reskeys:
            print k.rjust(width),
    print "Best Static".rjust(width)
    
    if inoptions.longoutput:
        sums = [0 for i in range(len(reskeys)+1)]
    else:
        sums = [0]
    
    for wl in wls:
        bms = fair_workloads.getBms(wl,np)
        assert len(bms) == len(bestResult[wl])
        for i in range(len(bestResult[wl])):
            if inoptions.benchmark == "" or inoptions.benchmark == bms[i]:
                print (wl+"-"+bms[i]).ljust(width),
                keynum = 0
                if inoptions.longoutput:
                    for reskey in reskeys:
                        assert "Total" in data[reskey][wl]
                        val = data[reskey][wl]["Total"][i]
                        print str(val).rjust(width),
                        sums[keynum] += val
                        keynum += 1
                best = bestResult[wl][i]
                print str(best).rjust(width)
                sums[keynum] += best

    print "Average".ljust(width),
    numLines = np * len(wls)
    for sum in sums:
        avg = float(sum) / float(numLines)
        print ("%.2f" % avg).rjust(width),
    print

elif doHistogram:
    
    values = []
    
    for wl in sortedWorkloads:
        for i in range(np):
            values.append(bestResult[wl][i])
    
    minval = min(values)
    maxval = max(values)
                
    firstbin = minval - (minval % inoptions.binsize)
    lastbin = maxval + (maxval % inoptions.binsize) + inoptions.binsize
    
    bincnt = (lastbin - firstbin) / inoptions.binsize
    
    bins = {}
    for i in range(firstbin, lastbin)[::inoptions.binsize]:
        bins[i] = 0
    
    for v in values:
        binkey = v - (v % inoptions.binsize)
        bins[binkey] += 1
    
    plotdata = []
    plotmax = 0
    sortedbins = bins.keys()
    sortedbins.sort()
    for b in sortedbins:
        if bins[b] != 0:
            plotdata.append( ( ((b + (b-inoptions.binsize))/2), [bins[b]]) )
            if bins[b] > plotmax:
                plotmax = bins[b]
        
    plot.plotHistogram(plotdata,
                       "interferenceplot",
                       ["Number of Benchmarks","Error"],
                       ["Number of Benchmarks"],
                       False,
                       False,
                       0,
                       plotmax+5)
    
    width = 25
    print "Bin".ljust(width),
    print "Elements".rjust(width)
    
    bkeys = bins.keys()
    bkeys.sort()
    
    for bkey in bkeys:
        if bins[bkey] != 0:
            print (str(bkey)+" - "+str(bkey + inoptions.binsize -1)).ljust(width),
            print str(bins[bkey]).rjust(width)
    
elif doQueueErrorPlot:
    
    sortedKeys = data.keys()
    sortedKeys.sort()
    
    width = 25
    print "".ljust(width),
    print "Shared lat".rjust(width),
    print "Interference".rjust(width),
    print "Estimated alone lat".rjust(width),
    print "Actual alone lat".rjust(width)
    
    for dk in sortedKeys:
        for wlk in sortedWorkloads:
            
            wlslat = slats[dk][wlk]["Bus Queue"]
            wlint = sints[dk][wlk]["Bus Queue"]
            wlalat = alats[dk][wlk]["Bus Queue"]
            
            estimate = [wlslat[i] - wlint[i] for i in range(np)]
            
            bms = fair_workloads.getBms(wlk,np)
            
            for i in range(np):
                print (wlk+"-"+bms[i]).ljust(width),
                print str(wlslat[i]).rjust(width),
                print str(wlint[i]).rjust(width),
                print str(estimate[i]).rjust(width),
                print str(wlalat[i]).rjust(width)
    
elif doQueueIntVsSpeedup:

    memQueueInt = {}

    for key in slats:
        assert key in alats
        memQueueInt[key] = {}

        for wl in slats[key]:
            assert wl in alats[key]
            assert 'Bus Queue' in alats[key][wl]
            assert 'Bus Queue' in slats[key][wl]
            
            queueInterference = [0 for i in range(np)]
            for i in range(np):
                queueInterference[i] = slats[key][wl]["Bus Queue"][i] - alats[key][wl]["Bus Queue"][i]

            memQueueInt[key][wl] = queueInterference


    speedupToQueueInt = {}
    for key in memQueueInt:
        assert key in speedups
        for wl in memQueueInt[key]:
            assert wl in speedups[key]
            for i in range(np):
                
                if sharedRequests[key][wl][i] >= 70000 and  sharedRequests[key][wl][i] <= 120000:
                
                    expid = key+"-"+wl+"-CPU"+str(i)
                    if speedups[key][wl][i] in speedupToQueueInt:
                        speedupToQueueInt[speedups[key][wl][i]].append( (memQueueInt[key][wl][i],expid, sharedRequests[key][wl][i]) )
                    else:
                        speedupToQueueInt[speedups[key][wl][i]] = [ (memQueueInt[key][wl][i], expid, sharedRequests[key][wl][i]) ]

    speedupKeys = speedupToQueueInt.keys()
    speedupKeys.sort()
    
    width = 30
    print "".ljust(width),
    print "Bus Queue Int.".rjust(width),
    print "ID".rjust(width),
    print "Shared Reqs".rjust(width)
    
    for k in speedupKeys:
        for val,id,sreq in speedupToQueueInt[k]: 
            print ("%.4f" % k).ljust(width),
            print str(val).rjust(width),
            print id.rjust(width),
            print str(sreq).rjust(width)

elif doPerArchErrorBreakdown:
    
    
    avgRes = {}
    distribution = {}
    for key in data:
        
        if key not in avgRes:
            avgRes[key] = {}
            distribution[key] = {}
        
        errorPerReqSum = {}
        reqsum = {}
        
        reqsPerError = {}
        
        for wl in data[key]:
            
            for itype in data[key][wl]:
                if itype != "Total":
                    
                    if itype not in errorPerReqSum:
                        errorPerReqSum[itype] = 0
                        reqsum[itype] = 0
                        reqsPerError[itype] = {}

                    for cpuID in range(len(data[key][wl][itype])):
                        
                        tmperror = abs(data[key][wl][itype][cpuID])
                        
                        errorPerReqSum[itype] += tmperror  * sharedRequests[key][wl][cpuID]
                        reqsum[itype] += sharedRequests[key][wl][cpuID]
                        
                        if tmperror not in reqsPerError[itype]:
                            reqsPerError[itype][tmperror] = 0
                        reqsPerError[itype][tmperror] += sharedRequests[key][wl][cpuID]
        
        for itype in errorPerReqSum:
            avgRes[key][itype] = float(errorPerReqSum[itype]) / float(reqsum[itype])
            
        for itype in reqsPerError:
            
            tolerance = 0.0001
            
            tmpdistrib = {}
            for error in reqsPerError[itype]:
                probability = float(reqsPerError[itype][error]) / float(reqsum[itype])
                tmpdistrib[error] = probability
                
            tmpkeys = tmpdistrib.keys()
            tmpkeys.sort()
            
            tmpdata = []
            representedReqs = 1.0
            for tmpkey in tmpkeys:
                representedReqs -= tmpdistrib[tmpkey]
                if representedReqs < tolerance:
                    representedReqs = 0.0
                tmpdata.append( (tmpkey, representedReqs) )
                    
            distribution[key][itype] = tmpdata
    
    width = 30
    
    
    if inoptions.type == "total":
    
        keys = avgRes.keys()
        keys.sort()
        
        itypes = avgRes[keys[0]].keys()
        itypes.sort()
        
        print "".ljust(width),
        for t in itypes:
            print t.rjust(width),
        print
        
        for k in keys:
            print k.ljust(width),
            for it in itypes:
                print ("%.2f" % avgRes[k][it]).rjust(width),
            print 
    else:
        usetype = iTypes[inoptions.type]
        
        keys = distribution.keys()
        keys.sort()
        
        print "".ljust(width),
        for k in keys:
            print k.rjust(width),
        print
            
        printData = {}
        for keyID in range(len(keys)):
            for error, cumprob in distribution[keys[keyID]][usetype]:
                if error not in printData:
                    printData[error] = [-1 for i in range(len(keys))]
                printData[error][keyID] = cumprob
                
        sortedErrors = printData.keys()
        sortedErrors.sort()

        for err in sortedErrors:
            print str(err).ljust(width),
            for elem in printData[err]:
                if elem == -1:
                    print "".rjust(width),
                else:
                    print ("%.3f" % elem).rjust(width),
            print

        
elif doAvgErrorWithErrorbars:
    
    avgRes = {}
    avgAbsRes = {}
    totalReqs = {}
    
    absdistribution = {}
    distribution = {}
    
    for key in data:
        
        if key not in absdistribution:
            absdistribution[key] = {}
            distribution[key] = {}
        
        errorsum = 0
        abserrorsum = 0
        reqsum = 0
        
        for wl in data[key]:
            for cpuID in range(len(data[key][wl]["Total"])):
                
                absError = abs(data[key][wl]["Total"][cpuID])
                realError = data[key][wl]["Total"][cpuID]
                
                errorsum += realError * sharedRequests[key][wl][cpuID]
                abserrorsum += absError *  sharedRequests[key][wl][cpuID]
                reqsum += sharedRequests[key][wl][cpuID]
                
                if absError not in absdistribution[key]:
                    absdistribution[key][absError] = 0
                absdistribution[key][absError] += sharedRequests[key][wl][cpuID]
                 
                if realError not in distribution[key]:
                    distribution[key][realError] = 0
                distribution[key][realError] += sharedRequests[key][wl][cpuID]  
                
        avgRes[key] = float(errorsum) / float(reqsum)
        avgAbsRes[key] = float(abserrorsum) / float(reqsum)
        totalReqs[key] = reqsum    

    stdDev = {}
    for k in distribution:
        
        samplemean = float(avgRes[key])
        
        variance = 0
        for errorval in distribution[k]:
            frequency = distribution[k][errorval]
            probability = float(frequency) / float(reqsum)

            variance += math.pow(float(errorval) - samplemean,2)  * probability             
        
        stdDev[k] = math.sqrt(variance)
        
    cumDistrib = {}
    
    for k in absdistribution:
        
        distkeys = absdistribution[k].keys()
        distkeys.sort()
        
        tmpdist = [0 for i in range(len(distkeys))]
        
        tmpdist[0] = absdistribution[k][distkeys[0]]
        reqsum = absdistribution[k][distkeys[0]]
        for i in range(len(distkeys))[1:]:
            tmpdist[i] = tmpdist[i-1] + absdistribution[k][distkeys[i]]
            reqsum += absdistribution[k][distkeys[i]]

        percdist = [float(d) / float(reqsum) for d in tmpdist]
        
        cumDistrib[k] = (distkeys, percdist)
        
        
    percerrs = [0.90, 0.95, 0.99,  0.999]
        
    width = 25
    
    print "".ljust(width),
    print "Avg Error".rjust(width),
    print "Std. dev".rjust(width),
    print "Avg Abs Error".rjust(width),
    for acceptErr in percerrs:
        print ("%.3f" % acceptErr).rjust(width),
    print
    
    keys = avgRes.keys()
    keys.sort()
    
    for k in keys:
        print k.ljust(width),
        print ("%.2f" % avgRes[k]).rjust(width),
        print ("%.2f" % stdDev[k]).rjust(width),
        print ("%.2f" % avgAbsRes[k]).rjust(width),
        
        for acceptErr in percerrs:
            
            distkeys, distrib = cumDistrib[k]
            
            for i in range(len(distrib)):
                if distrib[i] >= acceptErr:
                    break
            
            print str(distkeys[i]).rjust(width),
        print

else:
    print createOutputText(data, pattern)
    
    
