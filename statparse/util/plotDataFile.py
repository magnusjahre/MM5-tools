#!/usr/bin/env python

from optparse import OptionParser
from statparse.util import fatal

from statparse.plotResults import plotRawBoxPlot, plotRawLinePlot

import optcomplete

def parseArgs():
    parser = OptionParser(usage="plotDataFile.py [options] filename")

    plotTypes = ["boxplot", "lineplot"]

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--rotate", action="store", dest="rotate", type="int", default=0, help="Rotate labels by x degrees")
    parser.add_option("--legend-columns", action="store", dest="legendColumns", type="int", default=2, help="Number of columns in legend")
    parser.add_option("--margins", action="store", dest="margins", type="string", default="", help="Comma separated plot margins: left,right,top,bottom ")
    parser.add_option("--outfile", action="store", dest="outfile", type="string", default=None, help="Output filename (Default: plot.pdf)")
    parser.add_option("--plot-type", action="store", dest="plotType", type="string", default="boxplot", help="Output filename (Default: boxplot, alternatives "+str(plotTypes)+")")
    parser.add_option("-y", "--ytitle", action="store", dest="ytitle", type="string", default="Y axis title", help="Y axis title")
    parser.add_option("-x", "--xtitle", action="store", dest="xtitle", type="string", default="X axis title", help="X axis title")
    parser.add_option("--yrange", action="store", dest="yrange", type="string", default=None, help="Comma separated min,max pair")
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
    
    if opts.plotType not in plotTypes:
        fatal("Plot type needs to be one of "+str(plotTypes))
    
    return opts, args, datafile
    
def readFile(datafile, removeColumns):
    header = datafile.readline().strip().split()
    data = []
    for l in datafile:
        rawline = l.strip().split()
        tmp = [rawline[0]]
        
        error = False
        for e in rawline[1:]:
            if e == "N/A":
                error = True
                continue
            elif e == "RM":
                error = True
                continue
            
            try:
                tmp.append(float(e))
            except:
                fatal("Parse error, cannot convert "+e+" to float")
        
        if not error:
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

def createDataSeries(rawdata, datacols):
    dataseries =[[] for i in range(datacols+1)]
    
    for l in rawdata:
        for i in range(datacols+1):
            dataseries[i].append(l[i])

    return dataseries
    
def main():

    opts, args, datafile = parseArgs()
    
    print "Data file plot of file "+args[0]
    print "Processing data..."
    
    header, data = readFile(datafile, opts.removeColumns)
    
    dataseries = createDataSeries(data, len(header))
    
    if opts.margins != "":
        margList = opts.margins.split(",")
        try:
            margs = (float(margList[0]),float(margList[1]),float(margList[2]),float(margList[3]))
        except:
            fatal("Margin plot error")
    else:
        margs = None
    
    if opts.outfile != None:
        print "Plotting data to file "+opts.outfile+"..."
    else:
        print "Showing plot..."
    
    if opts.plotType == "lineplot":
        plotRawLinePlot(dataseries[0], dataseries[1:],
                        titles=header,
                        filename=opts.outfile,
                        xlabel=opts.xtitle,
                        ylabel=opts.ytitle,
                        legendColumns=opts.legendColumns,
                        yrange=opts.yrange)
    else:
        assert opts.plotType == "boxplot"
        plotRawBoxPlot(dataseries[1:],
                       titles=header,
                       rotate=opts.rotate,
                       plotmargins=margs,
                       filename=opts.outfile,
                       xlabel=opts.xtitle,
                       ylabel=opts.ytitle)

    print "Done!"

if __name__ == '__main__':
    main()