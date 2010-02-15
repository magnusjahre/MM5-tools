#!/usr/bin/env python

from optparse import OptionParser
from statparse.util import fatal

from statparse.plotResults import plotRawBoxPlot

import optcomplete

def parseArgs():
    parser = OptionParser(usage="plotDataFile.py [options] filename")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--rotate", action="store", dest="rotate", type="int", default=0, help="Rotate labels by x degrees")
    parser.add_option("--margins", action="store", dest="margins", type="string", default="", help="Comma separated plot margins: left,right,top,bottom ")
    parser.add_option("--outfile", action="store", dest="outfile", type="string", default="plot.pdf", help="Output filename (Default: plot.pdf)")
    parser.add_option("-y", "--ytitle", action="store", dest="ytitle", type="string", default="Y axis title")
    parser.add_option("-x", "--xtitle", action="store", dest="xtitle", type="string", default="X axis title")
    parser.add_option("--remove-columns", action="store", dest="removeColumns", type="string", default="", help="Comma separated list of columns to remove (Zero indexed)")

    optcomplete.autocomplete(parser, optcomplete.AllCompleter())

    opts, args = parser.parse_args()
    
    try:
        datafile = open(args[0])
    except:
        try:
            fatal("Cannot open file "+str(args[0]))
        except:
            print parser.usage
            fatal("Command line error")
    
    return opts, args, datafile
    
def readFile(datafile, removeColumns):
    header = datafile.readline().strip().split("  ")
    data = []
    for l in datafile:
        rawline = l.strip().split()
        tmp = [rawline[0]]
        for e in rawline[1:]:
            try:
                tmp.append(float(e))
            except:
                fatal("Parse error, cannot convert "+e+" to float")
        data.append(tmp)
        
    if len(header) != len(data[0])-1:
        fatal("Datafile parse error, header has length "+str(len(header))+", data length is "+str(len(data[0])))
    
    if removeColumns != "":
        colstrs = removeColumns.split(",")
        removelist = [float(s) for s in colstrs]
        
        newheader = []
        for i in range(len(header)):
            if i not in removelist:
                newheader.append(header[i])
        
        newdata = []
        for l in data:
            newline = [l[0]]
            for i in range(len(header)):
                if i not in removelist:
                    newline.append(l[i+1])
            newdata.append(newline)
        
        return newheader, newdata
    
    return header, data

def createBoxWhiskerData(rawdata, datacols):
    bwdata =[[] for i in range(datacols+1)]
    
    for l in rawdata:
        for i in range(datacols+1):
            bwdata[i].append(l[i])

    return bwdata[1:]
    
def main():

    opts, args, datafile = parseArgs()
    
    print "Data file plot of file "+args[0]
    print "Processing data..."
    
    header, data = readFile(datafile, opts.removeColumns)
    
    bwdata = createBoxWhiskerData(data, len(header))
    
    if opts.margins != "":
        margList = opts.margins.split(",")
        try:
            margs = (float(margList[0]),float(margList[1]),float(margList[2]),float(margList[3]))
        except:
            fatal("Margin plot error")
    else:
        margs = None
    
    print "Plotting data to file "+opts.outfile+"..."
    
    plotRawBoxPlot(bwdata,
                   titles=header,
                   rotate=opts.rotate,
                   plotmargins=margs,
                   filename=opts.outfile,
                   xlabel=opts.xtitle,
                   ylabel=opts.ytitle)

    print "Done!"

if __name__ == '__main__':
    main()