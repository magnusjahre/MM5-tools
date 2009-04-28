#!/usr/bin/python

import sys
import os
import re
from optparse import OptionParser 
import parsemethods

class CompareResults:
    
    options = {}
    args = []
    results = {}
    
    def __init(self):
        pass
    
    def parseCommandline(self, argv):
        parser = OptionParser(usage="%prog [options] baseline-dir result-dir [result-dir ...]")
        parser.add_option("-s", "--statistic-pattern", action="store", type="string", dest="statPattern", default="COM:IPC", help="the pattern to retrieve from the simulation results")
        parser.add_option("-k", "--key-pattern", action="store", type="string", dest="keyPattern", default=".*", help="only return experiments where the key matches the provided pattern")

        options,args = parser.parse_args()
        
        self.options = options
        self.args = args
        
        if len(self.args) < 2:
            print "Parse error: at least two directories must be provided"
            sys.exit(-1)
            
        for dir in args:
            error = False
            if not os.path.exists(dir+"/pbsconfig.py"):
                print "Parse error: directory "+str(dir)+" does not have a pbsconfig.py file"
                error = True
            if error:
                sys.exit(-1)
                
    def getDirectoryResults(self, dirname):
        
        print "Retrieving results from directory "+os.getcwd()
        
        assert dirname not in self.results
        self.results[dirname] = {}
        
        sys.path.append(os.getcwd())
        import pbsconfig
        
        keypat = re.compile(self.options.keyPattern)
        
        for cmd, config in pbsconfig.commandlines:
            id = pbsconfig.get_unique_id(config)
            key = pbsconfig.get_key(cmd,config)
            
            if keypat.findall(key) != []:
                print "Searching in experiment "+id
                
                
                wl = pbsconfig.get_workload(config)
                resfilename = id+"/"+id+".txt"
                result = parsemethods.findPattern(self.options.statPattern, resfilename)
                
                if key not in self.results[dirname]:
                    self.results[dirname][key] = {}
                    
                assert wl not in self.results[dirname][key]
                self.results[dirname][key][wl] = result
                
    def retrieveResults(self):
        
        workdir = os.getcwd()
        
        for dir in self.args:
            os.chdir(dir)
            self.getDirectoryResults(dir)
            os.chdir(workdir)
            
    def summarizeData(self):
        
        summary = []
        
        dirs = self.results.keys()
        dirs.sort()
        
        keys = self.results[dirs[0]].keys()
        for d in self.results:
            assert self.results[d].keys() == keys
        keys.sort()
        
        wls = self.results[dirs[0]][keys[0]].keys()
        wls.sort()
        
        for k in keys:
            for wl in wls:
                
                name = str(k+"-"+wl)
                
                patterns = []
                for pat in self.results[dirs[0]][k][wl]:
                    patterns.append(pat)
                
                patterns.sort()
                
                for pat in patterns:
                    title = (name+"-"+pat)
                    data = []
                    for dir in dirs:
                        assert pat in self.results[dir][k][wl]
                        data.append(self.results[dir][k][wl][pat])
                    
                    summary.append( (title, data) )
                        
        return dirs, summary
    
    def printSummary(self, titles, summary):
        
        width = 40
        
        print "".ljust(width),
        for t in titles:
            print str(t).rjust(width),
        print
        
        for key, data in summary:
            print str(key).ljust(width),
            for d in data:
                try:
                    print ("%.3f" % d).rjust(width),
                except:
                    print str(d).rjust(width),
            print 
        

def main(argv):
    
    results = CompareResults()
    results.parseCommandline(argv)
    
    results.retrieveResults()
    
    titles, summary = results.summarizeData()
    
    results.printSummary(titles, summary)
    

if __name__ == "__main__":
    sys.exit(main(sys.argv))