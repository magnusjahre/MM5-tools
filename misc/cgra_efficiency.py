#!/usr/bin/env python

import sys
import math
from optparse import OptionParser
from statparse.printResults import numberToString, printData

def parseArgs():
    
    parser = OptionParser(usage="cgra_efficiency.py [options]")
    parser.add_option("--verbose", '-v', action="store_true", dest="verbose", default=False, help="Print all lines")
    opts, args = parser.parse_args()
    
    if len(args) != 0:
        print "Usage:"
        print parser.usage
        sys.exit()
    
    return opts, args


class CGRAConfig:
    
    def __init__(self, activeFUs, activeSBs):
        
        self.activeFUs = activeFUs
        self.activeSBs = activeSBs
        
        perFUPower = 2.5 #mW
        sbOverhead = 50.0 #mW
        fuOpRate = 0.3333 #GOps / s
        
        self.power = activeFUs*perFUPower + activeSBs*sbOverhead
        
        fuBytesPerOP = 8 #one int read and one int written
        fuBandwidthNeed = fuOpRate*fuBytesPerOP*self.activeFUs #GB/s
        maxBW = 50.0 #GB/s
        
        if fuBandwidthNeed > maxBW:
            self.performance = maxBW / fuBytesPerOP #GOp/s
        else:
            self.performance = fuOpRate*activeFUs #GOp/s
        
        self.powerEfficiency = float(self.performance)/float(self.power*10**-3) #Gop/s/Watt
    
    def getDataLine(self, decimals):
        return [str(self.activeFUs),
                numberToString(self.performance, decimals),
                numberToString(self.power, decimals),
                numberToString(self.powerEfficiency, decimals)]
    
    def __str__(self):
        return "FUs="+str(self.activeFUs)+", SBs="+str(self.activeSBs)+", perf="+str(self.performance)+" GOp/s, power="+str(self.power)+" mW, power efficiency="+str(self.powerEfficiency)+" GOp/s/Watt"

def analyseCGRAs():
    data = []
    fusPerSoftbrain = 20
    numSoftbrains = 8
    for fus in [1] + range(5, (fusPerSoftbrain*numSoftbrains)+1,5):
        activatedSoftbrains = math.ceil(fus / float(fusPerSoftbrain))
        data.append(CGRAConfig(fus, activatedSoftbrains))
    return data

def printCGRAData(data):
    decimals = 2
    
    header = ["", "Performance_(GOps)", "Power_(mW)", "Power_Efficiency_(GOps/W)"]
    justify = [True, False, False, False]
    
    lines = [header]
    for d in data:
        lines.append(d.getDataLine(decimals))
        
    printData(lines, justify, sys.stdout, decimals)

def main():
    opts, args = parseArgs()

    data = analyseCGRAs()
    printCGRAData(data)
        
    
    
if __name__ == '__main__':
    main()