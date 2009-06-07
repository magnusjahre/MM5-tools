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
    np = -1
    
    def __init(self):
        pass
    
    def parseCommandline(self, argv):
        parser = OptionParser(usage="%prog [options] baseline-dir result-dir [result-dir ...]")
        parser.add_option("-s", "--statistic-pattern", action="store", type="string", dest="statPattern", default="COM:IPC", help="the pattern to retrieve from the simulation results")
        parser.add_option("-k", "--key-pattern", action="store", type="string", dest="keyPattern", default=".*", help="only return experiments where the key matches the provided pattern")
        parser.add_option("-c", "--compare-to-spm", action="store_true", dest="compareToSPM", default=False, help="present results relative to single program mode")
        parser.add_option("-a", "--compare-absolute", action="store_true", dest="compareAbsolute", default=False, help="present absolute diffrence rather than relative (wtr SPM)")
        parser.add_option("--spm-pattern", action="store", dest="spmPattern", default="", help="the pattern to search for in single program mode")
        parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="print progress information")
        parser.add_option("--np", action="store", type="int", dest="np", default=4, help="only return results for this number of CPUs")

        options,args = parser.parse_args()
        
        self.options = options
        self.args = args
        
        self.np = options.np
        
        if len(self.args) < 1:
            print "Parse error: at least one directory must be provided"
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
            
            if keypat.findall(key) != [] and np == self.np:
                
                
                if self.options.verbose:
                    print "Searching in experiment "+id
                
                wl = pbsconfig.get_workload(config)
                resfilename, alonefiles = parsemethods.getFilenames(pbsconfig, cmd, config, np)
                
                sharedResult = parsemethods.findPattern(self.options.statPattern, resfilename, self.options.verbose)
                
                if sharedResult == {}:
                    print "Shared pattern search for pattern .*\..*"+self.options.statPattern+".* did not return any results, quitting"
                    sys.exit(-1)
                
                aloneResult = {}
                
                if self.options.compareToSPM:
                    
                    cpuID = 0
                    for afile in alonefiles:
                        if self.options.spmPattern == "":
                            aresults = parsemethods.findPattern(self.options.statPattern, afile, self.options.verbose)
                            
                            for aresult in aresults:
                                if aresult.startswith("detailedCPU"):
                                    unifiedkey = string.replace(aresult, "detailedCPU0", "detailedCPU"+str(cpuID))
                                elif aresult.endswith("_[0-9]"):
                                    print "detected per cpu pattern, not implemented"
                                    assert False
                                else:
                                    unifiedkey = aresult+"_"+str(cpuID)
                                
                                aloneResult[unifiedkey] = aresults[aresult]
                            
                        else:
                            aresults = parsemethods.findPattern(self.options.spmPattern, afile, self.options.verbose)
                            print "Different SPM queue not implemented"
                            assert False
                        
                            
                        cpuID = cpuID + 1
                
                    
                finalRes = {}
                if aloneResult != {}:
                    for sharedKey in sharedResult:
                        
                        if sharedKey not in aloneResult:
                            print "Error: Shared key "+sharedKey+" does not match any SPM keys"
                            print "       Candidates are: "+str(aloneResult.keys())
                            sys.exit(-1)
                        
                        if self.options.compareAbsolute:
                            try:
                                finalRes[sharedKey] = float(sharedResult[sharedKey]) - float(aloneResult[sharedKey])
                            except:
                                finalRes[sharedKey] = "N/A"
                        else:
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
            
    def summarizeDirectoryData(self):
        
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
    
    def summarizeKeyData(self):
        
        assert len(self.results.keys()) == 1
        directory = self.results.keys()[0]
        
        keys = self.results[directory].keys()
        keys.sort()
                
        wls = self.results[directory][keys[0]].keys()
        wls.sort()
        
        patterns = []
        for pat in self.results[directory][keys[0]][wls[0]]:
            patterns.append(pat)
        patterns.sort()
        
        summary = []
        for wl in wls:
            for pat in patterns:
                title = wl+"-"+pat
                data = []
                for k in keys:
                    data.append(self.results[directory][k][wl][pat])
                summary.append( (title, data) )
        
        return keys, summary
    
    def printSummary(self, titles, summary, useLegend):
        
        textwidth = len(summary[0][0])+2
        datawidth = 20
        
        print "".ljust(textwidth),
        for t in titles:
            if useLegend:
                print str(self.legend[t]).rjust(datawidth),
            else:
                print str(t).rjust(datawidth),
        print
        
        for key, data in summary:
            print str(key).ljust(textwidth),
            for d in data:
                try:
                    print ("%.3f" % d).rjust(datawidth),
                except:
                    print str(d).rjust(datawidth),
            print 
        
        if useLegend:
            print
            print "Legend"
            for t in titles:
                print t.ljust(textwidth),
                print (self.legend[t]).rjust(datawidth)
             

def main(argv):
    
    results = CompareResults()
    results.parseCommandline(argv)
    
    results.retrieveResults()
    
    if results.numDirs > 1:
        titles, summary = results.summarizeDirectoryData()
        results.printSummary(titles, summary, True)
    else:
        titles, summary = results.summarizeKeyData()
        results.printSummary(titles, summary, False)
    
    

if __name__ == "__main__":
    sys.exit(main(sys.argv))