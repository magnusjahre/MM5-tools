#!/usr/bin/python

import pbsconfig
import sys
from optparse import OptionParser

def main():
    
    parser = OptionParser(usage="%prog [options] dictionary key width")
    options,args = parser.parse_args()
    
    if(len(args) != 3):
        print "You must provide a dictionary, a key and width"
        return -1
    
    dictionaryName = args[0]
    dictionaryKey = args[1]
    width = int(args[2])
        
    resultmodules = {}
    
    for cmd, config in pbsconfig.commandlines:
        key = pbsconfig.get_key(cmd,config)
        
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
                data[key][parameter] = resultmodules[key].errorRMS[parameter][dictionaryKey]
        else:
            print "Dictionaryname not supported"
            return -1
    
    
    dkeys = data.keys()
    dkeys.sort()
    
    paramkeys = data[dkeys[0]].keys()
    paramkeys.sort()
    
    print "".ljust(width),
    for k in dkeys:
        print str(k).rjust(width),
    print

    for pk in paramkeys:
        print str(pk).ljust(width),
        for dk in dkeys:
            print ("%.3f" % data[dk][pk]).rjust(width),
        print
            
    
        
        
    
    
    
    return 0

if __name__ == "__main__":
    sys.exit(main())