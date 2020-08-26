#!/usr/bin/env python
import sys
import os
import glob

def main():

    path = "res-4-*-b-b-cpl/globalPolicyCommittedInsts0.txt"
    
    for filename in glob.glob(path):
        command = "retrieveData.py " + filename
        os.system(command)
        command = "addIPCPrStalls.py " + filename
        os.system(command)
        command = "addVariousStallCycles.py " + filename
        os.system(command)
        
if __name__ == '__main__':
    main()