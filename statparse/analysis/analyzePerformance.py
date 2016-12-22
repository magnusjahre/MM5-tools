#!/usr/bin/env python

import sys
from optparse import OptionParser
from statparse.tracefile.tracefileData import TracefileData
from workloadfiles.workloads import Workloads, getWLIdent
from statparse.printResults import numberToString, printData

def parseArgs():
    
    parser = OptionParser(usage="analyzePerformance.py [options] np experiment-directory")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--outfile", action="store", dest="outfile", default="", help="Write output to this file")
    opts, args = parser.parse_args()
    
    if len(args) != 2:
        print "Command line error, usage:"
        print parser.usage
        sys.exit()
    
    np = int(args[0])
    wl = getWLIdent(args[1])
    
    varargstr = "-".join(args[1].split("-")[7:])
    varargstr = varargstr.replace("/","")
    
    return opts, np, wl, varargstr,args[1]

def getPrivModeDirectory(varargstr, wl, bm, bmID, np):
    return "-".join(["res", str(np), wl, bm, str(bmID), varargstr])

def getTraceData(key, tracepath):
    trace = TracefileData(tracepath)
    trace.readTracefile()
    colid = trace.findColumnID(key, -1)
    return trace.getColumn(colid)

def getSpeedupCurve(smpath, pmpath):
    
    smdata = getTraceData("Shared IPC", smpath)
    pmdata = getTraceData("Measured Alone IPC", pmpath)
    
    assert len(pmdata) <= len(smdata)
    
    speedups = [0 for i in range(len(pmdata))]
    for i in range(len(pmdata)):
        assert pmdata[i] > 0
        speedups[i] = smdata[i] / pmdata[i]
        
    return speedups

def computeSTP(speedups):
    return sum(speedups)

def computeHMoS(speedups):
    inverse = [1/s for s in speedups]
    return float(len(speedups)) / sum(inverse)

def printOutput(smCC, speedupCurves, bms, opts):
    data = [[""] + bms + ["STP", "HMoS"]]
    leftJust = [False for d in data[0]]
    
    for i in range(len(smCC)):
        line = [numberToString(smCC[i], 0)]
        
        doMetrics = True
        speedups = [0 for x in range(len(bms))]
        for j in range(len(bms)):
            if i < len(speedupCurves[j]):
                line.append(numberToString(speedupCurves[j][i], opts.decimals))
                speedups[j] = speedupCurves[j][i]
            else:
                line.append("0")
                doMetrics = False
                
        if doMetrics:
            line.append(numberToString(computeSTP(speedups), opts.decimals))
            line.append(numberToString(computeHMoS(speedups), opts.decimals))
        else:
            line += ["0", "0"]
        
        data.append(line)

    outfile = sys.stdout
    if opts.outfile != "":
        outfile = open(opts.outfile, "w")

    printData(data, leftJust, outfile, opts.decimals)
    

def main():
    opts, np, wl, varargstr, expdir = parseArgs()
    workloads = Workloads()
    bms = workloads.getBms(wl, np)
    
    smpath = expdir+"/globalPolicyCommittedInsts0.txt"
    smCC = getTraceData("Tick", smpath)
    
    speedupCurves = []
    for bmID in range(len(bms)):
        smpath = expdir+"/globalPolicyCommittedInsts"+str(bmID)+".txt"
        pmpath = getPrivModeDirectory(varargstr, wl, bms[bmID], bmID, np)+"/globalPolicyCommittedInsts0.txt"
        
        speedupCurves.append(getSpeedupCurve(smpath, pmpath))
    
    printOutput(smCC, speedupCurves, bms, opts)

if __name__ == '__main__':
    main()