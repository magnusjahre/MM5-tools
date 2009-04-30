#!/usr/bin/python

import sys
import os
import re
import string
from optparse import OptionParser 
import fairmha.resultparse.parsemethods as parsemethods

class CompareResults:
    
    options = {}
    args = []
    results = {}
    legend = {}
    numDirs = 0
    
    def __init(self):
        pass
    
    def parseCommandline(self, argv):
        parser = OptionParser(usage="%prog [options] baseline-dir result-dir [result-dir ...]")
        parser.add_option("-s", "--statistic-pattern", action="store", type="string", dest="statPattern", default="COM:IPC", help="the pattern to retrieve from the simulation results")
        parser.add_option("-k", "--key-pattern", action="store", type="string", dest="keyPattern", default=".*", help="only return experiments where the key matches the provided pattern")
        parser.add_option("-c", "--compare-to-spm", action="store_true", dest="compareToSPM", default=False, help="present results relative to single program mode")
        parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="print progress information")

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
        
        if self.options.verbose:
            print "Retrieving results from directory "+os.getcwd()
        
        self.numDirs += 1
        self.legend[dirname] = "Dir-"+str(self.numDirs)
        
        assert dirname not in self.results
        self.results[dirname] = {}
        
        oldpath = sys.path[:]
        sys.path.append(os.getcwd())
        import pbsconfig
        
        keypat = re.compile(self.options.keyPattern)
        
        for cmd, config in pbsconfig.commandlines:
            id = pbsconfig.get_unique_id(config)
            key = pbsconfig.get_key(cmd,config)
            np = pbsconfig.get_np(config)
            
            if keypat.findall(key) != []:
                
                
                if self.options.verbose:
                    print "Searching in experiment "+id
                
                wl = pbsconfig.get_workload(config)
                resfilename, alonefiles = parsemethods.getFilenames(pbsconfig, cmd, config, np)
                
                sharedResult = parsemethods.findPattern(self.options.statPattern, resfilename, self.options.verbose)
                
                aloneResult = {}
                
                if self.options.compareToSPM:
                    
                    cpuID = 0
                    for afile in alonefiles:
                        
                        aresults = parsemethods.findPattern(self.options.statPattern, afile, self.options.verbose)
                        for aresult in aresults:
                            if aresult.startswith("detailedCPU"):
                                unifiedkey = string.replace(aresult, "detailedCPU0", "detailedCPU"+str(cpuID))
                            elif aresult.endswith("_[0-9]*"):
                                print "detected per cpu pattern, not implemented"
                                assert False
                            else:
                                unifiedkey = aresult+"_"+str(cpuID)
                                
                            aloneResult[unifiedkey] = aresults[aresult]
                            
                        cpuID = cpuID + 1
                    
                finalRes = {}
                if aloneResult != {}:
                    for sharedKey in sharedResult:
                        
                        if sharedKey not in aloneResult:
                            print "Error: Shared key "+sharedKey+" does not match any SPM keys"
                            print "       Candidates are: "+str(aloneResult.keys())
                            sys.exit(-1)
                        
                        try:
                            finalRes[sharedKey] = float(sharedResult[sharedKey]) / float(aloneResult[sharedKey])
                        except:
                            finalRes[sharedKey] = "N/A"
                else:
                    finalRes = sharedResult
                    
                if key not in self.results[dirname]:
                    self.results[dirname][key] = {}
                    
                assert wl not in self.results[dirname][key]
                self.results[dirname][key][wl] = finalRes

                
        sys.path[:] = oldpath
                
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
        
        textwidth = 40
        datawidth = 10 
        
        print "".ljust(textwidth),
        for t in titles:
            print str(self.legend[t]).rjust(datawidth),
        print
        
        for key, data in summary:
            print str(key).ljust(textwidth),
            for d in data:
                try:
                    print ("%.3f" % d).rjust(datawidth),
                except:
                    print str(d).rjust(datawidth),
            print 
        
        print
        print "Legend"
        for t in titles:
            print t.ljust(textwidth),
            print (self.legend[t]).rjust(datawidth)
             

def main(argv):
    
    results = CompareResults()
    results.parseCommandline(argv)
    
    results.retrieveResults()
    
    titles, summary = results.summarizeData()
    
    results.printSummary(titles, summary)
    

if __name__ == "__main__":
    sys.exit(main(sys.argv))