#!/usr/bin/python

from optparse import OptionParser
import sys
import os

BUFFER_SIZE = 2**20

def parseArgs():
    parser = OptionParser(usage="verifyCopy.py dir1 dir2")
    
    parser.add_option("--verbose", action="store_true", dest="verbose", default=False, help="Verbose output")

    opts, args = parser.parse_args()
    
    if(len(args) != 2):
        print "Command line error"
        print "Usage: "+parser.usage
        sys.exit()
    
    return opts, args

def diff(file1name, file2name, verbose):
    if verbose:
        print "Checking files "+file1name+" "+file2name
        
    file1 = open(file1name, "rb")
    file2 = open(file2name, "rb")
    
    data1 = file1.read(BUFFER_SIZE)
    data2 = file2.read(BUFFER_SIZE)
    
    while data1 != "":
        
        if len(data1) != len(data2):
            print "Files "+file1name+" and "+file2name+" differ!"
            return 
        
        for i in range(len(data1)):
            if data1[i] != data2[i]:
                print "Files "+file1name+" and "+file2name+" differ!"
                return 
        
        data1 = file1.read(BUFFER_SIZE)
        data2 = file2.read(BUFFER_SIZE)
    

def checkDirectory(dir1, dir2, verbose):
    
    if verbose:
        print "Checking directory "+dir1
    
    dir1files = os.listdir(dir1)
    dir2files = os.listdir(dir2)
    
    for file in dir1files:
        name, ext = os.path.splitext(file)  
        if os.path.isdir(dir1+"/"+file):
            
            if file in dir2files:            
                checkDirectory(dir1+"/"+file, dir2+"/"+file, verbose)
            else:
                print "Subdirectory "+file+" is missing from "+dir2
        
        elif ext == ".bin":
            
            if file in dir2files:            
                diff(dir1+"/"+file, dir2+"/"+file, verbose)
            else:
                print "Binary file "+file+" is missing from "+dir2

def main():
    
    opts, args = parseArgs()
    
    dir1 = args[0]
    dir2 = args[1]
    
    if not os.path.exists(dir1):
        print "Error: "+dir1+" does not exist..."
    
    if not os.path.exists(dir2):
        print "Error: "+dir2+" does not exist..."
    
    print
    print "Comparing binary files in directory "+dir1+" with "+dir2+" recursively"
    print
    
    checkDirectory(dir1, dir2, opts.verbose)
    
    return 0

if __name__ == '__main__':
    main()