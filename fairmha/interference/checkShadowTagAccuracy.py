#!/usr/bin/python

import sys
import pbsconfig
import re

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
            
        filenames.append( (np, key, sfilename, afilenames) )
            
    return filenames

def find(pattern, filename, cpuid = -1):
    
    file = open(filename)
    text = file.read()
    file.close()
    
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

def main():
    
    relerrsum = {}
    relerrsumsq = {}
    numerrs = {}
    
    missPattern = re.compile("Shared.*misses_per_cpu_.*")
    aloneMissPattern = re.compile("Shared.*misses_per_cpu.*")
    shadowMissPattern = re.compile("Shared.*cpu_extra_misses_.*")
    
    for np, key, sharedfile, alonefiles in generateFilenames():
    
        if np not in relerrsum:
            relerrsum[np] = {}
            relerrsumsq[np] = {}
            numerrs[np] = {}
            
        if key not in relerrsum[np]:
            relerrsum[np][key] = 0
            relerrsumsq[np][key] = 0
            numerrs[np][key] = 0
            
        sharedMisses = find(missPattern, sharedfile)
        shadowMisses = find(shadowMissPattern, sharedfile)
        aloneMisses = [find(aloneMissPattern, alonefiles[i], i) for i in range(np) ]
    
        for cachekey in sharedMisses:
            for cpukey in sharedMisses[cachekey]:
                
                est = sharedMisses[cachekey][cpukey] - shadowMisses[cachekey][cpukey]
                err = float(est) - float(float(aloneMisses[cpukey][cachekey][cpukey]))
                relErr = float(err)/float(sharedMisses[cachekey][cpukey])
                            
                relerrsum[np][key] += relErr
                relerrsumsq[np][key] += relErr**2
                numerrs[np][key] += 1.0
    
    nps = relerrsum.keys()
    nps.sort()
    keys = relerrsum[nps[0]].keys()
    keys.sort()
    
    width = 30
    
    print "".ljust(width),
    print "Avg Rel Err".rjust(width),
    print "RMS Rel Err".rjust(width),
    print
    
    for np in nps:
        for key in keys:
            
            avgerr = relerrsum[np][key] / numerrs[np][key]
            rmserr = relerrsumsq[np][key] / numerrs[np][key]
            
            print (str(np)+"-"+key).ljust(width),
            print ("%.3f" % avgerr ).rjust(width),
            print ("%.3f" % rmserr).rjust(width),
            print

if __name__ == "__main__":
    sys.exit(main())