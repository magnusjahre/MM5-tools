#!/usr/bin/env python

from optparse import OptionParser
from statparse.util import fatal
from statparse.util import readDataFile

from statparse.plotResults import plotRawBoxPlot, plotRawLinePlot, plotDataFileBarChart

import optcomplete

def parseArgs():
    parser = OptionParser(usage="plotDataFile.py [options] filename [filename ...]")

    plotTypes = ["boxplot", "lineplot", "bars"]

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--legend-columns", action="store", dest="legendColumns", type="int", default=2, help="Number of columns in legend")
    parser.add_option("--margins", action="store", dest="margins", type="string", default="", help="Comma separated plot margins: left,right,top,bottom ")
    parser.add_option("--outfile", action="store", dest="outfile", type="string", default=None, help="Output filename (Default: plot.pdf)")
    parser.add_option("--plot-type", action="store", dest="plotType", type="string", default="boxplot", help="Output filename (Default: boxplot, alternatives "+str(plotTypes)+")")
    parser.add_option("-y", "--ytitle", action="store", dest="ytitle", type="string", default="Y axis title", help="Y axis title")
    parser.add_option("-x", "--xtitle", action="store", dest="xtitle", type="string", default="X axis title", help="X axis title")
    parser.add_option("--yrange", action="store", dest="yrange", type="string", default=None, help="Comma separated min,max pair")
    parser.add_option("--columns", action="store", dest="columns", type="string", default="", help="Comma separated list of columns to include (Zero indexed)")
    parser.add_option("--errorrows", action="store_true", dest="errorrows", default=False, help="Every second row in the data file is error values")
    parser.add_option("--errorcols", action="store_true", dest="errorcols", default=False, help="Every second column in the data file is error values")
    parser.add_option("--only-type", action="store", dest="onlyType", type="string", default="", help="Only include lines that have a workload key that contains this letter (a, b, c or n)")
    parser.add_option("--avg", action="store_true", dest="avg", default=False, help="Add average as a part of the data set")

    optcomplete.autocomplete(parser, optcomplete.AllCompleter())

    opts, args = parser.parse_args()
    
    datafiles = []
    for a in args:
        try:
            datafiles.append(open(a))
        except:
            try:
                fatal("Cannot open file "+str(a))
            except:
                print parser.usage
                fatal("Command line error")
    
    if opts.plotType not in plotTypes:
        fatal("Plot type needs to be one of "+str(plotTypes))
    
    if opts.plotType != "boxplot" and len(datafiles) > 1:
        fatal("Plotting of multiple data files only make sense for boxplots")
    
    return opts, args, datafiles

def createDataSeries(rawdata, datacols):
    dataseries =[[] for i in range(datacols+1)]
    
    for l in rawdata:
        for i in range(datacols+1):
            dataseries[i].append(l[i])

    return dataseries
    
def main():

    opts, args, datafiles = parseArgs()
    
    print "Data file plot script"
    
    dataseries = []
    header = []
    for i in range(len(datafiles)):
        print "Processing file plot of file "+args[i]
        
        thisHeader, thisData = readDataFile(datafiles[i], opts.columns, opts.onlyType)
        series = createDataSeries(thisData, len(thisHeader))
        
        if opts.plotType != "boxplot":
            dataseries = series
            header = thisHeader
        else:
            for s in series[1:]:
                dataseries.append(s)
                
            for h in thisHeader:
                header.append(h)
    
    if opts.avg:
        for i in range(len(dataseries)):
            if i == 0:
                dataseries[i].append("AVG")
            else:
                avg = float(sum(dataseries[i])) / float(len(dataseries[i]))
                dataseries[i].append(avg)
    
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
        
    elif opts.plotType == "bars":
        plotDataFileBarChart(dataseries[0],
                             dataseries[1:],
                             header,
                             filename=opts.outfile,
                             xlabel=opts.xtitle,
                             ylabel=opts.ytitle,
                             legendColumns=opts.legendColumns,
                             yrange=opts.yrange,
                             errorrows=opts.errorrows,
                             errorcols=opts.errorcols)
    else:
        assert opts.plotType == "boxplot"
        plotRawBoxPlot(dataseries,
                       titles=header,
                       plotmargins=margs,
                       filename=opts.outfile,
                       xlabel=opts.xtitle,
                       ylabel=opts.ytitle)

    print "Done!"

if __name__ == '__main__':
    main()