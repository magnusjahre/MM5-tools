#!/usr/bin/python

from optparse import OptionParser
import sys

'''
Created on Aug 5, 2010

@author: jahre
'''

class Instruction:
    DEBUG_SYMBOL_OFFSET = 4
    MNEMONIC_OFFSET = 6
    REGISTER_OFFSET= 7
    DATA_OFFSET = 11
    
    def __init__(self, rawArray):
        self.debugSymbol = rawArray[self.DEBUG_SYMBOL_OFFSET]
        self.mnemonic = rawArray[self.MNEMONIC_OFFSET]
        self.register = rawArray[self.REGISTER_OFFSET]
        if self.DATA_OFFSET < len(rawArray):
            self.data = rawArray[self.DATA_OFFSET]
        else:
            self.data = "-"

    def __str__(self):
        retstr = ""
        retstr += self.debugSymbol.ljust(15)
        retstr += self.mnemonic.ljust(10)
        retstr += self.register.ljust(20)
        retstr += self.data.ljust(20)
        
        return retstr


def parseArgs():
    
    parser = OptionParser(usage="compareInstTraces.py [options] file1 file2")
    #otherOptions.add_option("--only-index", action="store", dest="onlyIndexPat", default=".*", help="A comma-separated list of patterns to put in the index")
    opts, args = parser.parse_args()
    
    if len(args) != 2:
        print "Usage:"
        print parser.usage
        sys.exit()
    
    file1 = open(args[0])
    file2 = open(args[1])
    
    return file1, file2, opts

def isInt(intstr):
    try:
        intval = int(intstr)
        return True
    except:
        pass
    return False

def parseFile(file):
    instructions = []
    
    for line in file:
        splitted = line.split()
        
        if splitted == []:
            continue
        
        cc = splitted[0].replace(":","")
        if isInt(cc):
            instructions.append(Instruction(splitted))
    
    return instructions

def main():
    file1, file2, opts = parseArgs()
    
    instList1  = parseFile(file1)
    
    print instList1[0]
    print instList1[-1]
    
    file1.close()
    file2.close()

if __name__ == '__main__':
    main()