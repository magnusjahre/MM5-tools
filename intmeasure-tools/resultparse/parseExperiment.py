#!/usr/bin/python

import sys
from optparse import OptionParser
import pbsconfig
import re

class ExperimentResults:
    
    resultstore = {}
    
    def __init__(self):
        pass
        
    def add(self, cmd, config, searchpattern, keypattern):
        key = pbsconfig.get_key(cmd, config)
        id = pbsconfig.get_unique_id(config)
        wl = pbsconfig.get_workload(config)
        
        if re.findall(keypattern, key) != []:
            resfilename = id+"/"+id+".txt"
            resfile = open(resfilename)
            restext = resfile.read()
            resfile.close()
            
            results = re.findall(".*"+searchpattern+".*", restext)
            
            for res in results:
                splitted = res.split()
                reskey = splitted[0]
                try:
                    result = float(splitted[1])
                except:
                    result = "N/A"
                    
                if key not in self.resultstore:
                    self.resultstore[key] = {}
                    
                if wl not in self.resultstore[key]:
                    self.resultstore[key][wl] = {}
                    
                if reskey in self.resultstore[key][wl]:
                    print "Parse error: key "+str(reskey)+" is already present under "+str(key)+"-"+str(wl)
                    sys.exit(-1)
                    
                self.resultstore[key][wl][reskey] = result
                
    def dump(self, width, decimals):
        keys = self.resultstore.keys()
        keys.sort()
        
        wls = self.resultstore[keys[0]].keys()
        wls.sort()
        
        reskeys = self.resultstore[keys[0]][wls[0]].keys()
        reskeys.sort()
        
        for k in keys:
            for wl in wls:
                tmpkeys = self.resultstore[k][wl].keys()
                tmpkeys.sort()
                for i in range(len(tmpkeys)):
                    assert tmpkeys[i] == reskeys[i]
        
        print "".ljust(width),
        for k in keys:
            print str(k).rjust(width),
        print
        
        for wl in wls:
            if len(reskeys) == 1:
                print str(wl).ljust(width),
                for k in keys:
                    try:
                        print ("%."+str(decimals)+"f" % self.resultstore[k][wl][reskeys[0]]).rjust(width),
                    except:
                        print str(self.resultstore[k][wl][reskeys[0]]).rjust(width),
                print 
            else:
                print "FATAL: mult-result handling not implemented"
                sys.exit(-1)

def main(args):
    
    usage = "usage: %prog [options] <search-pattern>"
    parser = OptionParser(usage=usage,prog="parseExperiment.py")
    parser.add_option("-k", "--key-pattern", action="store", type="string", default=".*", dest="keypattern", help="Only return results with keys matching this regular expression")
    
    options,args =parser.parse_args() 
    
    if(len(args) != 1):
        print "Search pattern not specified"
        sys.exit(-1)
    
    searchpattern = args[0]
    
    results = ExperimentResults()
    
    for cmd, config in pbsconfig.commandlines:
        results.add(cmd, config, searchpattern, options.keypattern)
        
        
    results.dump(35,4)

if __name__ == "__main__":
    sys.exit(main(sys.argv))