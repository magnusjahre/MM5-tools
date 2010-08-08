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
    
    DEBUG_WIDTH = 25
    MNEMONIC_WIDTH = 7
    REGISTER_WIDTH = 20
    DATA_WIDTH = 20 
    
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
        retstr += self.debugSymbol.ljust(self.DEBUG_WIDTH)
        retstr += self.mnemonic.ljust(self.MNEMONIC_WIDTH)
        retstr += self.register.ljust(self.REGISTER_WIDTH)
        retstr += self.data.ljust(self.DATA_WIDTH)
        
        return retstr

    def __eq__(self, other):
        
        if other == None:
            return False
        
        if self.mnemonic == other.mnemonic \
        and self.register == other.register \
        and self.data == other.data:
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
    
    def getProcedureName(self):
        return self.debugSymbol.split("+")[0]

    def getInstStrWidth(self):
        return self.DEBUG_WIDTH+self.MNEMONIC_WIDTH+self.REGISTER_WIDTH+self.DATA_WIDTH

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

def printDiff(id1, inst1, id2, inst2):

    if inst1 == None:
        inst1str = "----- '' ------".ljust(inst2.getInstStrWidth())
    else:
        inst1str = str(inst1)
    
    if inst2 == None:
        inst2str = "----- '' ------".ljust(inst1.getInstStrWidth())
    else:
        inst2str = str(inst2)
    
    print str(id1)+": "+inst1str+" || "+str(id2)+": "+inst2str

def main():
    file1, file2, opts = parseArgs()
    
    instList1 = parseFile(file1)
    instList2 = parseFile(file2)
    
    i = 0
    j = 0
    
    differenceDetected = False
    differenceID = 1
    
    while i < len(instList1) and j < len(instList2):
        if instList1[i] == instList2[j]:
            i += 1
            j += 1
            differenceDetected = False
        else:
            if differenceDetected == False:
                print
                print "Difference number "+str(differenceID)
                print
                differenceID += 1
            
            differenceDetected = True
            if instList1[i].getProcedureName() != instList1[i-1].getProcedureName()\
            and instList1[i-1].getProcedureName() == instList2[j].getProcedureName():
                # advance j through rest of procedure
                printDiff(i, None, j, instList2[j])
                j += 1
            elif instList2[j].getProcedureName() != instList2[j-1].getProcedureName()\
            and instList2[j-1].getProcedureName() == instList1[i].getProcedureName():
                # advance i through rest of procedure
                
                printDiff(i, instList1[i], j, None)
                i += 1
            else:
                # difference but not on procedure call border
                printDiff(i, instList1[i], j, instList2[j])
                i += 1
                j += 1

            
    file1.close()
    file2.close()

if __name__ == '__main__':
    main()