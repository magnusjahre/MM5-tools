#!/usr/bin/python

import sys
import pbsconfig
import re
import math
from optparse import OptionParser
import deterministic_fw_wls as workloads

def generateFilenames():
    
    filenames = []

    for cmd, config in pbsconfig.commandlines:

        key = pbsconfig.get_key(cmd,config)
        np = pbsconfig.get_np(config)
        
        shareddir = pbsconfig.get_unique_id(config)
        wl =pbsconfig.get_workload(config)
        
        sfilename = shareddir+"/"+shareddir+".txt"
        afilenames = []
        
        for i in range(np):
            aparams = pbsconfig.get_alone_params(wl, i, config)
            alonedir = pbsconfig.get_unique_id(aparams)
            afilenames.append(alonedir+"/"+alonedir+".txt")
            
        filenames.append( (np, key, sfilename, afilenames, wl) )
            
    return filenames

def find(pattern, filename, cpuid = -1):
    try:
        file = open(filename)
        text = file.read()
        file.close()
    except IOError:
        print "Read error on file "+filename
        return []
        
    res = pattern.findall(text)
    
    results = {}
    
    for r in res:
        splitted = r.split()
        idsplit = splitted[0].split(".")
        cacheid = idsplit[0]
        data = int(splitted[1])
        useCPUID = cpuid
        if cpuid == -1:
            useCPUID = int(idsplit[1].split("_")[-1])
        
        if cacheid not in results:
            results[cacheid] = {}
            
        
        results[cacheid][useCPUID] = data
    
    return results

def parseParameters():
    parser = OptionParser(usage="checkShadowTagAccuracy.py [options]")
    parser.add_option("--full-map", action="store_true", dest="fullMap", default=False, help="Use full-map implementation results in parsing")
    parser.add_option("--print-all", action="store_true", dest="printAll", default=False, help="Print requests per workload")
    parser.add_option("--key-is-int", action="store_true", dest="keyIsInt", default=False, help="The keys can be sorted as integers")
    options,args = parser.parse_args()
    
    return options,args

def main():
    
    options,args = parseParameters()
    
    relerrsum = {}
    relerrsumsq = {}
    numerrs = {}
    
    missPattern = re.compile("Shared.*misses_per_cpu_.*")
    aloneMissPattern = re.compile("Shared.*misses_per_cpu.*")
    if options.fullMap:
        shadowMissPattern = re.compile("Shared.*cpu_extra_misses_.*")
    else:
        shadowAloneEstimatePattern = re.compile("Shared.*estimated_shadow_misses_.*")
    
    breakdownres = {}
    
    for np, key, sharedfile, alonefiles, wl in generateFilenames():
    
        if np not in relerrsum:
            relerrsum[np] = {}
            relerrsumsq[np] = {}
            numerrs[np] = {}
            breakdownres[np] = {} 
            
        if key not in relerrsum[np]:
            relerrsum[np][key] = 0
            relerrsumsq[np][key] = 0
            numerrs[np][key] = 0
            breakdownres[np][key] = {}
        
        sharedMisses = find(missPattern, sharedfile)
        aloneMisses = [find(aloneMissPattern, alonefiles[i], i) for i in range(np) ]
        
        if wl not in breakdownres[np][key]:
            breakdownres[np][key][wl] = {}
            for cachekey in sharedMisses:
                breakdownres[np][key][wl][cachekey] = {}
                for i in range(np):
                    breakdownres[np][key][wl][cachekey][i] = {"estimate": "N/A", "actual": "N/A", "relerror": "N/A"} 
        
        if options.fullMap:
            shadowMisses = find(shadowMissPattern, sharedfile)            
        else:
            shadowAloneMissEstimate = find(shadowAloneEstimatePattern, sharedfile)
        
        for cachekey in sharedMisses:
            for cpukey in sharedMisses[cachekey]:
                
                if aloneMisses[cpukey] == []:
                    continue

                if options.fullMap:    
                    est = sharedMisses[cachekey][cpukey] - shadowMisses[cachekey][cpukey]
                else:
                    est = shadowAloneMissEstimate[cachekey][cpukey]
                
                err = float(est) - float(aloneMisses[cpukey][cachekey][cpukey])
                relErr = float(err)/float(sharedMisses[cachekey][cpukey])
                
                breakdownres[np][key][wl][cachekey][cpukey]["estimate"] = float(est)
                breakdownres[np][key][wl][cachekey][cpukey]["actual"] = float(aloneMisses[cpukey][cachekey][cpukey])
                breakdownres[np][key][wl][cachekey][cpukey]["relerror"] =  relErr
                            
                relerrsum[np][key] += relErr
                relerrsumsq[np][key] += relErr**2
                numerrs[np][key] += 1.0
    
    if not options.printAll:
    
        nps = relerrsum.keys()
        nps.sort()
        keys = relerrsum[nps[0]].keys()
        
        if options.keyIsInt:
            keys = [int(i) for i in keys]
        
        keys.sort()
        
        width = 30
        
        print "".ljust(width),
        print "Avg Rel Err".rjust(width),
        print "RMS Rel Err".rjust(width),
        print "StdDev Rel Err".rjust(width),
        print
        
        for np in nps:
            for arrKey in keys:
                
                if options.keyIsInt:
                    key = str(arrKey)
                else:
                    key = arrKey
                
                avgerr = relerrsum[np][key] / numerrs[np][key]
                rmserr = math.sqrt(relerrsumsq[np][key] / numerrs[np][key])
                
                nsumsq = relerrsumsq[np][key] * numerrs[np][key]
                sumsum = relerrsum[np][key]*relerrsum[np][key]
                tmp = (nsumsq - sumsum) / (numerrs[np][key]*(numerrs[np][key]-1))
                assert tmp > 0
                stddev = math.sqrt(tmp)
                
                print (str(np)+"-"+key).ljust(width),
                print ("%.3f" % avgerr ).rjust(width),
                print ("%.3f" % rmserr).rjust(width),
                print ("%.3f" % stddev).rjust(width),
                print
    else:
        
        #TODO: add support for choosing which p-cnt to print
        cpus = breakdownres.keys()[0]
        
        print
        print "Result breakdown for "+str(cpus)+" CPUs"
        print
        
        keys = breakdownres[cpus].keys()
        keys.sort()
        
        wls = breakdownres[cpus][keys[0]].keys()
        wls.sort()
        
        caches = breakdownres[cpus][keys[0]][wls[0]].keys()
        caches.sort()        
        
        width = 20
        
        print "".ljust(40),
        print "Estimate".rjust(width),
        print "Actual".rjust(width),
        print "Relative Error".rjust(width)
        
        for k in keys:
            
            print
            print str(k)+" results"
            print
            
            for w in wls:
                bmnames = workloads.getBms(w,cpus)
                for i in range(int(cpus)):
                    for c in caches:
                        
                        print (str(w)+"-"+str(c)+"-"+bmnames[i]).ljust(40),
                        
                        if breakdownres[cpus][k][w] != {}:
                            print str(breakdownres[cpus][k][w][c][i]["estimate"]).rjust(width),                        
                            print str(breakdownres[cpus][k][w][c][i]["actual"]).rjust(width),
                        
                            try:
                                print ("%.2f" % breakdownres[cpus][k][w][c][i]["relerror"]).rjust(width)
                            except TypeError:
                                print str(breakdownres[cpus][k][w][c][i]["relerror"]).rjust(width)
                        else:
                            print "No data..".rjust(width)


if __name__ == "__main__":
    sys.exit(main())