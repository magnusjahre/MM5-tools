#!/usr/bin/python

import pbsconfig
import sys
from optparse import OptionParser

def main():
    
    parser = OptionParser(usage="%prog [options] dictionary key width")
    parser.add_option("--use-cpu-count", action="store_true", dest="useCPUCount", default=False, help="Use CPU-count in result module name")
    parser.add_option("--print-breakdown", action="store_true", dest="printBreakdown", default=False, help="Merge keys and print errors for all interference types")
    options,args = parser.parse_args()
    
    if(len(args) != 3):
        print "You must provide a dictionary, a key and width"
        return -1
    
    dictionaryName = args[0]
    dictionaryKey = args[1]
    width = int(args[2])
        
    resultmodules = {}
    
    for cmd, config in pbsconfig.commandlines:
        expkey = pbsconfig.get_key(cmd,config)
        np = pbsconfig.get_np(config)
        
        if options.useCPUCount:
            key = str(np)
        else:
            key = expkey
        
        if key not in resultmodules:
            try:                
                resultmodules[key] = __import__(key+"-results")
            except:
                print "File not found: "+key+"-results.py"
    
    data = {}
    
    for key in resultmodules:

        if dictionaryName == "errorRMS":
            data[key] = {}
            for parameter in resultmodules[key].errorRMS:
                assert parameter not in data[key]
                if options.printBreakdown:
                    data[key][parameter] = resultmodules[key].errorRMS[parameter]
                else:
                    data[key][parameter] = resultmodules[key].errorRMS[parameter][dictionaryKey]
        
        elif dictionaryName == "errorAvg":
            data[key] = {}
            for parameter in resultmodules[key].errorAvg:
                assert parameter not in data[key]
                if options.printBreakdown:
                    data[key][parameter] = resultmodules[key].errorAvg[parameter]
                else:
                    data[key][parameter] = resultmodules[key].errorAvg[parameter][dictionaryKey]
        
        elif dictionaryName == "relErrorAvg":
            data[key] = {}
            for parameter in resultmodules[key].relErrorAvg:
                assert parameter not in data[key]
                if options.printBreakdown:
                    data[key][parameter] = resultmodules[key].relErrorAvg[parameter]
                else:
                    data[key][parameter] = resultmodules[key].relErrorAvg[parameter][dictionaryKey]
                    
        elif dictionaryName == "relErrorStdDev":
            data[key] = {}
            for parameter in resultmodules[key].relErrorAvg:
                assert parameter not in data[key]
                if options.printBreakdown:
                    data[key][parameter] = resultmodules[key].relErrorStdDev[parameter]
                else:
                    data[key][parameter] = resultmodules[key].relErrorStdDev[parameter][dictionaryKey]
        
        elif dictionaryName == "avgLat":
            data[key] = {}
            for ss in resultmodules[key].aggregateLat:
                assert ss in resultmodules[key].aggregateNumSamples
                assert ss not in data[key]
                data[key][ss] =  float(resultmodules[key].aggregateLat[ss]) / float(resultmodules[key].aggregateNumSamples[ss])   
        
        elif dictionaryName == "allBusQueueRMS":
            data[key] = {}
            for id in resultmodules[key].rmsAllResults:
                ids = id.split("-")
                assert len(ids) == 4
                expkey = ids[0]+"-"+ids[1]
                bmkey = ids[2]+"-"+ids[3]
                
                if expkey not in data[key]:
                    data[key][expkey] = {}
                    
                data[key][expkey][bmkey] = resultmodules[key].rmsAllResults[id][1]["bus_queue"]
        
        else:
            print "Dictionary name "+dictionaryName+" not supported"
            return -1
    
    
    dkeys = data.keys()
    dkeys.sort()
    
    paramkeys = data[dkeys[0]].keys()
    paramkeys.sort()
    
    if dictionaryName == "allBusQueueRMS":
        
        dataArrays = {}
        
        for np in data:
            dataArrays[np] = {}
            for expkey in data[np]:
                values = []
                for bmkey in data[np][expkey]:    
                    values.append(data[np][expkey][bmkey])
                values.sort()
                dataArrays[np][expkey] = values
                assert len(values) == 160
                
        nps = dataArrays.keys()
        nps.sort()
        
        exps = dataArrays[nps[0]].keys()
        exps.sort()
        
        print "".ljust(width),
        for np in nps:
            for exp in exps:
                print (str(np)+"-"+str(exp)).rjust(width),
        print
        
        for i in range(160):
            print str(i).ljust(width),
            for np in nps:
                for exp in exps:
                    try:
                        print ("%.3f" % dataArrays[np][exp][i]).rjust(width),
                    except:
                        print str(dataArrays[np][exp][i]).rjust(width),
            print
        
        
    elif not options.printBreakdown:
    
        print "".ljust(width),
        for k in dkeys:
            print str(k).rjust(width),
        print
    
        for pk in paramkeys:
            print str(pk).ljust(width),
            for dk in dkeys:
                print ("%.3f" % data[dk][pk]).rjust(width),
            print
            
    else:
        
        itypes = data[dkeys[0]][paramkeys[0]].keys()
        itypes.sort()
        
        print "".ljust(width),
        for k in itypes:
            if k != "Total" and k != "cache_capacity":
                print str(k).rjust(width),
        print
        
        for dk in dkeys:
            for pk in paramkeys:
                print (str(dk)+"-"+str(pk)).ljust(width),
                for it in itypes:
                    if it != "Total" and it != "cache_capacity":
                        print ("%.3f" % data[dk][pk][it]).rjust(width),
                print
        

    return 0

if __name__ == "__main__":
    sys.exit(main())