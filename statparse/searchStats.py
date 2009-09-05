#!/usr/bin/python

import sys
import os

from optparse import OptionParser
from optparse import OptionGroup

from statfileParser import ExperimentConfiguration
from statfileParser import StatfileIndex

def parseArgs():
    parser = OptionParser(usage="parseStats.py [key-expression]")
    
    
    # index options
#    indexOptions = OptionGroup(parser, "Index options")
#    indexOptions.add_option("--create-index", action="store", dest="createIndex", type="string", default="", help="Create index with provided name")
#    indexOptions.add_option("--use-index", action="store", dest="useIndex", type="string", default="index.py", help="Use index with given name for searches if it exists")
#    parser.add_option_group(indexOptions)
    
    # search options
    searchOptions = OptionGroup(parser, "Search options")
    searchOptions.add_option("--np", action="store", dest="np", type="int", default=-1, help="Limit the file to configurations with n processors")
    searchOptions.add_option("--architecture", action="store", dest="architecture", type="string", default="*", help="Limit the file to configurations with this memory system architecture")
    searchOptions.add_option("--benchmark", action="store", dest="benchmark", type="string", default="*", help="Only present the results for this benchmark")
    searchOptions.add_option("--workload", action="store", dest="workload", type="string", default="*", help="Only present the results for this benchmark")
    searchOptions.add_option("--other-limits", action="store", dest="otherLimits", type="string", default="", help="Only print configs matching key and value. Format: key1,val1:key2,val2:...")
    searchOptions.add_option("--search-file", action="store", dest="searchFile", type="string", default="", help="Search after key in this file")
    parser.add_option_group(searchOptions)
    
    # Other options
    otherOptions = OptionGroup(parser, "Other options")
    otherOptions.add_option("--orderfile", action="store", dest="orderFile", type="string", default="statsDumpOrder.txt", help="Dump order file to use in single file mode")
    otherOptions.add_option("--width", action="store", dest="width", type="int", default=30, help="Width of each result column")
    otherOptions.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only print search results")
    parser.add_option_group(otherOptions)
    
    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Error: wrong number of arguments"
        print "Usage: "+parser.usage
        sys.exit(-1)
    
    params = {}
    if opts.architecture == "":
        params["MEMORY-SYSTEM"] = opts.architecture
        
    if opts.otherLimits != "":
        try:
            otherparams = opts.otherLimits.split(":")
            for pstr in otherparams:
                key,value = pstr.split(",")
                params[key] = value
        except:
            print "Could not parse parameter string "+opts.otherLimits
            sys.exit(-1)
    
    searchConfig = ExperimentConfiguration(opts.np, params, opts.benchmark, opts.workload)
    
    return opts, args, searchConfig

def main():
    
    opts, args, searchConfig = parseArgs()
    
    if not opts.quiet:
        print
        print "M5 Statistics Search"
        print
    
    if opts.searchFile != "":
        
        indexmodule = "index-"+os.path.basename(opts.searchFile).split(".")[0]
        indexmodulename = indexmodule+".py"
        
        if os.path.exists(indexmodulename):
            if not opts.quiet:
                print "Index exists, loading for file "+indexmodulename
            index = StatfileIndex(indexmodule)
            if not opts.quiet:
                print "Done!"
        else:
            index = StatfileIndex()
            if opts.np == -1 or opts.workload == "*":
                print "Options --np and --workload are required for single experiment parsing"
                sys.exit(-1)
            
            if not opts.quiet:
                print "Index does not exist, generating it..."
            index.addFile(opts.searchFile, opts.orderFile, opts.np, opts.workload)
            if not opts.quiet:
                print "Done!"
            
            if not opts.quiet:
                print "Storing index in file "+indexmodulename+" for future use"
            
            index.dumpIndex(indexmodule)
            if not opts.quiet:
                print "Done!"
            
        
        matchingConfigs = index.findConfiguration(searchConfig)
        results = index.searchForValues(args[0], matchingConfigs)
        
        statkeys = results.keys()
        statkeys.sort()
        
        for statkey in statkeys:
            for config in results[statkey]:
                print statkey.ljust(opts.width),
                print config.toString().ljust(opts.width),
                print ("%.2f" % results[statkey][config]).ljust(opts.width)
        
    else:
        if not opts.quiet:
            print "No filename provided, assuming experiment parse"
        if not os.path.exists("pbsconfig.py"):
            print "File not found: pbsconfig.py"
            print "Use the --search-file option to search a specific file"
            sys.exit(-1)
            
        import pbsconfig
        
        #TODO: generate index-id based on fixed parameters
        
        print "Experimentparsing not implemented"
        

if __name__ == '__main__':
    main()